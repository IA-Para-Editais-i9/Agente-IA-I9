from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f01_ingestion import IngestionFilter
from src.pipeline.pipeline import Pipeline


@dataclass
class PdfSmokeResult:
    pdf: str
    ok: bool
    elapsed_s: float
    markdown_chars: int = 0
    error: str | None = None
    skipped: bool = False


def _ocr_is_available() -> bool:
    """
    OCR é opcional. Consideramos "disponível" apenas se o pytesseract consegue
    listar idiomas no runtime (isso valida que o binário/tessdata existem).
    """
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        # Sanity check real: tenta rodar OCR mínimo; assim detecta falta de tessdata.
        img = Image.new("RGB", (1, 1), color=(255, 255, 255))
        _ = pytesseract.image_to_string(img, lang=os.getenv("TESSERACT_LANG", "por"))
        return True
    except Exception:
        return False


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _run_pytest() -> int:
    _print_header("pytest (unit + integration)")
    cmd = [sys.executable, "-m", "pytest", "-q"]
    proc = subprocess.run(cmd)
    if proc.returncode == 0:
        print("OK: pytest passou.")
    else:
        print(f"ERRO: pytest falhou (exit_code={proc.returncode}).")
    return proc.returncode


def _discover_pdfs() -> list[str]:
    base = Path("data")
    if not base.exists():
        return []
    return sorted(str(p) for p in base.rglob("*.pdf"))


def _smoke_test_pdfs(pdfs: list[str]) -> tuple[list[PdfSmokeResult], int]:
    _print_header("Smoke test: f01_ingestion (PDF -> Markdown)")

    if not pdfs:
        print("ERRO: nenhum PDF encontrado em `data/`.")
        return [], 1

    ocr_available = _ocr_is_available()
    if not ocr_available:
        print("WARN: OCR indisponível (tesseract/tessdata não configurado). PDFs escaneados podem ser ignorados.")

    pipeline = Pipeline([IngestionFilter()])
    results: list[PdfSmokeResult] = []

    for pdf in pdfs:
        t0 = perf_counter()
        try:
            ctx = PipelineContext(pdf_path=pdf)
            out = pipeline.run(ctx)
            md = (out.markdown_text or "").strip()
            elapsed = perf_counter() - t0

            ok = len(md) >= 200
            skipped = False
            err = None
            if not ok and not ocr_available:
                # Sem OCR, PDF escaneado pode resultar em markdown vazio.
                # Nesse cenário, reportamos como SKIP ao invés de FAIL.
                skipped = True
                err = "OCR indisponível; possível PDF escaneado (skip)"
            elif not ok:
                err = "markdown vazio/curto demais (<200 chars)"

            results.append(
                PdfSmokeResult(
                    pdf=pdf,
                    ok=ok,
                    elapsed_s=elapsed,
                    markdown_chars=len(md),
                    error=err,
                    skipped=skipped,
                )
            )
        except Exception as e:
            elapsed = perf_counter() - t0
            results.append(PdfSmokeResult(pdf=pdf, ok=False, elapsed_s=elapsed, error=str(e)))

    for r in results:
        status = "OK " if r.ok else ("SKIP" if r.skipped else "FAIL")
        extra = f"{r.markdown_chars} chars" if r.ok else (r.error or "erro desconhecido")
        print(f"{status} | {r.elapsed_s:6.2f}s | {extra:40} | {r.pdf}")

    fail_count = sum(1 for r in results if (not r.ok and not r.skipped))
    skip_count = sum(1 for r in results if r.skipped)
    ok_count = sum(1 for r in results if r.ok)

    if fail_count == 0:
        if skip_count:
            print(f"\nOK: {ok_count}/{len(results)} OK, {skip_count} SKIP (OCR indisponível).")
        else:
            print(f"\nOK: {len(results)}/{len(results)} PDFs convertidos com sucesso.")
        return results, 0

    print(f"\nERRO: {fail_count}/{len(results)} PDFs falharam.")
    return results, 1


def main() -> int:
    os.makedirs("outputs", exist_ok=True)

    pytest_code = _run_pytest()
    pdfs = _discover_pdfs()
    _, smoke_code = _smoke_test_pdfs(pdfs)

    _print_header("Resumo")
    if pytest_code == 0 and smoke_code == 0:
        print("TUDO CERTO: testes + ingestão PDF funcionando.")
        return 0

    print("ALGO QUEBROU: veja as seções acima (pytest / smoke test).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
