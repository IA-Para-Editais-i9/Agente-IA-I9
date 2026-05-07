from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineContext:
    pdf_path: str = ""  # entrada inicial
    markdown_text: str = ""  # saída do f01_ingestion

    # mudei aqui -lanna
    edital_collection_id: str = ""# saida f02 indexing
    empresa_collection_id: str = "" #docs i9

    criterios_edital: Optional[dict] = None  # saída do f03_extraction:
    company_chunks: list[str] = field(default_factory=list)  # saída do f04_retrieval
    resultado_fit: Optional[dict] = None  # saída do f05_inference
