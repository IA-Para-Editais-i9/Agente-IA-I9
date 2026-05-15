import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Acesso ao session_state
# ─────────────────────────────────────────────────────────────────────────────
def get_resultado():
    """Le o resultado da analise persistido pela tela de Upload (E1)."""
    return st.session_state.get("resultado_fit")


# ─────────────────────────────────────────────────────────────────────────────
# Gauge plotly — percentual de fit com cores por faixa
# ─────────────────────────────────────────────────────────────────────────────
def cor_por_percentual(percentual):
    if percentual >= 80:
        return "#27ae60"  # verde — Alto
    if percentual >= 60:
        return "#f1c40f"  # amarelo — Medio
    if percentual >= 40:
        return "#f39c12"  # laranja — Baixo
    return "#e74c3c"      # vermelho — Inviavel


def render_gauge(percentual):
    cor = cor_por_percentual(percentual)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percentual,
            number={"suffix": "%", "font": {"size": 48, "color": cor}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": cor},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 40], "color": "#fde2e2"},
                    {"range": [40, 60], "color": "#fdecd2"},
                    {"range": [60, 80], "color": "#fdf6c2"},
                    {"range": [80, 100], "color": "#d6f3df"},
                ],
            },
        )
    )
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Classificacao em destaque + metric cards
# ─────────────────────────────────────────────────────────────────────────────
CLASSIFICACAO_CORES = {
    "Alto": "#27ae60",
    "Médio": "#f1c40f",
    "Medio": "#f1c40f",
    "Baixo": "#f39c12",
    "Inviável": "#e74c3c",
    "Inviavel": "#e74c3c",
}


def render_classificacao(classificacao):
    cor = CLASSIFICACAO_CORES.get(classificacao, "#0055FF")
    st.markdown(
        f"""
        <div style="background:{cor}; padding:24px; border-radius:16px;
                    text-align:center; color:white;
                    box-shadow:0 8px 20px rgba(0,0,0,0.12); margin-bottom:8px;">
            <div style="font-size:0.95rem; font-weight:700;
                        text-transform:uppercase; letter-spacing:1px; opacity:0.85;">
                Classificacao
            </div>
            <div style="font-size:2.6rem; font-weight:900; margin-top:6px;">
                {classificacao.upper()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(resultado):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Edital", resultado.get("edital_titulo", "—"))
    with col2:
        st.metric("Orgao", resultado.get("orgao", "—"))
    with col3:
        percentual = resultado.get("percentual", 0)
        st.metric("Percentual de Fit", f"{percentual}%")
    with col4:
        st.metric("Classificacao", resultado.get("classificacao", "—"))


# ─────────────────────────────────────────────────────────────────────────────
# Justificativa do percentual
# ─────────────────────────────────────────────────────────────────────────────
def render_justificativa(resultado):
    texto = resultado.get(
        "justificativa_percentual",
        resultado.get("resumo_executivo", ""),
    )
    if not texto:
        return
    st.subheader("Justificativa do percentual")
    st.markdown(
        f"""
        <div style="background:#F8FAFC; border-left:6px solid #0055FF;
                    padding:18px 20px; border-radius:10px;
                    color:#1f2937; line-height:1.55; font-size:1rem;
                    margin-top:6px;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tabs — esqueleto para incremento de E3 e E4
# ─────────────────────────────────────────────────────────────────────────────
def render_tabs_placeholders(resultado):
    tab_geral, tab_criterios, tab_acoes = st.tabs(
        ["Visao Geral", "Criterios e Gaps", "Acoes e Recomendacoes"]
    )

    with tab_geral:
        st.markdown("##### Resumo do diagnostico")
        n_criterios = len(resultado.get("criterios_atendidos", []))
        n_gaps = len(resultado.get("gaps_identificados", []))
        n_acoes = len(resultado.get("acoes_prioritarias", []))
        st.write(
            f"Foram identificados **{n_criterios}** criterios atendidos, "
            f"**{n_gaps}** gaps e **{n_acoes}** acoes prioritarias. "
            "Use as abas ao lado para o detalhamento completo."
        )

    with tab_criterios:
        # ─────────────────────────────────────────────────────────────────
        # [E3] INSERIR AQUI — Tab: Criterios e Gaps
        # Consumir: resultado["criterios_atendidos"] e resultado["gaps_identificados"]
        # ─────────────────────────────────────────────────────────────────
        st.info("Em desenvolvimento — Task E3 (Criterios Atendidos vs Gaps)")

    with tab_acoes:
        # ─────────────────────────────────────────────────────────────────
        # [E4] INSERIR AQUI — Tab: Acoes e Recomendacoes
        # Consumir: resultado["acoes_prioritarias"], resultado["recomendacoes"],
        #           resultado["parceiros_sugeridos"]
        # ─────────────────────────────────────────────────────────────────
        st.info("Em desenvolvimento — Task E4 (Acoes Prioritarias e Recomendacoes)")


# ─────────────────────────────────────────────────────────────────────────────
# Empty state — quando o usuario acessa direto sem ter feito upload
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state():
    st.warning(
        "Nenhuma analise disponivel. Faca o upload de um edital "
        "na pagina **Upload** antes de visualizar o resultado."
    )
    if st.button("Ir para Upload", type="primary", use_container_width=True):
        st.switch_page("pages/1_📄_Upload.py")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
def render_header(resultado):
    titulo = resultado.get("edital_titulo", "Edital sem titulo")
    orgao = resultado.get("orgao", "Orgao nao informado")
    st.title("Diagnostico de Viabilidade")
    st.caption(f"{titulo} — {orgao}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    resultado = get_resultado()
    if not resultado:
        render_empty_state()
    render_header(resultado)
    render_metric_cards(resultado)
    col_gauge, col_class = st.columns([1.4, 1])
    with col_gauge:
        render_gauge(resultado.get("percentual", 0))
    with col_class:
        render_classificacao(resultado.get("classificacao", "—"))
    render_justificativa(resultado)
    render_tabs_placeholders(resultado)


main()
