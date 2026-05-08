from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineContext:
    pdf_path: str = ""  # entrada inicial
    markdown_text: str = ""  # saída do f01_ingestion
    chroma_collection_id: str = ""  # saída do f02_indexing
    criterios_edital: Optional[dict] = None  # saída do f03_extraction
    company_chunks: list[str] = field(default_factory=list)  # saída do f04_retrieval
    resultado_fit: Optional[dict] = None  # saída do f05_inference
