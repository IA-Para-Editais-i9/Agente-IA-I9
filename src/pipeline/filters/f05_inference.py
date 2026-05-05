import logging
import os

import instructor
from groq import Groq

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext
from src.schemas.resultado_fit import ResultadoFit

logger = logging.getLogger(__name__)

MODEL_GROQ = "llama-3.1-8b-instant"
MODEL_GEMINI = "gemini-1.5-flash"

PESOS_FIT = """
Calcule o percentual_fit em 4 etapas separadas antes de compor o total:

1. ELEGIBILIDADE TÉCNICA (máx 40 pts)
   - CNAE/setor elegível conforme o edital? (+0 a 20)
   - Porte da empresa compatível? (+0 a 10)
   - Localização/abrangência compatível? (+0 a 10)

2. ALINHAMENTO TEMÁTICO (máx 30 pts)
   - Temas do edital aparecem explicitamente nos projetos da empresa? (+0 a 20)
   - Histórico de projetos no mesmo domínio tecnológico? (+0 a 10)

3. CAPACIDADE DOCUMENTAL/FINANCEIRA (máx 20 pts)
   - Documentos exigidos provavelmente disponíveis? (+0 a 10)
   - Capacidade de contrapartida financeira, se exigida? (+0 a 10)

4. EXPERIÊNCIA PRÉVIA (máx 10 pts)
   - Editais similares já executados? (+0 a 10)

percentual_fit = soma dos 4 sub-scores acima.
"""


def _build_groq_client() -> instructor.Instructor:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY não configurada no ambiente.")
    groq_client = Groq(api_key=api_key)
    return instructor.from_groq(groq_client, mode=instructor.Mode.JSON)


def _build_gemini_client() -> instructor.Instructor:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada no ambiente.")

    # import local para evitar custo quando não usado
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    gemini_client = genai.GenerativeModel(MODEL_GEMINI)
    return instructor.from_gemini(gemini_client, mode=instructor.Mode.GEMINI_JSON)


def _build_prompt(criterios: dict, company_chunks: list[str]) -> str:
    chunks_formatados = (
        "\n---\n".join(company_chunks)
        if company_chunks
        else "(nenhum trecho disponível)"
    )
    return f"""Você é um consultor especialista em editais de inovação brasileiros.
Sua tarefa é analisar o fit entre a empresa i9+ e o edital abaixo.

=== CRITÉRIOS DO EDITAL ===
{criterios}

=== PERFIL DA EMPRESA (trechos relevantes do portfólio e documentos internos) ===
{chunks_formatados}

=== INSTRUÇÕES DE ANÁLISE ===
{PESOS_FIT}

Regras obrigatórias:
1. Use APENAS as informações fornecidas acima. Não invente dados.
2. Seja específico para a i9+. Recomendações genéricas são inúteis.
3. Se o edital exigir parceria com ICT, sugira parceiros reais do Paraná (UTFPR,
   UFPR, SENAI-PR, TECPAR, Lactec, etc.).
4. Para gaps: mencione o critério exato que não é atendido.
5. Para ações prioritárias: liste no máximo 3, da mais urgente para a menos urgente.
6. Calcule os 4 sub-scores explicitamente na justificativa_percentual antes de somar.

Retorne APENAS o JSON com os campos solicitados. Nenhum texto fora do JSON.
"""


class InferenceFilter(Filter):
    """
    f05 — Agente 2 (Inferência & Fit).
    Recebe criterios_edital + company_chunks e retorna ResultadoFit.
    Popula: ctx.resultado_fit (dict)
    Fallback automático: Groq → Gemini.
    """

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.criterios_edital:
            raise ValueError(
                "f05: ctx.criterios_edital está vazio. f03 rodou corretamente?"
            )

        prompt = _build_prompt(ctx.criterios_edital, ctx.company_chunks)
        resultado = self._call_with_fallback(prompt)

        ctx.resultado_fit = resultado.model_dump()
        logger.info(
            "f05: análise concluída. Fit=%.1f%% | Classificação=%s",
            resultado.percentual_fit,
            resultado.classificacao,
        )
        return ctx

    def _call_with_fallback(self, prompt: str) -> ResultadoFit:
        try:
            return self._call_groq(prompt)
        except Exception as e:
            logger.warning(
                "f05: Groq falhou (%s). Tentando Gemini como fallback.", str(e)
            )
            try:
                return self._call_gemini(prompt)
            except Exception as e2:
                raise RuntimeError(
                    f"f05: ambos os provedores falharam. Groq: {e} | Gemini: {e2}"
                ) from e2

    def _call_groq(self, prompt: str) -> ResultadoFit:
        client = _build_groq_client()
        return client.chat.completions.create(
            model=MODEL_GROQ,
            messages=[{"role": "user", "content": prompt}],
            response_model=ResultadoFit,
            max_retries=3,
            temperature=0.2,
        )

    def _call_gemini(self, prompt: str) -> ResultadoFit:
        client = _build_gemini_client()
        return client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            response_model=ResultadoFit,
            max_retries=2,
        )
