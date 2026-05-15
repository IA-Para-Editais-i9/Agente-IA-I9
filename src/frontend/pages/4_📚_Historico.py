"""Pagina de historico de analises previamente realizadas."""

from __future__ import annotations

from datetime import datetime

import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Identidade visual i9+ — coerente com app.py / 1_Upload / 2_Resultado
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

    .stApp {
        background-color: #F8FAFC;
        background-image:
            radial-gradient(at 10% 10%, rgba(0, 85, 255, 0.08) 0px, transparent 50%),
            radial-gradient(at 90% 10%, rgba(230, 0, 73, 0.05) 0px, transparent 50%);
        background-attachment: fixed;
    }

    h1 {
        background: linear-gradient(to right, #0A142F 0%, #0055FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        font-size: 2.8rem !important;
        margin-bottom: 0px !important;
    }

    .linha-logo {
        height: 6px; width: 100px;
        background: linear-gradient(to right, #E60049 0%, #0055FF 100%);
        border-radius: 4px; margin-top: 12px; margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(230, 0, 73, 0.4);
    }

    [data-testid="stSidebar"] {
        background-color: #050B14 !important;
        border-right: 2px solid rgba(0, 85, 255, 0.3);
    }
    [data-testid="stSidebarNav"] span, [data-testid="stSidebarNav"] svg {
        color: #FFFFFF !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] h2 {
        color: #F8FAFC !important;
    }
    [data-testid="stSidebar"] button {
        background-color: #0055FF !important;
        color: #FFFFFF !important;
        border: none !important;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] button:hover {
        background-color: #E60049 !important;
        transform: scale(1.02);
    }

    /* Card do historico */
    .historico-card {
        background: #FFFFFF;
        border-left: 6px solid #0055FF;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0, 11, 20, 0.06);
        animation: fadeInUp 0.35s ease-out;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .historico-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(0, 85, 255, 0.12);
    }
    .historico-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 6px;
    }
    .historico-titulo {
        color: #0A142F;
        font-weight: 800;
        font-size: 1.05rem;
        line-height: 1.3;
    }
    .historico-percentual-badge {
        color: #FFFFFF;
        font-weight: 900;
        padding: 4px 14px;
        border-radius: 999px;
        font-size: 0.95rem;
        letter-spacing: 0.3px;
    }
    .historico-meta {
        color: #64748B;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    /* Empty state amigavel */
    .historico-empty {
        background: #FFFFFF;
        border-left: 6px solid #E60049;
        padding: 28px;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(0, 11, 20, 0.06);
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .historico-empty h3 {
        color: #0A142F !important;
        margin-top: 0;
        margin-bottom: 10px;
        font-weight: 900;
    }
    .historico-empty p {
        color: #475569;
        font-size: 1.05rem;
        line-height: 1.5;
        margin: 0;
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
</style>
""",
    unsafe_allow_html=True,
)


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
