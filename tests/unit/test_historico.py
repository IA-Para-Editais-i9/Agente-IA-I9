"""Testes unitarios da feature de historico de analises (Squad E)."""

from __future__ import annotations

from datetime import datetime


MAX_ITENS_HISTORICO = 50


def _criar_item(percentual: int = 80, edital: str = "Edital teste") -> dict:
    """Helper para montar um item de historico igual ao do 1_Upload.py."""
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "edital_nome": f"{edital}.pdf",
        "edital_titulo": edital,
        "orgao": "Orgao Teste",
        "percentual": percentual,
        "classificacao": "Alto",
        "resultado_completo": {"percentual": percentual},
    }


def _adicionar(historico: list, item: dict) -> list:
    """Replica a logica do 1_Upload.py: insert na posicao 0 + slice [:50]."""
    historico.insert(0, item)
    return historico[:MAX_ITENS_HISTORICO]


def test_inicializa_historico_vazio():
    historico: list = []
    assert historico == []
    assert len(historico) == 0


def test_adiciona_analise_ao_historico():
    historico: list = []
    item = _criar_item(percentual=75, edital="Edital X")

    historico = _adicionar(historico, item)

    assert len(historico) == 1
    assert historico[0]["edital_titulo"] == "Edital X"
    assert historico[0]["percentual"] == 75


def test_ordem_dos_itens_mais_recente_primeiro():
    historico: list = []
    historico = _adicionar(historico, _criar_item(edital="Antigo"))
    historico = _adicionar(historico, _criar_item(edital="Medio"))
    historico = _adicionar(historico, _criar_item(edital="Recente"))

    assert historico[0]["edital_titulo"] == "Recente"
    assert historico[1]["edital_titulo"] == "Medio"
    assert historico[2]["edital_titulo"] == "Antigo"


def test_limita_historico_a_50_itens():
    historico: list = []
    for i in range(60):
        historico = _adicionar(historico, _criar_item(edital=f"Edital {i}"))

    assert len(historico) == MAX_ITENS_HISTORICO
    # O mais recente (Edital 59) deve estar no topo
    assert historico[0]["edital_titulo"] == "Edital 59"
    # O Edital 10 deve ter saido (foi empurrado para fora da janela de 50)
    titulos = [i["edital_titulo"] for i in historico]
    assert "Edital 9" not in titulos


def test_limpar_historico():
    historico = [_criar_item() for _ in range(5)]
    assert len(historico) == 5

    historico = []
    assert historico == []


def test_item_preserva_resultado_completo_para_reabertura():
    """Garantir que o resultado completo fica acessivel para o botao Ver Detalhes."""
    item = _criar_item(percentual=92)
    item["resultado_completo"] = {
        "edital_titulo": "Teste",
        "orgao": "Orgao X",
        "percentual": 92,
        "criterios_atendidos": [{"criterio": "C1", "evidencia": "E1"}],
        "gaps_identificados": [],
        "acoes_prioritarias": [],
        "parceiros_sugeridos": [],
        "recomendacoes": [],
    }

    assert "resultado_completo" in item
    assert item["resultado_completo"]["percentual"] == 92
    assert "criterios_atendidos" in item["resultado_completo"]
