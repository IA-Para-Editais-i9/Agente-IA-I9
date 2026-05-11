"""
C6 — Harness de calibração para validar %fit contra expectativas manuais.

Estrutura:
  - Cada fixture em CALIBRATION_FIXTURES descreve um edital + resultado esperado.
  - Por enquanto os fixtures estão com dados placeholder (classificação esperada e
    intervalo de percentual_fit). Quando os 3 editais forem avaliados manualmente,
    basta preencher os campos.
  - O harness roda o pipeline completo (f01→f05) e compara contra as expectativas.

Uso:
    pytest tests/integration/test_calibration.py -v
    pytest tests/integration/test_calibration.py -v -k "embrapii"

Para adicionar um novo edital de calibração:
    1. Coloque o PDF em data/editais/samples/
    2. Adicione uma entrada em CALIBRATION_FIXTURES com os campos preenchidos
    3. Rode o teste
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Fixture de calibração ──────────────────────────────────
@dataclass
class CalibrationFixture:
    """Descreve um edital e o resultado esperado para calibração."""

    id: str  # identificador curto (ex: "embrapii_2025")
    pdf_filename: str  # nome do PDF em data/editais/samples/
    expected_classificacao: Optional[str] = None  # "Alto", "Médio", "Baixo", "Inviável"
    expected_fit_min: Optional[float] = None  # intervalo inferior do %fit esperado
    expected_fit_max: Optional[float] = None  # intervalo superior do %fit esperado
    expected_ict: Optional[bool] = None  # necessidade_parceria_ict esperada
    notes: str = ""  # observações da avaliação manual


# ═══════════════════════════════════════════════════════════
# FIXTURES — preencher quando os editais forem avaliados manualmente
# ═══════════════════════════════════════════════════════════
CALIBRATION_FIXTURES = [
    CalibrationFixture(
        id="embrapii_cpp001",
        pdf_filename="EDITAL_CPP-001_2025CPFL.pdf",
        expected_classificacao=None,  # TODO: preencher após avaliação manual
        expected_fit_min=None,
        expected_fit_max=None,
        expected_ict=None,
        notes="Chamada pública CPFL/EMBRAPII. Aguardando avaliação manual.",
    ),
    CalibrationFixture(
        id="chamada_pdi_2026",
        pdf_filename="Edital_-_Chamada_PDI_2026_.pdf",
        expected_classificacao=None,
        expected_fit_min=None,
        expected_fit_max=None,
        expected_ict=None,
        notes="Chamada PDI 2026. Aguardando avaliação manual.",
    ),
    CalibrationFixture(
        id="lab_procel",
        pdf_filename="Edital LAB PROCEL II_2a chamada.pdf",
        expected_classificacao=None,
        expected_fit_min=None,
        expected_fit_max=None,
        expected_ict=None,
        notes="LAB PROCEL II 2a chamada. Aguardando avaliação manual.",
    ),
]


# ── Helpers ────────────────────────────────────────────────

def _pdf_path(filename: str) -> Path:
    return PROJECT_ROOT / "data" / "editais" / "samples" / filename


def _has_llm_keys() -> bool:
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def _fixture_is_configured(fix: CalibrationFixture) -> bool:
    """Retorna True se o fixture tem pelo menos uma expectativa preenchida."""
    return any([
        fix.expected_classificacao is not None,
        fix.expected_fit_min is not None,
        fix.expected_fit_max is not None,
        fix.expected_ict is not None,
    ])


# ── Testes ─────────────────────────────────────────────────

@pytest.mark.skipif(
    not _has_llm_keys(),
    reason="Chaves de LLM (GROQ_API_KEY / GOOGLE_API_KEY) não configuradas",
)
class TestCalibration:
    """
    Testes de calibração — rodam o pipeline completo e comparam com expectativas.

    Os testes são skipados automaticamente se:
      - As chaves de LLM não estiverem configuradas
      - O PDF do fixture não existir
      - O fixture não tiver expectativas preenchidas (ainda não avaliado)
    """

    @pytest.mark.parametrize(
        "fixture",
        CALIBRATION_FIXTURES,
        ids=[f.id for f in CALIBRATION_FIXTURES],
    )
    def test_calibration_fit(self, fixture: CalibrationFixture):
        pdf = _pdf_path(fixture.pdf_filename)

        if not pdf.exists():
            pytest.skip(f"PDF não encontrado: {fixture.pdf_filename}")

        if not _fixture_is_configured(fixture):
            pytest.skip(
                f"Fixture '{fixture.id}' ainda não tem expectativas preenchidas. "
                f"Avalie manualmente e preencha os campos em CALIBRATION_FIXTURES."
            )

        # ── Rodar pipeline completo ────────────────────────
        from src.pipeline.context import PipelineContext
        from src.pipeline.filters.f01_ingestion import IngestionFilter
        from src.pipeline.filters.f02_indexing import IndexingFilter
        from src.pipeline.filters.f03_extraction import ExtractionFilter
        from src.pipeline.filters.f04_retrieval import RetrievalFilter
        from src.pipeline.filters.f05_inference import InferenceFilter
        from src.pipeline.pipeline import Pipeline

        pipeline = Pipeline([
            IngestionFilter(),
            IndexingFilter(),
            ExtractionFilter(),
            RetrievalFilter(),
            InferenceFilter(),
        ])

        ctx = PipelineContext(pdf_path=str(pdf))
        ctx = pipeline.run(ctx)

        # ── Validar resultado ──────────────────────────────
        assert ctx.resultado_fit is not None, (
            f"[{fixture.id}] Pipeline não produziu resultado_fit"
        )

        fit = ctx.resultado_fit

        if fixture.expected_classificacao is not None:
            assert fit["classificacao"] == fixture.expected_classificacao, (
                f"[{fixture.id}] Classificação esperada: {fixture.expected_classificacao}, "
                f"obtida: {fit['classificacao']}"
            )

        if fixture.expected_fit_min is not None:
            assert fit["percentual_fit"] >= fixture.expected_fit_min, (
                f"[{fixture.id}] Fit {fit['percentual_fit']}% abaixo do mínimo "
                f"esperado ({fixture.expected_fit_min}%)"
            )

        if fixture.expected_fit_max is not None:
            assert fit["percentual_fit"] <= fixture.expected_fit_max, (
                f"[{fixture.id}] Fit {fit['percentual_fit']}% acima do máximo "
                f"esperado ({fixture.expected_fit_max}%)"
            )

        if fixture.expected_ict is not None:
            assert fit["necessidade_parceria_ict"] == fixture.expected_ict, (
                f"[{fixture.id}] ICT esperada: {fixture.expected_ict}, "
                f"obtida: {fit['necessidade_parceria_ict']}"
            )

        # Salvar resultado para inspeção
        output_dir = PROJECT_ROOT / "outputs" / "calibration"
        output_dir.mkdir(parents=True, exist_ok=True)
        result_file = output_dir / f"{fixture.id}_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fixture_id": fixture.id,
                    "pdf": fixture.pdf_filename,
                    "criterios_edital": ctx.criterios_edital,
                    "company_chunks_count": len(ctx.company_chunks),
                    "resultado_fit": ctx.resultado_fit,
                    "notes": fixture.notes,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )


# ── Teste de sanidade (sempre roda) ────────────────────────

def test_calibration_fixtures_are_valid():
    """Verifica que os fixtures estão bem formados."""
    ids = [f.id for f in CALIBRATION_FIXTURES]
    assert len(ids) == len(set(ids)), "IDs de fixtures duplicados!"

    for fix in CALIBRATION_FIXTURES:
        assert fix.pdf_filename, f"Fixture '{fix.id}' sem pdf_filename"

        if fix.expected_fit_min is not None:
            assert 0 <= fix.expected_fit_min <= 100

        if fix.expected_fit_max is not None:
            assert 0 <= fix.expected_fit_max <= 100

        if fix.expected_fit_min is not None and fix.expected_fit_max is not None:
            assert fix.expected_fit_min <= fix.expected_fit_max, (
                f"Fixture '{fix.id}': min ({fix.expected_fit_min}) > max ({fix.expected_fit_max})"
            )
