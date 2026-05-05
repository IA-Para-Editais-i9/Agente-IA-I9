from typing import List # tipagem
from src.pipeline.base import Filter # classe dos filtros
from src.pipeline.context import PipelineContext # objeto que carrega os dados

'''
orquestrador do pipeline
pega um dado(context) e passa por uma sequência de filtros
'''

class Pipeline:
    def __init__(self, filters: List[Filter]): # List -> lista de objetos do tipo Filter
        self.filters = filters # lista de filtros

    def run(self, context: PipelineContext) -> PipelineContext: # recebe e retorna PipelineContext
        for filter in self.filters:
            result = filter.process(context) # filtro processa a entrada
            if result is not None:      # compatível com ambas as convenções
                context = result
            
        return context