# src/pipeline/filters/f03_extraction.py
#
# Squad B — Agente Extrator
# Tarefas: B2 (Groq + Instructor) e B5 (fallback Groq → Gemini)
# ─────────────────────────────────────────────────────────────

import os                         # lê variáveis de ambiente (GROQ_API_KEY, GOOGLE_API_KEY)
import time                       # usado no retry com espera entre tentativas

from dotenv import load_dotenv    # carrega o arquivo .env para os.environ

import instructor                 # wrappa clientes de LLM para retornar Pydantic
from groq import Groq             # cliente oficial da Groq
import google.generativeai as genai  # SDK do Google Gemini

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext
from src.schemas.criterios_edital import CriteriosEdital

# ─── Carrega .env ───────────────────────────────────────────
# Precisa rodar antes de qualquer os.getenv()
# Sem isso, GROQ_API_KEY e GOOGLE_API_KEY ficam None
load_dotenv()

# ─── Prompt de extração (B3) ────────────────────────────────
# Definido aqui fora da classe para ser reutilizável nos dois métodos
# (Groq e Gemini usam o mesmo prompt — só o cliente muda)
EXTRACTION_PROMPT = """
You are a structured data extraction system for Brazilian public calls and edicts.
Your sole function is to locate and literally transcribe the requested information.

RULE ZERO — DO NOT INTERPRET, JUST COPY
If the information is not explicitly in the text, return null (or empty list for list fields).

RULE 1 — TITLE AND AGENCY
- titulo: exact title of the call/edict as it appears in the document.
- orgao_financiador: entity with primary financial responsibility (e.g., EMBRAPII, FINEP, CNPq).

RULE 2 — MAXIMUM VALUE PER PROPOSAL (CRITICAL)
STOP AND THINK: Am I extracting the value for a SINGLE PROJECT or the value of ALL PROJECTS COMBINED?
- IGNORE the total budget of the call or global fund (e.g., R$ 20 million, R$ 90 million).
- Look for the funding cap PER PROJECT, PER UNIT, or PER PROPOSAL.
- If there are varied values per line of action, extract the HIGHEST absolute value possible for a single project.
- If there is no financial transfer, return null.
- valor_maximo: numeric value in BRL (float, no currency symbol). null if not found.

RULE 3 — DEADLINE
- prazo: submission deadline as stated in the document (e.g., "30/06/2026", "60 dias após publicação").

RULE 4 — ELIGIBLE SECTORS AND COMPANY SIZE
- setores_elegiveis: list each eligible sector/area as a separate element (e.g., ["energia", "TIC", "saúde"]).
- porte_empresa: list each eligible company size (e.g., ["MEI", "ME", "EPP", "Médio porte", "Grande empresa"]).

RULE 5 — TECHNICAL REQUIREMENTS
- requisitos_tecnicos: list each technical requirement or qualification demanded (e.g., lab capacity, certifications, minimum TRL).

RULE 6 — REQUIRED DOCUMENTS
- documentos_exigidos: list each required document for submission (e.g., ["CNPJ", "certidão negativa", "plano de trabalho"]).

RULE 7 — EXCLUSION CRITERIA
- criterios_exclusao: list any conditions that disqualify a proposal or applicant.

RULE 8 — ICT PARTNERSHIP
- necessidade_parceria_ict: true if the call REQUIRES partnership with a research institution (ICT/universidade). false otherwise.

RULE 9 — THEMATIC KEYWORDS
- palavras_chave_tematicas: list the main thematic keywords or focus areas of the call (e.g., ["inteligência artificial", "IoT", "indústria 4.0"]).

RULE 10 — SUMMARY
- resumo_objetivo: a concise 2-3 sentence summary of the call's objective and what it funds. Copy from the document if possible.

RULE 11 — OUTPUT FORMAT
Return ONLY valid JSON matching the schema. No markdown, no explanations, no extra keys.

=== DOCUMENT TO ANALYZE ===
{markdown_text}
"""

# ─── Constantes de configuração ─────────────────────────────
MAX_TOKENS_GROQ = 8000     # limite seguro para o contexto do llama-3.1-8b-instant
MAX_TOKENS_GEMINI = 12000  # Gemini Flash suporta janela maior — útil para editais longos
GROQ_RETRY_WAIT = 61       # segundos de espera após rate limit da Groq (janela de 1 min)


# ════════════════════════════════════════════════════════════
class ExtractionFilter(Filter):
    """
    Filtro responsável por:
      1. Receber o Markdown do edital (gerado por f01_ingestion)
      2. Tentar extração com Groq (llama-3.1-8b-instant)   ← B2
      3. Se Groq falhar → retentar automaticamente com Gemini ← B5
      4. Validar a saída contra o schema CriteriosEdital (Pydantic)
      5. Salvar o dicionário resultante em ctx.criterios_edital
    """

    def __init__(self):
        # ── Cliente Groq com Instructor ──────────────────────
        # instructor.from_groq() "patcha" o cliente Groq para que
        # chat.completions.create() aceite response_model=<Pydantic>
        # e retorne diretamente uma instância do modelo, não uma string.
        self.groq_client = instructor.from_groq(
            Groq(api_key=os.getenv("GROQ_API_KEY"))
            # se GROQ_API_KEY for None (não configurada), o Groq() lança AuthenticationError
            # logo no __init__ — erro aparece cedo, antes de processar qualquer edital
        )

        # ── Configuração do Gemini ────────────────────────────
        # O SDK do Gemini usa uma chave global (configure uma vez, usa em todo o módulo)
        # Diferente do Groq que passa a key no construtor
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

        # Instructor tem suporte nativo ao Gemini via from_gemini()
        # gemini-1.5-flash é o modelo gratuito mais capaz disponível atualmente
        self.gemini_client = instructor.from_gemini(
            client=genai.GenerativeModel(model_name="gemini-1.5-flash"),
            mode=instructor.Mode.GEMINI_JSON,
            # GEMINI_JSON instrui o Instructor a usar o modo de resposta JSON nativo
            # do Gemini — mais confiável para schemas Pydantic do que parsing de texto livre
        )

    # ────────────────────────────────────────────────────────
    def process(self, context: PipelineContext) -> None:
        """
        Ponto de entrada do pipeline.
        Recebe ctx com markdown_text preenchido (pelo f01),
        tenta extrair os critérios e salva em ctx.criterios_edital.
        """
        markdown = context.markdown_text

        # Guarda coerência com o padrão do f01 (que também valida entrada antes de processar)
        if not markdown:
            print("\n>> [B] Erro: markdown_text está vazio. O filtro f01 falhou?")
            return

        # ── Tentativa 1: Groq ────────────────────────────────
        try:
            print("\n>> [B] Tentando extração com Groq...")
            criterios = self._extract_with_groq(markdown)
            context.criterios_edital = criterios.model_dump()
            # model_dump() converte o objeto Pydantic em dict Python
            # → compatível com Optional[dict] definido no PipelineContext
            print(">> [B] Extração com Groq bem-sucedida.")
            return  # sucesso — sai do método sem tentar Gemini

        except Exception as groq_error:
            # Captura qualquer falha do Groq:
            # - RateLimitError: free tier esgotado (30 req/min ou 14.400/dia)
            # - AuthenticationError: GROQ_API_KEY inválida ou ausente
            # - APIConnectionError: sem internet ou endpoint fora do ar
            # - ValidationError: modelo retornou JSON inválido (Instructor não conseguiu parsear)
            print(f"\n>> [B] Groq falhou ({type(groq_error).__name__}: {groq_error})")
            print(">> [B] Iniciando fallback para Gemini...")

        # ── Tentativa 2: Gemini (fallback) ───────────────────
        # Só chega aqui se o bloco Groq levantou qualquer Exception
        try:
            # Pequena pausa antes do Gemini para não sobrecarregar em caso de erro em cascata
            # (ex: se o problema for de rede, esperar 2s pode ajudar)
            time.sleep(2)

            criterios = self._extract_with_gemini(markdown)
            context.criterios_edital = criterios.model_dump()
            print(">> [B] Extração com Gemini (fallback) bem-sucedida.")
            return

        except Exception as gemini_error:
            # Se ambos falharam, levanta um erro claro para o Squad D (orquestrador)
            # saber que o pipeline está quebrado neste ponto
            raise RuntimeError(
                f"[B] Extração falhou em ambos os provedores.\n"
                f"  Groq: já logado acima\n"
                f"  Gemini: {type(gemini_error).__name__}: {gemini_error}"
            ) from gemini_error

    # ────────────────────────────────────────────────────────
    def _extract_with_groq(self, text: str) -> CriteriosEdital:
        """
        Chama a API da Groq via Instructor e retorna um objeto CriteriosEdital validado.

        O Instructor intercepta a chamada, injeta instruções de schema no prompt,
        e re-tenta internamente se o JSON vier malformado (até 3x por padrão).
        """
        # Trunca o texto para não ultrapassar o limite de tokens do modelo
        # llama-3.1-8b-instant tem janela de ~8k tokens de entrada
        safe_text = text[:MAX_TOKENS_GROQ]

        result: CriteriosEdital = self.groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_model=CriteriosEdital,
            # response_model é a "mágica" do Instructor:
            # ele formata o prompt para pedir JSON no schema do CriteriosEdital,
            # valida a resposta com Pydantic e retorna a instância diretamente
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(markdown_text=safe_text)
            }],
            max_retries=2,
            # max_retries do Instructor (não do Groq):
            # se o modelo retornar JSON inválido, o Instructor reenvía o prompt
            # com a mensagem de erro do Pydantic para o modelo se autocorrigir
        )

        return result  # tipo: CriteriosEdital (objeto Pydantic já validado)

    # ────────────────────────────────────────────────────────
    def _extract_with_gemini(self, text: str) -> CriteriosEdital:
        """
        Fallback: chama a API do Gemini via Instructor com o mesmo schema.

        Interface idêntica ao _extract_with_groq — recebe texto, retorna CriteriosEdital.
        Isso é intencional: o process() não precisa saber qual provedor está sendo usado.
        """
        # Gemini Flash suporta janela maior — aproveita para passar mais contexto
        safe_text = text[:MAX_TOKENS_GEMINI]

        result: CriteriosEdital = self.gemini_client.chat.completions.create(
            response_model=CriteriosEdital,
            # Gemini com Instructor funciona igual ao Groq do ponto de vista do código:
            # response_model define o schema esperado, Instructor valida a saída
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(markdown_text=safe_text)
            }],
        )

        return result
