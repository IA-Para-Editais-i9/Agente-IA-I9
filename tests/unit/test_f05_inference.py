import pytest

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f05_inference import InferenceFilter
from src.schemas.resultado_fit import ResultadoFit


def _resultado_valido() -> ResultadoFit:
    return ResultadoFit(
        percentual_fit=80.0,
        classificacao="Alto",
        criterios_atendidos=["x"],
        gaps_identificados=["y"],
        recomendacoes_adequacao=["z"],
        necessidade_parceria_ict=False,
        sugestao_parceiros=[],
        justificativa_percentual="subscores: 40+25+10+5 = 80",
        acoes_prioritarias=["ação 1", "ação 2", "ação 3"],
    )


def test_resultadofit_valida_classificacao_contra_percentual():
    with pytest.raises(ValueError, match="incompatível"):
        ResultadoFit(
            percentual_fit=80.0,
            classificacao="Baixo",
            criterios_atendidos=[],
            gaps_identificados=[],
            recomendacoes_adequacao=[],
            necessidade_parceria_ict=False,
            sugestao_parceiros=[],
            justificativa_percentual="",
            acoes_prioritarias=["a"],
        )


def test_f05_exige_criterios_edital():
    ctx = PipelineContext(criterios_edital=None)
    with pytest.raises(ValueError, match="ctx\\.criterios_edital"):
        InferenceFilter().run(ctx)


def test_f05_popula_ctx_resultado_fit(monkeypatch):
    filtro = InferenceFilter()
    monkeypatch.setattr(filtro, "_call_with_fallback", lambda prompt: _resultado_valido())

    ctx = PipelineContext(criterios_edital={"resumo_objetivo": "x"}, company_chunks=["chunk"])
    ctx = filtro.run(ctx)
    assert ctx.resultado_fit is not None
    assert ctx.resultado_fit["classificacao"] == "Alto"
    assert 0.0 <= ctx.resultado_fit["percentual_fit"] <= 100.0


def test_f05_fallback_groq_para_gemini(monkeypatch):
    filtro = InferenceFilter()

    def _fail(_prompt: str):
        raise RuntimeError("rate limit")

    monkeypatch.setattr(filtro, "_call_groq", _fail)
    monkeypatch.setattr(filtro, "_call_gemini", lambda prompt: _resultado_valido())

    res = filtro._call_with_fallback("prompt")
    assert isinstance(res, ResultadoFit)
    assert res.classificacao == "Alto"
