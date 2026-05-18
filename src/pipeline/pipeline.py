from src.pipeline.context import PipelineContext
from src.pipeline.filters.f01_ingestion import IngestionFilter
from src.pipeline.filters.f02_indexing import IndexingFilter
from src.pipeline.filters.f03_extraction import ExtractionFilter
from src.pipeline.filters.f04_retrieval import RetrievalFilter
from src.pipeline.filters.f05_inference import InferenceFilter
from src.pipeline.base import Filter
from typing import List


class Pipeline:
    def __init__(self, filters: List[Filter]):
        self.filters = filters

    def run(self, context: PipelineContext) -> PipelineContext:
        for filter in self.filters:
            result = filter.process(context)
            if result is not None:
                context = result
        return context


def build_pipeline() -> Pipeline:
    """
    Instancia o pipeline completo com os 5 filtros na ordem correta.
    """
    return Pipeline(filters=[
        IngestionFilter(),   # f01 - PDF -> Markdown
        IndexingFilter(),    # f02 - Markdown -> ChromaDB
        ExtractionFilter(),  # f03 - Markdown -> CriteriosEdital
        RetrievalFilter(),   # f04 - Query -> Company chunks
        InferenceFilter(),   # f05 - Chunks -> ResultadoFit
    ])