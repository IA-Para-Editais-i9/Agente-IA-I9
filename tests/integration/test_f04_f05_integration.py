"""
Teste de integração f04 + f05.

- Requer ChromaDB populado (coleção `perfil_empresa`) e chaves de API configuradas.
- Não roda no CI (CI executa apenas tests/unit).
"""

import os

import pytest

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f04_retrieval import RetrievalFilter
from src.pipeline.filters.f05_inference import InferenceFilter
from src.schemas.resultado_fit import ResultadoFit


CRITERIOS_MOCK = {
    "titulo": "Edital FINEP Economia Circular 2024",
    "orgao_financiador": "FINEP",
    "valor_maximo": 1500000,
    "prazo_meses": 24,
    "setores_elegiveis": ["manufatura", "química verde", "baterias"],
    "porte_empresa": "Pequena ou Média Empresa",
    "resumo_objetivo": "Apoio a projetos de P&D em economia circular, reuso de materiais e baterias de segunda vida",
    "palavras_chave_tematicas": ["economia circular", "baterias", "reuso", "sustentabilidade"],
    "necessidade_parceria_ict": True,
    "criterios_exclusao": ["empresas com débitos fiscais"],
}


@pytest.mark.skipif(
    not os.environ.get("GROQ_API_KEY") and not os.environ.get("GEMINI_API_KEY"),
    reason="Sem chaves de API configuradas (GROQ_API_KEY/GEMINI_API_KEY).",
)
def test_f05_retorna_resultado_fit_valido_com_chunks_mockados():
    ctx = PipelineContext(
        criterios_edital=CRITERIOS_MOCK,
        company_chunks=[
            "A i9+ desenvolveu projeto de reuso de baterias de lítio em parceria com a UTFPR em 2022.",
            "Portfólio inclui sistema de logística reversa para resíduos eletroeletrônicos.",
            "Empresa de pequeno porte, CNAE 7210-0/00 (pesquisa e desenvolvimento).",
        ],
    )
    ctx = InferenceFilter().run(ctx)
    assert ctx.resultado_fit is not None
    resultado = ResultadoFit(**ctx.resultado_fit)
    assert 0 <= resultado.percentual_fit <= 100
    assert len(resultado.acoes_prioritarias) <= 3


@pytest.mark.skipif(
    not os.path.exists("./chroma_db"),
    reason="ChromaDB local não encontrado em ./chroma_db",
)
def test_pipeline_f04_f05_completo_requer_chromadb_e_chaves():
    if not os.environ.get("GROQ_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("Sem chaves de API configuradas (GROQ_API_KEY/GEMINI_API_KEY).")

    ctx = PipelineContext(criterios_edital=CRITERIOS_MOCK)
    ctx = RetrievalFilter().run(ctx)
    ctx = InferenceFilter().run(ctx)
    assert ctx.resultado_fit is not None
    resultado = ResultadoFit(**ctx.resultado_fit)
    assert resultado.justificativa_percentual
