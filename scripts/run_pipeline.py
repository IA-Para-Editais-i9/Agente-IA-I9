#!/usr/bin/env python
"""
Executa o pipeline completo de análise de fit: f01 → f02 → f03 → f04 → f05.

Uso:
    python scripts/run_pipeline.py data/editais/samples/algum_edital.pdf
    python scripts/run_pipeline.py data/editais/samples/algum_edital.pdf --output outputs/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f01_ingestion import IngestionFilter
from src.pipeline.filters.f02_indexing import IndexingFilter
from src.pipeline.filters.f03_extraction import ExtractionFilter
from src.pipeline.filters.f04_retrieval import RetrievalFilter
from src.pipeline.filters.f05_inference import InferenceFilter
from src.pipeline.pipeline import Pipeline



def build_pipeline() -> Pipeline:
    """Monta o pipeline completo com os 5 filtros na ordem correta."""
    return Pipeline([
        IngestionFilter(),      # f01: PDF → Markdown
        IndexingFilter(),       # f02: Markdown → chunks no ChromaDB (editais)
        ExtractionFilter(),     # f03: Markdown → CriteriosEdital (via LLM)
        RetrievalFilter(),      # f04: CriteriosEdital → company_chunks (RAG)
        InferenceFilter(),      # f05: CriteriosEdital + company_chunks → ResultadoFit
    ])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executa o pipeline completo de análise de fit para um edital PDF."
    )
    parser.add_argument("pdf", help="Caminho para o PDF do edital")
    parser.add_argument(
        "--output", "-o",
        default="outputs",
        help="Diretório para salvar resultados (default: outputs/)",
    )
    args = parser.parse_args()

    pdf_path = args.pdf
    if not Path(pdf_path).exists():
        print(f"ERRO: arquivo não encontrado: {pdf_path}")
        return 1

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print("  Pipeline completo — Análise de Fit")
    print(f"  PDF: {pdf_path}")
    print(f"{'='*70}\n")

    t0 = perf_counter()

    ctx = PipelineContext(pdf_path=pdf_path)
    pipeline = build_pipeline()

    try:
        ctx = pipeline.run(ctx)
    except Exception as e:
        print(f"\nERRO no pipeline: {type(e).__name__}: {e}")
        return 1

    elapsed = perf_counter() - t0

    # ── Resumo ─────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"  Resultado — {elapsed:.1f}s")
    print(f"{'='*70}")

    if ctx.criterios_edital:
        titulo = ctx.criterios_edital.get("titulo", "(sem título)")
        print(f"\n  Edital: {titulo}")
        orgao = ctx.criterios_edital.get("orgao_financiador", "?")
        print(f"  Órgão: {orgao}")

    print(f"  Chunks empresa recuperados: {len(ctx.company_chunks)}")

    if ctx.resultado_fit:
        fit = ctx.resultado_fit
        print("\n  ── Resultado Fit ──")
        print(f"  Percentual:    {fit.get('percentual_fit', '?')}%")
        print(f"  Classificação: {fit.get('classificacao', '?')}")
        print(f"  ICT necessária: {fit.get('necessidade_parceria_ict', '?')}")

        if fit.get("criterios_atendidos"):
            print("\n  Critérios atendidos:")
            for c in fit["criterios_atendidos"]:
                print(f"    + {c}")

        if fit.get("gaps_identificados"):
            print("\n  Gaps identificados:")
            for g in fit["gaps_identificados"]:
                print(f"    - {g}")

        if fit.get("acoes_prioritarias"):
            print("\n  Ações prioritárias:")
            for i, a in enumerate(fit["acoes_prioritarias"], 1):
                print(f"    {i}. {a}")

        if fit.get("justificativa_percentual"):
            print(f"\n  Justificativa: {fit['justificativa_percentual']}")
    else:
        print("\n  AVISO: resultado_fit não foi preenchido.")

    # ── Salvar resultados em JSON ──────────────────────────
    stem = Path(pdf_path).stem
    result_path = output_dir / f"{stem}_resultado.json"
    result_data = {
        "pdf_path": pdf_path,
        "edital_collection_id": ctx.edital_collection_id,
        "criterios_edital": ctx.criterios_edital,
        "company_chunks_count": len(ctx.company_chunks),
        "resultado_fit": ctx.resultado_fit,
    }

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"\n  Resultado salvo em: {result_path}")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
