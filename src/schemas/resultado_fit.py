from typing import Literal

from pydantic import BaseModel, Field


class ResultadoFit(BaseModel):
    percentual_fit: float = Field(ge=0, le=100)
    classificacao: Literal["Alto", "Médio", "Baixo", "Inviável"]
    criterios_atendidos: list[str] = Field(default_factory=list)
    gaps_identificados: list[str] = Field(default_factory=list)
    recomendacoes_adequacao: list[str] = Field(default_factory=list)
    necessidade_parceria_ict: bool
    sugestao_parceiros: list[str] = Field(default_factory=list)
    justificativa_percentual: str
    acoes_prioritarias: list[str] = Field(default_factory=list, max_length=3)
