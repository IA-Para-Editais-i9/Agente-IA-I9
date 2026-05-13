from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ResultadoFit(BaseModel):
    percentual_fit: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score de fit de 0 a 100",
    )
    classificacao: Literal["Alto", "Médio", "Baixo", "Inviável"] = Field(
        ...,
        description="Classificação derivada do percentual_fit",
    )
    criterios_atendidos: list[str] = Field(
        default_factory=list,
        description="Critérios do edital que a empresa já atende",
    )
    gaps_identificados: list[str] = Field(
        default_factory=list,
        description="Critérios do edital que a empresa NÃO atende",
    )
    recomendacoes_adequacao: list[str] = Field(
        default_factory=list,
        description="Ações que a empresa pode tomar para aumentar o fit",
    )
    necessidade_parceria_ict: bool = Field(
        ...,
        description=(
            "True se o edital exige parceria com ICT (universidade, instituto, etc.)"
        ),
    )
    sugestao_parceiros: list[str] = Field(
        default_factory=list,
        description=(
            "Parceiros concretos sugeridos (ex: UTFPR, SENAI-PR). "
            "Lista vazia se não aplicável."
        ),
    )
    justificativa_percentual: str = Field(
        ...,
        description="Explicação em texto de como o percentual foi calculado",
    )
    acoes_prioritarias: list[str] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="Top 3 ações mais urgentes para aumentar o fit",
    )

    @field_validator("classificacao", mode="after")
    @classmethod
    def check_classificacao_vs_percentual(cls, v: str, info) -> str:
        pct = info.data.get("percentual_fit")
        if pct is None:
            return v

        mapa = {
            "Inviável": (0.0, 25.0),
            "Baixo": (25.0, 50.0),
            "Médio": (50.0, 75.0),
            "Alto": (75.0, 100.01),
        }
        min_pct, max_pct = mapa[v]
        if not (min_pct <= pct < max_pct):
            raise ValueError(
                f"Classificação '{v}' incompatível com percentual_fit={pct}. "
                f"Esperado entre {min_pct} e {max_pct}."
            )
        return v
