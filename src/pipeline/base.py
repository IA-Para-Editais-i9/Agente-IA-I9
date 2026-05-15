from abc import ABC, abstractmethod
from src.pipeline.context import PipelineContext

class Filter(ABC):
    @abstractmethod
    def process(self, ctx: PipelineContext) -> PipelineContext:
        pass
