import plotly.graph_objects as go
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Identidade visual i9+ — coerente com app.py e 1_📄_Upload.py da E1
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

    [data-testid="stMetric"] {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0, 11, 20, 0.06);
        border-left: 4px solid #0055FF;
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.78rem;
        letter-spacing: 0.5px;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #0A142F !important;
        font-weight: 900;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #FFFFFF;
        border-radius: 10px 10px 0 0;
        padding: 10px 18px;
        color: #0A142F;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] {
        background: #0055FF;
        color: #FFFFFF !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


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
# Helper: renderiza lista de criterios ou gaps em cards visuais
# ─────────────────────────────────────────────────────────────────────────────
def render_lista_criterios(lista, tipo):
    """Renderiza lista de criterios ou gaps em cards visuais.

    Aceita itens como string ou dict (com chaves 'criterio'/'gap',
    'evidencia'/'detalhe' e opcionalmente 'impacto').

    Args:
        lista: list[str] ou list[dict]
        tipo: "atendido" (verde) ou "gap" (vermelho)
    """
    if not lista:
        msg = (
            "Nenhum criterio atendido identificado."
            if tipo == "atendido"
            else "Nenhum gap identificado."
        )
        st.info(msg)
        return

    card_class = "criterio-card-atendido" if tipo == "atendido" else "criterio-card-gap"
    icone = "✅" if tipo == "atendido" else "❌"

    for item in lista:
        if isinstance(item, str):
            titulo = item
            descricao = ""
            impacto = ""
        elif isinstance(item, dict):
            titulo = item.get("criterio") or item.get("gap") or item.get("titulo") or ""
            descricao = (
                item.get("evidencia") or item.get("detalhe") or item.get("descricao") or ""
            )
            impacto = item.get("impacto", "") if tipo == "gap" else ""
        else:
            titulo = str(item)
            descricao = ""
            impacto = ""

        badge_impacto = (
            f'<span class="criterio-impacto-badge">Impacto: {impacto}</span>'
            if impacto
            else ""
        )
        descricao_html = (
            f'<div class="criterio-descricao">{descricao}</div>' if descricao else ""
        )

        st.markdown(
            f"""
            <div class="{card_class}">
                <div class="criterio-titulo">{icone} {titulo}{badge_impacto}</div>
                {descricao_html}
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
# Botoes de navegacao no rodape
# ─────────────────────────────────────────────────────────────────────────────
def render_navigation():
    st.divider()
    col_voltar, col_nova = st.columns(2)
    with col_voltar:
        if st.button("← Voltar ao Upload", use_container_width=True):
            st.switch_page("pages/1_📄_Upload.py")
    with col_nova:
        if st.button(
            "🔄 Nova Analise",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["analise_concluida"] = False
            st.session_state["resultado_fit"] = None
            st.switch_page("pages/1_📄_Upload.py")


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
    st.markdown('<div class="linha-logo"></div>', unsafe_allow_html=True)
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
    render_navigation()


main()
