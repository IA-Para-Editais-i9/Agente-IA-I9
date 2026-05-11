# src/pipeline/filters/f05_inference.py
#
# Squad C — Agente 2 (Inferência + %fit)
# Tarefas: C2 (scorecard de pesos) + C4 (prompt LLM) + C5 (integração RAG)
# ─────────────────────────────────────────────────────────────

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

import instructor
from groq import Groq
import google.generativeai as genai

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext
from src.schemas.resultado_fit import ResultadoFit

# ─── Carrega .env ───────────────────────────────────────────
load_dotenv()

logger = logging.getLogger(__name__)

# ─── Pesos do scorecard (C2) ────────────────────────────────
# Cada sub-score vale de 0 a 100; o total é a média ponderada.
SCORE_WEIGHTS = {
    "elegibilidade_tecnica": 0.40,
    "alinhamento_tematico": 0.30,
    "capacidade_documental_financeira": 0.20,
    "experiencia_previa": 0.10,
}

# ─── Prompt do Agente 2 (C4) ───────────────────────────────
INFERENCE_PROMPT = """
Você é um analista especializado em avaliação de aderência (fit) de empresas
a editais públicos brasileiros de inovação e fomento.

Sua tarefa: avaliar se a empresa descrita nos TRECHOS DO PERFIL DA EMPRESA
atende aos CRITÉRIOS DO EDITAL e produzir um resultado de fit (adequação).

═══ CRITÉRIOS DO EDITAL ═══
{criterios_edital_json}

═══ TRECHOS DO PERFIL DA EMPRESA (recuperados por RAG) ═══
{company_chunks_text}

═══ INSTRUÇÕES DE CÁLCULO (OBRIGATÓRIO — siga na ordem) ═══

PASSO 1 — Calcule cada sub-score de 0 a 100:

1. elegibilidade_tecnica (peso 40%):
   Compare os requisitos_tecnicos e setores_elegiveis do edital com as
   capacidades da empresa. Considere certificações, infraestrutura e TRL.
   Se não houver informação da empresa, atribua 20.

2. alinhamento_tematico (peso 30%):
   Compare palavras_chave_tematicas e resumo_objetivo do edital com os
   projetos e áreas de atuação da empresa. Avalie sobreposição temática.
   Se não houver informação da empresa, atribua 20.

3. capacidade_documental_financeira (peso 20%):
   Verifique se a empresa parece atender porte_empresa, documentos_exigidos
   e valor_maximo do edital. Considere contratos anteriores como evidência.
   Se não houver informação da empresa, atribua 20.

4. experiencia_previa (peso 10%):
   Avalie se a empresa tem histórico de projetos semelhantes, contratos
   com órgãos públicos, ou participação em editais similares.
   Se não houver informação da empresa, atribua 10.

PASSO 2 — Calcule o percentual_fit total:
  percentual_fit = (elegibilidade_tecnica × 0.40) + (alinhamento_tematico × 0.30)
                 + (capacidade_documental_financeira × 0.20) + (experiencia_previa × 0.10)

PASSO 3 — Determine a classificacao:
  - "Alto"     se percentual_fit >= 70
  - "Médio"    se percentual_fit >= 45
  - "Baixo"    se percentual_fit >= 20
  - "Inviável" se percentual_fit < 20

PASSO 4 — Preencha os campos restantes:
  - criterios_atendidos: lista dos critérios do edital que a empresa atende.
  - gaps_identificados: lista das lacunas ou requisitos não atendidos.
  - recomendacoes_adequacao: ações sugeridas para melhorar a aderência.
  - necessidade_parceria_ict: true se o edital exige parceria com ICT e a empresa
    não possui; caso contrário, copie o valor do campo do edital.
  - sugestao_parceiros: se necessidade_parceria_ict for true, sugira tipos
    de parceiros (ex: "universidade com laboratório de IA").
  - justificativa_percentual: explique como chegou ao percentual, mencionando
    cada sub-score e a evidência (ou falta dela).
  - acoes_prioritarias: até 3 ações mais urgentes para viabilizar a candidatura.

═══ FORMATO DE SAÍDA ═══
Retorne APENAS JSON válido, sem markdown, sem explicações fora do JSON.
O JSON deve conter exatamente estes campos:
  percentual_fit, classificacao, criterios_atendidos, gaps_identificados,
  recomendacoes_adequacao, necessidade_parceria_ict, sugestao_parceiros,
  justificativa_percentual, acoes_prioritarias
"""

# ─── Constantes ─────────────────────────────────────────────
MAX_TOKENS_GROQ = 8000
MAX_TOKENS_GEMINI = 12000
MAX_CHUNKS_IN_PROMPT = 10


def _format_criterios(criterios: Dict[str, Any]) -> str:
    """Formata critérios do edital como JSON legível para o prompt."""
    try:
        return json.dumps(criterios, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(criterios)


def _format_chunks(chunks: list[str]) -> str:
    """Formata os chunks da empresa para o prompt."""
    if not chunks:
        return "(Nenhum documento da empresa disponível. Avalie com base apenas nos critérios do edital, atribuindo scores baixos onde não há evidência.)"

    selected = chunks[:MAX_CHUNKS_IN_PROMPT]
    parts = []
    for i, chunk in enumerate(selected, 1):
        parts.append(f"--- Trecho {i} ---\n{chunk.strip()}")
    return "\n\n".join(parts)


def compute_weighted_score(sub_scores: Dict[str, float]) -> float:
    """
    Calcula o percentual_fit ponderado a partir dos sub-scores.

    Função pura e auditável — pode ser usada fora do LLM para validação.
    """
    total = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        score = sub_scores.get(key, 0.0)
        # Clamp entre 0 e 100
        score = max(0.0, min(100.0, score))
        total += score * weight
    return round(total, 2)


def classify_fit(percentual: float) -> str:
    """Classifica o fit com base no percentual."""
    if percentual >= 70:
        return "Alto"
    if percentual >= 45:
        return "Médio"
    if percentual >= 20:
        return "Baixo"
    return "Inviável"


# ════════════════════════════════════════════════════════════
class InferenceFilter(Filter):
    """
    Filtro responsável por:
      1. Receber ctx.criterios_edital (do f03) e ctx.company_chunks (do f04)
      2. Montar prompt do Agente 2 com scorecard obrigatório
      3. Chamar LLM (Groq → Gemini fallback) para produzir ResultadoFit
      4. Validar saída contra schema Pydantic
      5. Salvar em ctx.resultado_fit
    """

    def __init__(self):
        # ── Cliente Groq com Instructor ──────────────────────
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            self.groq_client = instructor.from_groq(
                Groq(api_key=groq_key)
            )
        else:
            self.groq_client = None
            logger.warning(
                "[C] GROQ_API_KEY não configurada. Groq indisponível para inferência."
            )

        # ── Configuração do Gemini ────────────────────────────
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            genai.configure(api_key=google_key)
            self.gemini_client = instructor.from_gemini(
                client=genai.GenerativeModel(model_name="gemini-1.5-flash"),
                mode=instructor.Mode.GEMINI_JSON,
            )
        else:
            self.gemini_client = None
            logger.warning(
                "[C] GOOGLE_API_KEY não configurada. Gemini indisponível para inferência."
            )

    # ────────────────────────────────────────────────────────
    def process(self, ctx: PipelineContext) -> None:
        """
        Ponto de entrada do pipeline.
        Recebe ctx com criterios_edital e company_chunks preenchidos,
        produz resultado_fit.
        """
        criterios = ctx.criterios_edital
        if not criterios:
            logger.error(
                "[C] criterios_edital está vazio. O filtro f03 falhou?"
            )
            print("\n>> [C] Erro: criterios_edital está vazio. O filtro f03 falhou?")
            return

        company_chunks = ctx.company_chunks or []

        # Monta o prompt com critérios + chunks
        prompt_text = INFERENCE_PROMPT.format(
            criterios_edital_json=_format_criterios(criterios),
            company_chunks_text=_format_chunks(company_chunks),
        )

        # ── Tentativa 1: Groq ────────────────────────────────
        if self.groq_client is not None:
            try:
                print("\n>> [C] Tentando inferência com Groq...")
                resultado = self._infer_with_groq(prompt_text)
                ctx.resultado_fit = resultado.model_dump()
                print(">> [C] Inferência com Groq bem-sucedida.")
                return
            except Exception as groq_error:
                logger.warning(
                    "[C] Groq falhou (%s: %s)",
                    type(groq_error).__name__,
                    groq_error,
                )
                print(
                    f"\n>> [C] Groq falhou ({type(groq_error).__name__}: {groq_error})"
                )
                print(">> [C] Iniciando fallback para Gemini...")

        # ── Tentativa 2: Gemini (fallback) ───────────────────
        if self.gemini_client is not None:
            try:
                time.sleep(2)
                print("\n>> [C] Tentando inferência com Gemini...")
                resultado = self._infer_with_gemini(prompt_text)
                ctx.resultado_fit = resultado.model_dump()
                print(">> [C] Inferência com Gemini bem-sucedida.")
                return
            except Exception as gemini_error:
                raise RuntimeError(
                    f"[C] Inferência falhou em ambos os provedores.\n"
                    f"  Groq: já logado acima\n"
                    f"  Gemini: {type(gemini_error).__name__}: {gemini_error}"
                ) from gemini_error

        # Nenhum provedor disponível
        raise RuntimeError(
            "[C] Nenhum provedor de LLM configurado. "
            "Defina GROQ_API_KEY e/ou GOOGLE_API_KEY no .env"
        )

    # ────────────────────────────────────────────────────────
    def _infer_with_groq(self, prompt_text: str) -> ResultadoFit:
        """Chama Groq via Instructor e retorna ResultadoFit validado."""
        safe_text = prompt_text[:MAX_TOKENS_GROQ]

        result: ResultadoFit = self.groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            response_model=ResultadoFit,
            messages=[{"role": "user", "content": safe_text}],
            max_retries=2,
        )
        return result

    # ────────────────────────────────────────────────────────
    def _infer_with_gemini(self, prompt_text: str) -> ResultadoFit:
        """Fallback: chama Gemini via Instructor com o mesmo schema."""
        safe_text = prompt_text[:MAX_TOKENS_GEMINI]

        result: ResultadoFit = self.gemini_client.chat.completions.create(
            response_model=ResultadoFit,
            messages=[{"role": "user", "content": safe_text}],
        )
        return result
