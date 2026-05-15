#!/usr/bin/env python
import os
import sys
import uuid

from src.pipeline.context import PipelineContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.infrastructure.chroma_manager import ChromaManager
from src.pipeline.filters.f01_ingestion import IngestionFilter
from src.utils.batch_processor import BatchProcessor
from src.utils.chunking import chunk_text


def index_company_documents():
    ingestion = IngestionFilter()
    chroma = ChromaManager()
    processor = BatchProcessor()

    all_ids = []
    all_chunks = []
    all_metadatas = []

    directories = {
        "portfolio": "portfolio",
        "contratos": "contratos",
        "certificacoes": "certificacoes"
    }

    for doc_type, subdir in directories.items():
        dir_path = f"data/empresa/{subdir}"
        pdf_files = processor.scan_pdfs(dir_path)

        for pdf_path in pdf_files:
            # processa cada PDF
            '''
            temp_ctx = PipelineContext(pdf_path=pdf_path)
            pipeline = Pipeline([IngestionFilter()])
            pipeline.run(temp_ctx)
            '''
            temp_ctx = PipelineContext(pdf_path=pdf_path)
            ingestion.process(temp_ctx)

            chunks = chunk_text(temp_ctx.markdown_text)
            metadata = processor.get_file_metadata(pdf_path, doc_type)

            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                all_ids.append(chunk_id)
                all_chunks.append(chunk)

                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                all_metadatas.append(chunk_metadata)

    # indexar tudo
    chroma.index_documents(
        collection_name="perfil_empresa",
        ids=all_ids,
        documents=all_chunks,
        metadatas=all_metadatas
    )


if __name__ == "__main__":
    index_company_documents()
