from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext


class IngestionFilter(Filter):
    def run(self, ctx: PipelineContext) -> PipelineContext:
        return ctx
