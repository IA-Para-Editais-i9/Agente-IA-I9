"""Exportacao de relatorio de analise em formato Markdown.

A funcao principal `gerar_markdown(resultado)` recebe o dict do
`resultado_fit` populado pela tela de Upload (com mesmo schema do
MOCK_RESULTADO da E1) e devolve uma string Markdown pronta para ser
servida via `st.download_button`.

Tolerante a campos opcionais e a itens que sejam string OU dict
(mesmo padrao das funcoes render_* do painel de Resultado).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formatacao
# ─────────────────────────────────────────────────────────────────────────────
def _safe(value: Any, default: str = "—") -> str:
    if value is None or value == "":
        return default
    return str(value)


def format_lista_simples(lista: list, prefixo: str = "-") -> str:
    """Formata lista de strings/dicts em bullet list Markdown.

    - Strings viram `{prefixo} {item}`
    - Dicts: usa 'titulo' ou 'criterio' ou 'gap' como rotulo e
      'descricao'/'evidencia'/'detalhe' como subtitulo entre parenteses.
    """
    if not lista:
        return "_Nenhum item registrado._"

    linhas: list[str] = []
    for item in lista:
        if isinstance(item, str):
            linhas.append(f"{prefixo} {item}")
        elif isinstance(item, dict):
            rotulo = (
                item.get("titulo")
                or item.get("criterio")
                or item.get("gap")
                or item.get("recomendacao")
                or ""
            )
            descricao = (
                item.get("descricao")
                or item.get("evidencia")
                or item.get("detalhe")
                or ""
            )
            if descricao:
                linhas.append(f"{prefixo} **{rotulo}** — {descricao}")
            else:
                linhas.append(f"{prefixo} {rotulo}")
        else:
            linhas.append(f"{prefixo} {item}")
    return "\n".join(linhas)


def format_acao(acao: Any, numero: int) -> str:
    """Formata uma acao do top 3 em bloco numerado."""
    if isinstance(acao, str):
        return f"{numero}. {acao}"
    if not isinstance(acao, dict):
        return f"{numero}. {acao}"

    titulo = acao.get("titulo") or acao.get("acao") or ""
    descricao = acao.get("descricao") or acao.get("detalhe") or ""
    prazo = acao.get("prazo_estimado") or acao.get("prazo") or ""
    esforco = acao.get("esforco", "")
    responsavel = acao.get("responsavel_sugerido") or acao.get("responsavel") or ""

    linhas = [f"{numero}. **{titulo}**"]
    if descricao:
        linhas.append(f"   - Descricao: {descricao}")
    if prazo:
        linhas.append(f"   - Prazo estimado: {prazo}")
    if esforco:
        linhas.append(f"   - Esforco: {esforco}")
    if responsavel:
        linhas.append(f"   - Responsavel sugerido: {responsavel}")
    return "\n".join(linhas)


def format_parceiro(parceiro: Any) -> str:
    if isinstance(parceiro, str):
        return f"- {parceiro}"
    if not isinstance(parceiro, dict):
        return f"- {parceiro}"

    nome = parceiro.get("nome") or parceiro.get("parceiro") or ""
    tipo = parceiro.get("tipo", "")
    motivo = parceiro.get("motivo") or parceiro.get("justificativa") or ""
    match = parceiro.get("match")
    contato = parceiro.get("contato", "")

    partes = [f"**{nome}**"]
    if tipo:
        partes.append(f"({tipo})")
    if match is not None:
        partes.append(f"— Match {match}%")
    linha_principal = f"- {' '.join(partes)}"
    if motivo:
        linha_principal += f": {motivo}"
    if contato:
        linha_principal += f"\n   - Contato: {contato}"
    return linha_principal


# ─────────────────────────────────────────────────────────────────────────────
# Geracao do relatorio em Markdown
# ─────────────────────────────────────────────────────────────────────────────
def gerar_markdown(resultado: dict) -> str:
    """Constroi o relatorio completo em Markdown.

    O `resultado` segue o schema do MOCK_RESULTADO da E1
    (edital_titulo, orgao, valor_estimado, prazo_entrega_proposta,
    classificacao, percentual, justificativa_percentual OU
    resumo_executivo, criterios_atendidos, gaps_identificados,
    acoes_prioritarias, recomendacoes, parceiros_sugeridos).
    """
    if not isinstance(resultado, dict):
        return "# Relatorio indisponivel\n\nNenhum resultado de analise encontrado."

    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    titulo = _safe(resultado.get("edital_titulo"), "Edital sem titulo")
    orgao = _safe(resultado.get("orgao"))
    valor = _safe(resultado.get("valor_estimado"))
    prazo = _safe(resultado.get("prazo_entrega_proposta"))
    classificacao = _safe(resultado.get("classificacao"))
    percentual = resultado.get("percentual", 0)
    justificativa = (
        resultado.get("justificativa_percentual")
        or resultado.get("resumo_executivo")
        or "Sem justificativa registrada."
    )

    criterios = resultado.get("criterios_atendidos", []) or []
    gaps = resultado.get("gaps_identificados", []) or []
    acoes = resultado.get("acoes_prioritarias", []) or []
    recomendacoes = resultado.get("recomendacoes", []) or []
    parceiros = resultado.get("parceiros_sugeridos", []) or []

    acoes_top3 = acoes[:3]
    if acoes_top3:
        acoes_render = "\n\n".join(
            format_acao(a, idx) for idx, a in enumerate(acoes_top3, start=1)
        )
    else:
        acoes_render = "_Nenhuma acao prioritaria registrada._"

    parceiros_render = (
        "\n".join(format_parceiro(p) for p in parceiros)
        if parceiros
        else "_Nenhum parceiro adicional necessario para esse edital._"
    )

    return f"""# Analise de Edital — {titulo}

**Orgao:** {orgao}
**Data da analise:** {timestamp}
**Classificacao:** {classificacao}
**Percentual de Fit:** {percentual}%
**Valor estimado:** {valor}
**Prazo de entrega:** {prazo}

---

## Justificativa do percentual

{justificativa}

---

## Criterios Atendidos ({len(criterios)})

{format_lista_simples(criterios, prefixo="- ✅")}

---

## Gaps Identificados ({len(gaps)})

{format_lista_simples(gaps, prefixo="- ❌")}

---

## Top 3 Acoes Prioritarias

{acoes_render}

---

## Recomendacoes de Adequacao

{format_lista_simples(recomendacoes, prefixo="-")}

---

## Parceiros Sugeridos

{parceiros_render}

---

*Relatorio gerado em {timestamp} pelo Sistema de Analise de Editais i9+.*
"""
