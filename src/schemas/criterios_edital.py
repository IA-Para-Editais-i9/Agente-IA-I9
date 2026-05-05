from typing import Optional

from pydantic import BaseModel, Field


class CriteriosEdital(BaseModel):
    titulo: str
    orgao_financiador: str
    valor_maximo: Optional[float] = None
    prazo: str
    setores_elegiveis: list[str] = Field(default_factory=list)
    porte_empresa: list[str] = Field(default_factory=list)
    requisitos_tecnicos: list[str] = Field(default_factory=list)
    documentos_exigidos: list[str] = Field(default_factory=list)
    criterios_exclusao: list[str] = Field(default_factory=list)
    necessidade_parceria_ict: bool
    palavras_chave_tematicas: list[str] = Field(default_factory=list)
    resumo_objetivo: str
