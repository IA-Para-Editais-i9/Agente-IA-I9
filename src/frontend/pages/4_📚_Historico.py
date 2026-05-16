"""Pagina de historico de analises previamente realizadas."""

from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

from src.frontend.utils.exportar import gerar_markdown


# ─────────────────────────────────────────────────────────────────────────────
# Identidade visual i9+ — coerente com app.py / 1_Upload / 2_Resultado
# ─────────────────────────────────────────────────────────────────────────────
from src.frontend.utils.plotly_theme import apply_theme
from src.frontend.utils.demo_data import render_backend_status_pill
from src.frontend.utils.styles import inject_global_ui

inject_global_ui()
render_backend_status_pill()
apply_theme()



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
    """Paleta semantica coerente com o tema (success/warning/error)."""
    if percentual >= 70:
        return "#10B981"
    if percentual >= 40:
        return "#F59E0B"
    return "#EF4444"


def _slug(texto: str) -> str:
    """Converte titulo em slug seguro para nome de arquivo."""
    if not texto:
        return "analise"
    base = re.sub(r"[^a-zA-Z0-9_-]+", "_", texto).strip("_").lower()
    return base[:60] or "analise"


# ─────────────────────────────────────────────────────────────────────────────
# Empty state
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state() -> None:
    st.markdown(
        """
        <div style="background:#1A1F24;
                    border:1px solid rgba(129,147,160,0.12);
                    padding:48px 36px;
                    border-radius:16px;
                    text-align:center;
                    margin: 20px 0;">
            <div style="font-size: 3rem; margin-bottom: 18px;">✦</div>
            <h3 style="color:#FBF9F9; margin:0 0 10px 0; font-size:1.3rem;">
                Nenhuma análise realizada ainda
            </h3>
            <p style="color:#8193A0; font-size:0.98rem; line-height:1.6;
                      max-width:420px; margin: 0 auto 24px;">
                Faça o upload de um edital para começar. As análises concluídas
                aparecem aqui automaticamente para consulta posterior.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _, col_centro, _ = st.columns([1, 1.4, 1])
    with col_centro:
        if st.button(
            "Fazer primeira análise",
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
        <div style="background:#1A1F24;
                    border:1px solid rgba(129,147,160,0.12);
                    border-left:3px solid {cor};
                    border-radius:16px;
                    padding:20px 22px;
                    margin-bottom:10px;
                    transition: all 0.25s ease;"
             onmouseover="this.style.borderColor='#E8317E'; this.style.transform='translateY(-2px)';"
             onmouseout="this.style.borderColor='rgba(129,147,160,0.12)'; this.style.transform='translateY(0)';">
            <div style="display:flex; align-items:center; justify-content:space-between;
                        gap:14px; flex-wrap:wrap; margin-bottom:8px;">
                <span style="color:#FBF9F9; font-weight:600; font-size:1.05rem;
                             letter-spacing:-0.01em;">{titulo}</span>
                <span style="background:{cor}1A; color:{cor};
                             font-weight:700; padding:4px 12px;
                             border-radius:999px; font-size:0.85rem;
                             border: 1px solid {cor}33;">
                    {percentual}%
                </span>
            </div>
            <div style="color:#8193A0; font-size:0.85rem; line-height:1.6;">
                🏛️ {orgao} &nbsp;·&nbsp; 🏷️ {classificacao} &nbsp;·&nbsp; 🕒 {timestamp_fmt}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_ver, col_exportar = st.columns(2)
    with col_ver:
        if st.button(
            "🔍 Ver Detalhes",
            key=f"ver_detalhes_{index}",
            use_container_width=True,
        ):
            st.session_state["resultado_fit"] = item["resultado_completo"]
            st.session_state["analise_concluida"] = True
            st.switch_page("pages/2_📊_Resultado.py")
    with col_exportar:
        resultado_completo = item.get("resultado_completo") or {}
        slug = _slug(resultado_completo.get("edital_titulo") or titulo)
        ts_arquivo = item.get("timestamp", "").replace(":", "").replace("-", "")[:13]
        st.download_button(
            label="📥 Exportar",
            data=gerar_markdown(resultado_completo),
            file_name=f"analise_{slug}_{ts_arquivo}.md",
            mime="text/markdown",
            key=f"exportar_{index}",
            use_container_width=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    if "historico" not in st.session_state:
        st.session_state["historico"] = []

    st.markdown('<div class="eyebrow">· Histórico</div>', unsafe_allow_html=True)
    st.title("Suas análises anteriores")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)

    historico = st.session_state.get("historico") or []

    if not historico:
        render_empty_state()
        return

    # Filtros pills (visuais — só destacam total atual)
    total = len(historico)
    alto = sum(1 for it in historico if it.get("percentual", 0) >= 70)
    medio = sum(1 for it in historico if 40 <= it.get("percentual", 0) < 70)
    baixo = sum(1 for it in historico if it.get("percentual", 0) < 40)

    st.markdown(
        f"""
        <div style="display:flex; gap:8px; flex-wrap:wrap; margin: 4px 0 22px;">
            <span style="background:rgba(232,49,126,0.12); color:#E8317E;
                         padding:6px 16px; border-radius:999px;
                         font-size:0.82rem; font-weight:600;
                         border:1px solid rgba(232,49,126,0.30);">
                Todas · {total}
            </span>
            <span style="background:rgba(16,185,129,0.10); color:#10B981;
                         padding:6px 16px; border-radius:999px;
                         font-size:0.82rem; font-weight:600;
                         border:1px solid rgba(16,185,129,0.22);">
                Score alto · {alto}
            </span>
            <span style="background:rgba(245,158,11,0.10); color:#F59E0B;
                         padding:6px 16px; border-radius:999px;
                         font-size:0.82rem; font-weight:600;
                         border:1px solid rgba(245,158,11,0.22);">
                Médio · {medio}
            </span>
            <span style="background:rgba(239,68,68,0.10); color:#EF4444;
                         padding:6px 16px; border-radius:999px;
                         font-size:0.82rem; font-weight:600;
                         border:1px solid rgba(239,68,68,0.22);">
                Baixo · {baixo}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, item in enumerate(historico):
        render_item_historico(item, index)

    st.divider()
    confirmar = st.checkbox(
        "Confirmar limpeza do histórico (ação não pode ser desfeita)",
        key="confirma_limpar_historico",
    )
    if st.button(
        "Limpar histórico",
        disabled=not confirmar,
        use_container_width=True,
    ):
        st.session_state["historico"] = []
        st.rerun()


main()
