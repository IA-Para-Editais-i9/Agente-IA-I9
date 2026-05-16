"""Testes unitarios do exportador de relatorio em Markdown (Squad E)."""

from __future__ import annotations

from src.frontend.utils.exportar import (
    format_acao,
    format_lista_simples,
    format_parceiro,
    gerar_markdown,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture mock baseada no MOCK_RESULTADO da E1
# ─────────────────────────────────────────────────────────────────────────────
MOCK_COMPLETO = {
    "edital_titulo": "Edital de Inovacao 001/2026",
    "orgao": "Ministerio da Ciencia e Tecnologia",
    "valor_estimado": "R$ 1.500.000,00",
    "prazo_entrega_proposta": "15/06/2026",
    "classificacao": "Alto",
    "percentual": 85,
    "justificativa_percentual": "Empresa tem aderencia tecnica forte.",
    "criterios_atendidos": [
        {"criterio": "Experiencia", "evidencia": "Portfolio com 3 projetos."}
    ],
    "gaps_identificados": [
        {"gap": "Cloud", "impacto": "Alto", "detalhe": "Exige Tier III."}
    ],
    "acoes_prioritarias": [
        {
            "titulo": "Firmar parceria AWS",
            "descricao": "Buscar Tier III.",
            "prazo_estimado": "5 dias",
            "esforco": "Medio",
            "responsavel_sugerido": "TI",
        }
    ],
    "parceiros_sugeridos": [
        {
            "nome": "CloudTech",
            "tipo": "Empresa",
            "match": 95,
            "motivo": "Especialistas em licitacoes.",
        }
    ],
    "recomendacoes": ["Ajustar proposta.", "Preparar CNDs."],
}


# ─────────────────────────────────────────────────────────────────────────────
# Testes do exportador completo
# ─────────────────────────────────────────────────────────────────────────────
def test_gerar_markdown_com_mock_completo_retorna_string():
    md = gerar_markdown(MOCK_COMPLETO)
    assert isinstance(md, str)
    assert len(md) > 100


def test_gerar_markdown_inclui_todas_secoes():
    md = gerar_markdown(MOCK_COMPLETO)
    assert "## Justificativa" in md
    assert "## Criterios Atendidos" in md
    assert "## Gaps Identificados" in md
    assert "## Top 3 Acoes Prioritarias" in md
    assert "## Recomendacoes" in md
    assert "## Parceiros Sugeridos" in md


def test_gerar_markdown_inclui_dados_principais():
    md = gerar_markdown(MOCK_COMPLETO)
    assert "Edital de Inovacao 001/2026" in md
    assert "85%" in md
    assert "Alto" in md
    assert "Ministerio da Ciencia" in md


def test_gerar_markdown_com_listas_vazias_nao_quebra():
    resultado_minimo = {
        "edital_titulo": "Edital Vazio",
        "orgao": "X",
        "percentual": 50,
        "classificacao": "Medio",
        "criterios_atendidos": [],
        "gaps_identificados": [],
        "acoes_prioritarias": [],
        "parceiros_sugeridos": [],
        "recomendacoes": [],
    }
    md = gerar_markdown(resultado_minimo)
    assert "Edital Vazio" in md
    assert "Nenhum item registrado" in md
    assert "Nenhuma acao prioritaria registrada" in md
    assert "Nenhum parceiro adicional necessario" in md


def test_gerar_markdown_com_resultado_invalido_nao_quebra():
    md = gerar_markdown(None)
    assert "Relatorio indisponivel" in md
    md_lista = gerar_markdown([])
    assert "Relatorio indisponivel" in md_lista


def test_gerar_markdown_usa_resumo_executivo_como_fallback():
    resultado = {
        "edital_titulo": "Teste",
        "resumo_executivo": "Texto do resumo executivo.",
    }
    md = gerar_markdown(resultado)
    assert "Texto do resumo executivo" in md


def test_gerar_markdown_limita_top3_acoes():
    resultado = {
        **MOCK_COMPLETO,
        "acoes_prioritarias": [
            {"titulo": f"Acao {i}"} for i in range(10)
        ],
    }
    md = gerar_markdown(resultado)
    # Deve incluir as 3 primeiras
    assert "1. **Acao 0**" in md
    assert "2. **Acao 1**" in md
    assert "3. **Acao 2**" in md
    # NAO deve incluir a quarta
    assert "4. **Acao 3**" not in md


# ─────────────────────────────────────────────────────────────────────────────
# Testes dos helpers de formatacao
# ─────────────────────────────────────────────────────────────────────────────
def test_format_lista_simples_aceita_strings():
    resultado = format_lista_simples(["item 1", "item 2"], prefixo="-")
    assert "- item 1" in resultado
    assert "- item 2" in resultado


def test_format_lista_simples_aceita_dicts():
    resultado = format_lista_simples(
        [{"titulo": "T", "descricao": "D"}], prefixo="-"
    )
    assert "**T**" in resultado
    assert "D" in resultado


def test_format_lista_simples_mistura_str_e_dict():
    resultado = format_lista_simples(
        ["string simples", {"criterio": "C", "evidencia": "E"}],
        prefixo="-",
    )
    assert "string simples" in resultado
    assert "**C**" in resultado


def test_format_lista_simples_lista_vazia():
    resultado = format_lista_simples([], prefixo="-")
    assert "_Nenhum item registrado._" in resultado


def test_format_acao_com_string():
    resultado = format_acao("Fazer X", 1)
    assert resultado == "1. Fazer X"


def test_format_acao_com_dict_completo():
    acao = {
        "titulo": "Negociar",
        "descricao": "Detalhe",
        "prazo_estimado": "3 dias",
        "esforco": "Baixo",
    }
    resultado = format_acao(acao, 2)
    assert "2. **Negociar**" in resultado
    assert "Detalhe" in resultado
    assert "3 dias" in resultado
    assert "Baixo" in resultado


def test_format_parceiro_com_dict():
    parceiro = {
        "nome": "Empresa X",
        "tipo": "ICT",
        "match": 90,
        "motivo": "Bom fit.",
    }
    resultado = format_parceiro(parceiro)
    assert "**Empresa X**" in resultado
    assert "(ICT)" in resultado
    assert "90%" in resultado


def test_format_parceiro_com_string():
    assert format_parceiro("Parceiro Simples") == "- Parceiro Simples"
