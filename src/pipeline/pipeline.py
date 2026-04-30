from typing import List

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext

'''
orquestrador do pipeline
pega um dado(context) e passa por uma sequência de filtros
'''

class Pipeline:
    def __init__(self, filters: List[Filter]):
        self.filters = filters

    def run(self, context: PipelineContext) -> PipelineContext:
        for filtro in self.filters:
            context = filtro.process(context)

        return context
