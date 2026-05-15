"""Pagina de historico de analises previamente realizadas."""

from __future__ import annotations

from datetime import datetime

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def format_timestamp(iso_string: str) -> str:
    """Formata ISO 8601 em DD/MM/AAAA HH:MM."""
    if not iso_string:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return iso_string


def get_color_by_percentual(percentual: float) -> str:
    if percentual >= 80:
        return "#27ae60"
    if percentual >= 60:
        return "#f1c40f"
    if percentual >= 40:
        return "#f39c12"
    return "#e74c3c"


# ─────────────────────────────────────────────────────────────────────────────
# Empty state
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state() -> None:
    st.markdown(
        """
        <div class="historico-empty">
            <h3>Nenhuma analise realizada ainda</h3>
            <p>Faca o upload de um edital para comecar. As analises concluidas
            aparecem aqui automaticamente para consulta posterior.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "📄 Fazer primeira analise",
        type="primary",
        use_container_width=True,
    ):
        st.switch_page("pages/1_📄_Upload.py")


# ─────────────────────────────────────────────────────────────────────────────
# Card de um item do historico
# ─────────────────────────────────────────────────────────────────────────────
def render_item_historico(item: dict, index: int) -> None:
    percentual = item.get("percentual", 0)
    cor = get_color_by_percentual(percentual)
    titulo = item.get("edital_titulo") or item.get("edital_nome") or "Edital sem titulo"
    orgao = item.get("orgao", "—")
    classificacao = item.get("classificacao", "—")
    timestamp_fmt = format_timestamp(item.get("timestamp", ""))

    st.markdown(
        f"""
        <div class="historico-card" style="border-left-color:{cor};">
            <div class="historico-card-header">
                <span class="historico-titulo">{titulo}</span>
                <span class="historico-percentual-badge" style="background:{cor};">
                    {percentual}%
                </span>
            </div>
            <div class="historico-meta">
                🏛️ {orgao} &nbsp;·&nbsp; 🏷️ {classificacao} &nbsp;·&nbsp; 🕒 {timestamp_fmt}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "🔍 Ver Detalhes",
        key=f"ver_detalhes_{index}",
        use_container_width=True,
    ):
        st.session_state["resultado_fit"] = item["resultado_completo"]
        st.session_state["analise_concluida"] = True
        st.switch_page("pages/2_📊_Resultado.py")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    st.title("📚 Historico de Analises")
    st.markdown('<div class="linha-logo"></div>', unsafe_allow_html=True)

    historico = st.session_state.get("historico") or []

    if not historico:
        render_empty_state()
        return

    st.caption(f"{len(historico)} analise(s) realizada(s) nesta sessao.")

    for index, item in enumerate(historico):
        render_item_historico(item, index)

    st.divider()
    confirmar = st.checkbox(
        "Confirmar limpeza do historico (acao nao pode ser desfeita)",
        key="confirma_limpar_historico",
    )
    if st.button(
        "🗑️ Limpar Historico",
        disabled=not confirmar,
        use_container_width=True,
    ):
        st.session_state["historico"] = []
        st.rerun()


main()
