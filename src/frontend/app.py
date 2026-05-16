import streamlit as st

from src.frontend.utils.demo_data import seed_demo
from src.frontend.utils.plotly_theme import apply_theme
from src.frontend.utils.demo_data import render_backend_status_pill
from src.frontend.utils.styles import inject_global_ui

st.set_page_config(
    page_title="i9+ · Análise Inteligente de Editais",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_ui()
render_backend_status_pill()
apply_theme()

DEFAULT_STATE = {
    "analise_concluida": False,
    "edital_nome": None,
    "docs_empresa_nomes": [],
    "resultado_fit": None,
    "historico": [],
}
for chave, valor in DEFAULT_STATE.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor


# ─────────────────────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────────────────────
col_texto, col_visual = st.columns([1.25, 1], gap="large")

with col_texto:
    st.markdown(
        '<div class="eyebrow">✦ i9+ · Multi-Agente</div>',
        unsafe_allow_html=True,
    )
    st.title("Análise Inteligente de Editais de Fomento")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:1.12rem; color:#8193A0; line-height:1.65; max-width:540px;">'
        "Use IA multi-agente para avaliar o fit do seu projeto com editais públicos. "
        "Pipeline que lê, mapeia critérios, cruza com o acervo da empresa e "
        "entrega um diagnóstico estruturado em segundos."
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    col_cta1, col_cta2, col_cta3 = st.columns([1, 1, 1])
    with col_cta1:
        if st.button("Começar Análise", type="primary", use_container_width=True):
            st.switch_page("pages/1_📄_Upload.py")
    with col_cta2:
        if st.button("Modo Demo ✨", use_container_width=True):
            seed_demo(st.session_state)
            st.switch_page("pages/2_📊_Resultado.py")
    with col_cta3:
        if st.button("Ver Histórico", use_container_width=True):
            st.switch_page("pages/4_📚_Historico.py")

    st.caption(
        "💡 **Modo Demo** popula o app com 3 análises de exemplo "
        "(alto/médio/baixo) sem precisar de PDF nem backend."
    )

with col_visual:
    st.markdown(
        """
        <div style="
            background: #1A1F24;
            border: 1px solid rgba(129, 147, 160, 0.12);
            border-radius: 20px;
            padding: 28px 30px;
            position: relative;
            overflow: hidden;
            min-height: 320px;
        ">
            <div style="position:absolute; top:-80px; right:-80px;
                        width:260px; height:260px;
                        background: radial-gradient(circle, rgba(232,49,126,0.25), transparent 70%);
                        filter: blur(20px);"></div>
            <div style="position:relative; z-index:1;">
                <div class="pill-soft" style="margin-bottom:18px;">✦ Pipeline ativo</div>
                <div style="font-family: 'Inter', sans-serif;
                            font-size: 0.78rem;
                            color: #8193A0;
                            letter-spacing: 0.16em;
                            text-transform: uppercase;
                            margin-bottom: 10px;">
                    · Score médio · 30 dias
                </div>
                <div style="font-size: 4.2rem; font-weight: 700;
                            color: #FBF9F9; line-height: 1;
                            letter-spacing: -0.03em;">
                    85<span style="color:#E8317E;">%</span>
                </div>
                <div style="margin-top:18px; display:flex; gap:8px; flex-wrap:wrap;">
                    <span class="pill-soft" style="background:rgba(16,185,129,0.10); color:#10B981;">
                        ▲ Alta aderência
                    </span>
                    <span class="pill-soft" style="background:rgba(129,147,160,0.10); color:#8193A0;">
                        128 editais analisados
                    </span>
                </div>
                <div style="margin-top:26px; padding-top:20px;
                            border-top: 1px solid rgba(129,147,160,0.12);
                            display:flex; justify-content:space-between; gap:14px;">
                    <div>
                        <div style="font-size:0.7rem; color:#8193A0;
                                    letter-spacing:0.18em; text-transform:uppercase;
                                    margin-bottom:6px;">tempo médio</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#FBF9F9;">
                            &lt; 3min
                        </div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#8193A0;
                                    letter-spacing:0.18em; text-transform:uppercase;
                                    margin-bottom:6px;">precisão</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#FBF9F9;">
                            85<span style="color:#E8317E;">%</span>
                        </div>
                    </div>
                    <div>
                        <div style="font-size:0.7rem; color:#8193A0;
                                    letter-spacing:0.18em; text-transform:uppercase;
                                    margin-bottom:6px;">agentes</div>
                        <div style="font-size:1.4rem; font-weight:700; color:#FBF9F9;">
                            02
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br><br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FEATURES GRID (3 colunas)
# ─────────────────────────────────────────────────────────────────────────────
def _feature_card(icon: str, title: str, description: str) -> str:
    return f"""
    <div style="
        background: #1A1F24;
        border: 1px solid rgba(129, 147, 160, 0.12);
        border-radius: 16px;
        padding: 28px 26px;
        height: 100%;
        transition: all 0.25s ease;
    " onmouseover="this.style.borderColor='#E8317E'; this.style.transform='translateY(-3px)';"
       onmouseout="this.style.borderColor='rgba(129, 147, 160, 0.12)'; this.style.transform='translateY(0)';">
        <div style="
            width: 48px; height: 48px;
            background: rgba(232, 49, 126, 0.12);
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 18px;
        ">{icon}</div>
        <h3 style="margin: 0 0 8px 0; color: #FBF9F9; font-size: 1.2rem;">
            {title}
        </h3>
        <p style="margin: 0; color: #8193A0; font-size: 0.95rem; line-height: 1.55;">
            {description}
        </p>
    </div>
    """


st.markdown('<div class="eyebrow">· Pipeline em 3 estágios</div>', unsafe_allow_html=True)
st.markdown("### Da submissão ao score, em três etapas")
st.markdown("<br>", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3, gap="medium")
with col_a:
    st.markdown(
        _feature_card(
            "📄",
            "Upload de Edital",
            "Envie PDFs de editais e acervos. Validamos formato e tamanho automaticamente.",
        ),
        unsafe_allow_html=True,
    )
with col_b:
    st.markdown(
        _feature_card(
            "🤖",
            "Análise por IA",
            "Agentes CrewAI com Groq/Llama extraem critérios e cruzam com seu perfil.",
        ),
        unsafe_allow_html=True,
    )
with col_c:
    st.markdown(
        _feature_card(
            "📊",
            "Score Visual",
            "Gauge interativo Plotly, breakdown por critério e plano de ação priorizado.",
        ),
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# COMO FUNCIONA — fluxo em 4 passos + CTAs finais
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .how-it-works {
        margin: 1.5rem 0 1rem 0;
        padding: 2rem;
        background: linear-gradient(135deg, rgba(232, 49, 126, 0.05) 0%, rgba(199, 22, 107, 0.02) 100%);
        border-radius: 16px;
        border: 1px solid rgba(232, 49, 126, 0.18);
    }
    .how-it-works .section-title {
        text-align: center;
        color: #E8317E;
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.01em;
    }
    .how-it-works .section-subtitle {
        text-align: center;
        color: #8193A0;
        margin: 0 0 2rem 0;
        font-size: 1rem;
    }
    .how-it-works .steps-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.25rem;
    }
    @media (max-width: 900px) {
        .how-it-works .steps-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 500px) {
        .how-it-works .steps-grid { grid-template-columns: 1fr; }
    }
    .how-it-works .step-card {
        position: relative;
        padding: 1.6rem 1.25rem 1.25rem;
        background: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(232, 49, 126, 0.18);
        border-radius: 12px;
        transition: all 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    .how-it-works .step-card:hover {
        transform: translateY(-4px);
        border-color: rgba(232, 49, 126, 0.55);
        box-shadow: 0 12px 30px rgba(232, 49, 126, 0.18);
    }
    .how-it-works .step-number {
        position: absolute;
        top: -14px;
        left: 16px;
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #E8317E 0%, #C7166B 100%);
        color: #FFFFFF;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 1rem;
        box-shadow: 0 4px 10px rgba(232, 49, 126, 0.4);
    }
    .how-it-works .step-icon {
        font-size: 1.9rem;
        margin-bottom: 0.5rem;
        line-height: 1;
    }
    .how-it-works .step-card h3 {
        font-size: 1rem;
        font-weight: 600;
        margin: 0.35rem 0 0.5rem;
        color: #FBF9F9;
    }
    .how-it-works .step-card p {
        font-size: 0.86rem;
        color: #8193A0;
        margin: 0;
        line-height: 1.5;
    }
    .cta-helper {
        text-align: center;
        color: #8193A0;
        opacity: 0.85;
        font-size: 0.88rem;
        margin: 0.6rem 0 0 0;
    }
    </style>

    <div class="how-it-works">
        <h2 class="section-title">🚀 Como funciona</h2>
        <p class="section-subtitle">Em 4 passos você descobre se seu projeto tem fit com o edital</p>
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-number">1</div>
                <div class="step-icon">📄</div>
                <h3>Envie o edital</h3>
                <p>Upload do PDF do edital público que você quer analisar.</p>
            </div>
            <div class="step-card">
                <div class="step-number">2</div>
                <div class="step-icon">📁</div>
                <h3>Adicione seu acervo</h3>
                <p>Portfólio, certificações e contratos da empresa (opcional).</p>
            </div>
            <div class="step-card">
                <div class="step-number">3</div>
                <div class="step-icon">🤖</div>
                <h3>IA analisa o fit</h3>
                <p>Agentes CrewAI extraem critérios e cruzam com seu perfil.</p>
            </div>
            <div class="step-card">
                <div class="step-number">4</div>
                <div class="step-icon">📊</div>
                <h3>Receba o diagnóstico</h3>
                <p>Score, gaps, ações prioritárias e parceiros sugeridos.</p>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

col_cta_1, col_cta_2, col_cta_3 = st.columns(3, gap="medium")
with col_cta_1:
    if st.button(
        "🚀 Começar Análise",
        type="primary",
        use_container_width=True,
        key="cta_comecar",
    ):
        st.switch_page("pages/1_📄_Upload.py")
with col_cta_2:
    if st.button(
        "✨ Ver Modo Demo",
        use_container_width=True,
        key="cta_demo",
    ):
        seed_demo(st.session_state)
        st.switch_page("pages/2_📊_Resultado.py")
with col_cta_3:
    if st.button(
        "📚 Ver Histórico",
        use_container_width=True,
        key="cta_historico",
    ):
        st.switch_page("pages/4_📚_Historico.py")

st.markdown(
    "<p class='cta-helper'>💡 Sem PDF em mãos? Use o <b>Modo Demo</b> para explorar a interface com dados de exemplo.</p>",
    unsafe_allow_html=True,
)
