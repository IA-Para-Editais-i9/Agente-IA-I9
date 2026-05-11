#!/usr/bin/env python
"""
Batch: converte PDFs de editais em Markdown, chunkifica e indexa no ChromaDB.

Uso:
    python scripts/index_editais.py
    python scripts/index_editais.py --pdf-dir data/editais/samples
    python scripts/index_editais.py --md-dir data/editais/markdown --collection editais
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from src.infrastructure.chroma_manager import ChromaManager
from src.pipeline.filters.f01_ingestion import pdf_to_markdown
from src.utils.batch_processor import BatchProcessor
from src.utils.chunking import chunk_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _progress(current: int, total: int, path: str) -> None:
    print(f"  [{current}/{total}] {Path(path).name}")


def index_editais(
    pdf_dir: str = "data/editais/samples",
    md_dir: str = "data/editais/markdown",
    collection_name: str = "editais",
    chroma_dir: str = "./chroma_db",
) -> dict:
    """
    Converte PDFs → Markdown → chunks e indexa no ChromaDB.

    Retorna estatísticas: {"total_pdfs", "ok", "failed", "total_chunks"}.
    """
    pdf_path = Path(pdf_dir)
    md_path = Path(md_dir)
    md_path.mkdir(parents=True, exist_ok=True)

    processor = BatchProcessor(progress_callback=_progress)
    chroma = ChromaManager(persist_directory=chroma_dir)

    pdf_files = processor.scan_pdfs(str(pdf_path))
    if not pdf_files:
        print(f"Nenhum PDF encontrado em: {pdf_dir}")
        return {"total_pdfs": 0, "ok": 0, "failed": 0, "total_chunks": 0}

    print(f"\n{'='*60}")
    print("  Batch indexação de editais")
    print(f"  PDFs: {pdf_dir}  ({len(pdf_files)} arquivos)")
    print(f"  Markdown: {md_dir}")
    print(f"  Coleção ChromaDB: {collection_name}")
    print(f"{'='*60}\n")

    all_ids: list[str] = []
    all_chunks: list[str] = []
    all_metadatas: list[dict] = []
    ok_count = 0
    fail_count = 0

    for i, pdf_file in enumerate(pdf_files, 1):
        stem = Path(pdf_file).stem
        print(f"  [{i}/{len(pdf_files)}] {Path(pdf_file).name}")

        # ── 1. PDF → Markdown ──────────────────────────────
        try:
            markdown = pdf_to_markdown(pdf_file)
        except Exception as e:
            print(f"    ERRO na conversão: {e}")
            fail_count += 1
            continue

        if not markdown or len(markdown.strip()) < 50:
            print(f"    AVISO: markdown muito curto ({len(markdown)} chars), pulando.")
            fail_count += 1
            continue

        # ── 2. Salvar .md para inspeção ────────────────────
        md_file = md_path / f"{stem}.md"
        md_file.write_text(markdown, encoding="utf-8")

        # ── 3. Chunkificar ─────────────────────────────────
        chunks = chunk_text(markdown)
        if not chunks:
            print("    AVISO: nenhum chunk gerado, pulando.")
            fail_count += 1
            continue

        # ── 4. Preparar para indexação ─────────────────────
        metadata_base = BatchProcessor().get_file_metadata(pdf_file, "edital")

        for j, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            all_ids.append(chunk_id)
            all_chunks.append(chunk)

            meta = metadata_base.copy()
            meta["chunk_index"] = j
            meta["edital_stem"] = stem
            all_metadatas.append(meta)

        ok_count += 1
        print(f"    OK: {len(chunks)} chunks | md salvo: {md_file.name}")

    # ── 5. Indexar tudo de uma vez ─────────────────────────
    if all_chunks:
        # ChromaDB tem limite de ~5461 por batch; dividir se necessário
        batch_size = 5000
        for start in range(0, len(all_chunks), batch_size):
            end = min(start + batch_size, len(all_chunks))
            chroma.index_documents(
                collection_name=collection_name,
                ids=all_ids[start:end],
                documents=all_chunks[start:end],
                metadatas=all_metadatas[start:end],
            )

    info = chroma.get_collection_info(collection_name)
    stats = {
        "total_pdfs": len(pdf_files),
        "ok": ok_count,
        "failed": fail_count,
        "total_chunks": len(all_chunks),
    }

    print(f"\n{'='*60}")
    print("  Resultado")
    print(f"  PDFs processados: {ok_count}/{len(pdf_files)}")
    print(f"  Falhas: {fail_count}")
    print(f"  Chunks indexados neste batch: {len(all_chunks)}")
    print(f"  Total na coleção '{collection_name}': {info['count']}")
    print(f"  Markdowns salvos em: {md_dir}/")
    print(f"{'='*60}\n")

    return stats


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Converte PDFs de editais para Markdown e indexa no ChromaDB."
    )
    parser.add_argument(
        "--pdf-dir",
        default="data/editais/samples",
        help="Diretório com PDFs de editais (default: data/editais/samples)",
    )
    parser.add_argument(
        "--md-dir",
        default="data/editais/markdown",
        help="Diretório para salvar Markdowns (default: data/editais/markdown)",
    )
    parser.add_argument(
        "--collection",
        default="editais",
        help="Nome da coleção no ChromaDB (default: editais)",
    )
    parser.add_argument(
        "--chroma-dir",
        default="./chroma_db",
        help="Diretório de persistência do ChromaDB (default: ./chroma_db)",
    )
    args = parser.parse_args()

    stats = index_editais(
        pdf_dir=args.pdf_dir,
        md_dir=args.md_dir,
        collection_name=args.collection,
        chroma_dir=args.chroma_dir,
    )

    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
