"""
Testes unitários para f05_inference (InferenceFilter).

Testa:
  - Funções puras (compute_weighted_score, classify_fit, formatters)
  - Comportamento do process() com LLM mockado
  - Degradação graciosa (sem critérios, sem LLM keys, falha de provedor)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f05_inference import (
    SCORE_WEIGHTS,
    _format_chunks,
    _format_criterios,
    classify_fit,
    compute_weighted_score,
)
from src.schemas.resultado_fit import ResultadoFit


# ═══════════════════════════════════════════════════════════
# Testes de funções puras
# ═══════════════════════════════════════════════════════════


class TestComputeWeightedScore:
    """Testa a função compute_weighted_score (scorecard C2)."""

    def test_todos_100_retorna_100(self):
        scores = {
            "elegibilidade_tecnica": 100,
            "alinhamento_tematico": 100,
            "capacidade_documental_financeira": 100,
            "experiencia_previa": 100,
        }
        assert compute_weighted_score(scores) == 100.0

    def test_todos_0_retorna_0(self):
        scores = {
            "elegibilidade_tecnica": 0,
            "alinhamento_tematico": 0,
            "capacidade_documental_financeira": 0,
            "experiencia_previa": 0,
        }
        assert compute_weighted_score(scores) == 0.0

    def test_pesos_corretos(self):
        """40% elegibilidade + 30% alinhamento + 20% capacidade + 10% experiência."""
        scores = {
            "elegibilidade_tecnica": 80,    # 80 * 0.40 = 32
            "alinhamento_tematico": 60,     # 60 * 0.30 = 18
            "capacidade_documental_financeira": 50,  # 50 * 0.20 = 10
            "experiencia_previa": 40,       # 40 * 0.10 = 4
        }
        # Total = 32 + 18 + 10 + 4 = 64
        assert compute_weighted_score(scores) == 64.0

    def test_clamp_acima_de_100(self):
        """Scores > 100 são limitados a 100."""
        scores = {
            "elegibilidade_tecnica": 150,
            "alinhamento_tematico": 100,
            "capacidade_documental_financeira": 100,
            "experiencia_previa": 100,
        }
        assert compute_weighted_score(scores) == 100.0

    def test_clamp_abaixo_de_0(self):
        """Scores < 0 são limitados a 0."""
        scores = {
            "elegibilidade_tecnica": -50,
            "alinhamento_tematico": 100,
            "capacidade_documental_financeira": 100,
            "experiencia_previa": 100,
        }
        # 0*0.4 + 100*0.3 + 100*0.2 + 100*0.1 = 0 + 30 + 20 + 10 = 60
        assert compute_weighted_score(scores) == 60.0

    def test_chaves_ausentes_usam_zero(self):
        """Se uma chave não existe, assume 0."""
        scores = {"elegibilidade_tecnica": 100}
        # 100*0.4 + 0*0.3 + 0*0.2 + 0*0.1 = 40
        assert compute_weighted_score(scores) == 40.0

    def test_dict_vazio(self):
        assert compute_weighted_score({}) == 0.0

    def test_pesos_somam_1(self):
        """Os pesos devem somar 1.0 para que o score máximo seja 100."""
        total_weight = sum(SCORE_WEIGHTS.values())
        assert abs(total_weight - 1.0) < 1e-9


class TestClassifyFit:
    """Testa a função classify_fit."""

    def test_alto(self):
        assert classify_fit(70) == "Alto"
        assert classify_fit(85) == "Alto"
        assert classify_fit(100) == "Alto"

    def test_medio(self):
        assert classify_fit(45) == "Médio"
        assert classify_fit(55) == "Médio"
        assert classify_fit(69.9) == "Médio"

    def test_baixo(self):
        assert classify_fit(20) == "Baixo"
        assert classify_fit(30) == "Baixo"
        assert classify_fit(44.9) == "Baixo"

    def test_inviavel(self):
        assert classify_fit(0) == "Inviável"
        assert classify_fit(10) == "Inviável"
        assert classify_fit(19.9) == "Inviável"

    def test_limites_exatos(self):
        """Verifica os limites exatos de cada faixa."""
        assert classify_fit(70.0) == "Alto"
        assert classify_fit(45.0) == "Médio"
        assert classify_fit(20.0) == "Baixo"
        assert classify_fit(19.99) == "Inviável"


class TestFormatCriterios:
    """Testa _format_criterios."""

    def test_dict_normal(self):
        criterios = {"titulo": "Edital X", "valor_maximo": 100000.0}
        result = _format_criterios(criterios)
        assert "Edital X" in result
        assert "100000.0" in result

    def test_acentos_preservados(self):
        criterios = {"resumo_objetivo": "Inovação em inteligência artificial"}
        result = _format_criterios(criterios)
        assert "Inovação" in result
        assert "inteligência" in result

    def test_fallback_para_str_se_invalido(self):
        """Se json.dumps falhar, retorna str()."""
        # set não é JSON-serializável
        criterios = {"chaves": {1, 2, 3}}
        result = _format_criterios(criterios)
        assert isinstance(result, str)


class TestFormatChunks:
    """Testa _format_chunks."""

    def test_chunks_vazios(self):
        result = _format_chunks([])
        assert "Nenhum documento" in result

    def test_chunks_formatados(self):
        chunks = ["Chunk sobre IA", "Chunk sobre IoT"]
        result = _format_chunks(chunks)
        assert "Trecho 1" in result
        assert "Chunk sobre IA" in result
        assert "Trecho 2" in result
        assert "Chunk sobre IoT" in result

    def test_limita_a_max_chunks(self):
        """Deve limitar a MAX_CHUNKS_IN_PROMPT (10) chunks."""
        chunks = [f"chunk_{i}" for i in range(20)]
        result = _format_chunks(chunks)
        assert "Trecho 10" in result
        assert "Trecho 11" not in result


# ═══════════════════════════════════════════════════════════
# Testes do InferenceFilter.process()
# ═══════════════════════════════════════════════════════════


def _make_resultado_fit(**overrides) -> ResultadoFit:
    """Cria um ResultadoFit válido com defaults sensatos."""
    defaults = {
        "percentual_fit": 55.0,
        "classificacao": "Médio",
        "criterios_atendidos": ["porte adequado", "setor elegível"],
        "gaps_identificados": ["falta certificação ISO"],
        "recomendacoes_adequacao": ["obter certificação ISO 9001"],
        "necessidade_parceria_ict": True,
        "sugestao_parceiros": ["universidade com lab de IA"],
        "justificativa_percentual": "Score baseado em análise dos critérios.",
        "acoes_prioritarias": ["certificação", "parceria ICT"],
    }
    defaults.update(overrides)
    return ResultadoFit(**defaults)


def _make_inference_filter(
    groq_result: ResultadoFit | None = None,
    groq_raises: Exception | None = None,
    gemini_result: ResultadoFit | None = None,
    gemini_raises: Exception | None = None,
    has_groq: bool = True,
    has_gemini: bool = True,
):
    """
    Cria InferenceFilter com clientes LLM mockados.
    Evita chamar __init__ real (que tentaria conectar aos provedores).
    """
    from src.pipeline.filters.f05_inference import InferenceFilter

    filt = InferenceFilter.__new__(InferenceFilter)

    # Mock Groq
    if has_groq:
        mock_groq = MagicMock()
        if groq_raises:
            mock_groq.chat.completions.create.side_effect = groq_raises
        else:
            if groq_result is None:
                groq_result = _make_resultado_fit()
            mock_groq.chat.completions.create.return_value = groq_result
        filt.groq_client = mock_groq
    else:
        filt.groq_client = None

    # Mock Gemini
    if has_gemini:
        mock_gemini = MagicMock()
        if gemini_raises:
            mock_gemini.chat.completions.create.side_effect = gemini_raises
        else:
            if gemini_result is None:
                gemini_result = _make_resultado_fit()
            mock_gemini.chat.completions.create.return_value = gemini_result
        filt.gemini_client = mock_gemini
    else:
        filt.gemini_client = None

    return filt


class TestInferenceFilterProcess:
    """Testa o método process() do InferenceFilter."""

    def _make_ctx(self, **overrides) -> PipelineContext:
        ctx = PipelineContext()
        ctx.criterios_edital = overrides.get("criterios_edital", {
            "titulo": "Chamada IA 2026",
            "orgao_financiador": "EMBRAPII",
            "resumo_objetivo": "Projetos de IA para indústria 4.0",
            "necessidade_parceria_ict": True,
            "requisitos_tecnicos": ["TRL >= 4"],
            "setores_elegiveis": ["TIC", "Indústria"],
        })
        ctx.company_chunks = overrides.get("company_chunks", [
            "A empresa atua com IA e automação industrial.",
            "Possui certificação ISO 9001 e parceria com UFPR.",
        ])
        return ctx

    def test_groq_sucesso_preenche_resultado_fit(self):
        """Quando Groq funciona, preenche resultado_fit e não tenta Gemini."""
        expected = _make_resultado_fit(percentual_fit=72.0, classificacao="Alto")
        filt = _make_inference_filter(groq_result=expected)

        ctx = self._make_ctx()
        filt.process(ctx)

        assert ctx.resultado_fit is not None
        assert ctx.resultado_fit["percentual_fit"] == 72.0
        assert ctx.resultado_fit["classificacao"] == "Alto"

    @patch("src.pipeline.filters.f05_inference.time.sleep")
    def test_groq_falha_gemini_funciona(self, mock_sleep):
        """Quando Groq falha, faz fallback para Gemini."""
        gemini_result = _make_resultado_fit(percentual_fit=48.0, classificacao="Médio")
        filt = _make_inference_filter(
            groq_raises=RuntimeError("Groq rate limit"),
            gemini_result=gemini_result,
        )

        ctx = self._make_ctx()
        filt.process(ctx)

        assert ctx.resultado_fit is not None
        assert ctx.resultado_fit["percentual_fit"] == 48.0
        mock_sleep.assert_called_once_with(2)

    @patch("src.pipeline.filters.f05_inference.time.sleep")
    def test_ambos_falham_levanta_runtime_error(self, mock_sleep):
        """Quando Groq e Gemini falham, levanta RuntimeError."""
        filt = _make_inference_filter(
            groq_raises=RuntimeError("Groq down"),
            gemini_raises=RuntimeError("Gemini down"),
        )

        ctx = self._make_ctx()

        with pytest.raises(RuntimeError, match="Inferência falhou em ambos"):
            filt.process(ctx)

    def test_sem_provedores_levanta_runtime_error(self):
        """Sem nenhum provedor configurado, levanta RuntimeError."""
        filt = _make_inference_filter(has_groq=False, has_gemini=False)

        ctx = self._make_ctx()

        with pytest.raises(RuntimeError, match="Nenhum provedor de LLM"):
            filt.process(ctx)

    def test_criterios_edital_none_retorna_sem_erro(self):
        """Se criterios_edital for None, retorna sem resultado (não quebra)."""
        filt = _make_inference_filter()

        ctx = PipelineContext()
        ctx.criterios_edital = None

        filt.process(ctx)

        assert ctx.resultado_fit is None

    def test_criterios_edital_vazio_retorna_sem_erro(self):
        """Se criterios_edital for dict vazio, retorna sem resultado."""
        filt = _make_inference_filter()

        ctx = PipelineContext()
        ctx.criterios_edital = {}

        filt.process(ctx)

        assert ctx.resultado_fit is None

    def test_company_chunks_vazio_nao_quebra(self):
        """Quando não há chunks da empresa, o filtro deve funcionar."""
        expected = _make_resultado_fit(percentual_fit=25.0, classificacao="Baixo")
        filt = _make_inference_filter(groq_result=expected)

        ctx = self._make_ctx(company_chunks=[])
        filt.process(ctx)

        assert ctx.resultado_fit is not None
        assert ctx.resultado_fit["percentual_fit"] == 25.0

    def test_resultado_fit_tem_todos_os_campos(self):
        """O resultado_fit deve ter todos os campos do schema ResultadoFit."""
        resultado = _make_resultado_fit()
        filt = _make_inference_filter(groq_result=resultado)

        ctx = self._make_ctx()
        filt.process(ctx)

        fit = ctx.resultado_fit
        assert fit is not None

        expected_keys = {
            "percentual_fit",
            "classificacao",
            "criterios_atendidos",
            "gaps_identificados",
            "recomendacoes_adequacao",
            "necessidade_parceria_ict",
            "sugestao_parceiros",
            "justificativa_percentual",
            "acoes_prioritarias",
        }
        assert expected_keys.issubset(set(fit.keys()))

    def test_somente_gemini_disponivel(self):
        """Quando só Gemini está configurado (sem Groq), usa Gemini direto."""
        gemini_result = _make_resultado_fit(percentual_fit=60.0)
        filt = _make_inference_filter(
            has_groq=False,
            gemini_result=gemini_result,
        )

        ctx = self._make_ctx()

        with patch("src.pipeline.filters.f05_inference.time.sleep"):
            filt.process(ctx)

        assert ctx.resultado_fit is not None
        assert ctx.resultado_fit["percentual_fit"] == 60.0


class TestResultadoFitSchema:
    """Testa o schema ResultadoFit diretamente."""

    def test_valida_resultado_valido(self):
        resultado = _make_resultado_fit()
        assert resultado.percentual_fit == 55.0
        assert resultado.classificacao == "Médio"

    def test_percentual_fit_fora_do_range(self):
        with pytest.raises(Exception):
            ResultadoFit(
                percentual_fit=150.0,  # > 100
                classificacao="Alto",
                necessidade_parceria_ict=False,
                justificativa_percentual="teste",
            )

    def test_classificacao_invalida(self):
        with pytest.raises(Exception):
            ResultadoFit(
                percentual_fit=50.0,
                classificacao="Excelente",  # não está no Literal
                necessidade_parceria_ict=False,
                justificativa_percentual="teste",
            )

    def test_acoes_prioritarias_max_3(self):
        """acoes_prioritarias tem max_length=3."""
        with pytest.raises(Exception):
            ResultadoFit(
                percentual_fit=50.0,
                classificacao="Médio",
                necessidade_parceria_ict=False,
                justificativa_percentual="teste",
                acoes_prioritarias=["a", "b", "c", "d"],  # 4 > max 3
            )
