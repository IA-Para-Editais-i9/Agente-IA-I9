from abc import ABC, abstractmethod

from src.pipeline.context import PipelineContext


class Filter(ABC):
    @abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        """Executa o filtro e devolve o contexto atualizado."""
        raise NotImplementedError

    def process(self, ctx: PipelineContext) -> PipelineContext:
        """
        Compatibilidade com o orquestrador atual (`Pipeline.run`).
        O padrão do projeto usa `run(ctx)`.
        """
        return self.run(ctx)
