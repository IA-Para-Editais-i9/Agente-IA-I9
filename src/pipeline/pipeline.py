from typing import List  # tipagem
import time  # NOVO — para o delay

from src.pipeline.base import Filter  # classe dos filtros
from src.pipeline.context import PipelineContext  # objeto que carrega os dados

"""
orquestrador do pipeline
pega um dado(context) e passa por uma sequência de filtros
"""

# Delay aplicado entre etapas do pipeline (em segundos).
# Protege APIs externas (Gemini/OpenAI) de estourar rate limits do free tier.
INTER_STEP_DELAY: float = 0.5


def apply_inter_step_delay() -> None:
    """Pausa entre etapas do pipeline. Centraliza a lógica de espaçamento."""
    if INTER_STEP_DELAY > 0:
        time.sleep(INTER_STEP_DELAY)


class Pipeline:
    def __init__(self, filters: List[Filter]):
        self.filters = filters

    def run(self, context: PipelineContext) -> PipelineContext:
        total = len(self.filters)
        for index, filter in enumerate(self.filters):
            result = filter.process(context)  # filtro processa a entrada
            if result is not None:  # compatível com ambas as convenções
                context = result

            # Aplica delay entre etapas, mas não depois da última
            is_last = index == total - 1
            if not is_last:
                apply_inter_step_delay()

        return context
