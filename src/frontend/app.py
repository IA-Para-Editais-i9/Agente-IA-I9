import streamlit as st

st.set_page_config(
    page_title="Pipeline de Análise de Editais",
    page_icon="⚡",
    layout="wide",
)

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

    [data-testid="stSidebar"] {
        background-color: #050B14 !important;
        border-right: 2px solid rgba(0, 85, 255, 0.3);
        box-shadow: 5px 0 15px rgba(0,0,0,0.1);
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

    h1 {
        background: linear-gradient(to right, #0A142F 0%, #0055FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        font-size: 3.5rem !important;
        margin-bottom: 0px !important;
    }

    .linha-logo {
        height: 6px; width: 100px;
        background: linear-gradient(to right, #E60049 0%, #0055FF 100%);
        border-radius: 4px; margin-top: 15px; margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(230, 0, 73, 0.4);
    }

    .hero-img {
        border-radius: 20px;
        box-shadow: 0 25px 50px rgba(0, 11, 20, 0.15);
        width: 100%; height: 400px; object-fit: cover;
    }

    .grid-cards { display: flex; gap: 30px; margin-top: 30px; margin-bottom: 40px; }

    .meu-card {
        background: #FFFFFF;
        border-radius: 20px; flex: 1; overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(0, 85, 255, 0.1);
        border-bottom: 5px solid #0055FF;
        transition: all 0.3s ease;
    }
    .meu-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 20px 40px rgba(0, 85, 255, 0.15);
        border-bottom: 5px solid #E60049;
    }
    .meu-card img { width: 100%; height: 160px; object-fit: cover; }
    .meu-card-conteudo { padding: 25px; }
    .meu-card h3 { color: #0A142F !important; font-size: 1.4rem; font-weight: 900; margin-top: 0; }
    .meu-card p { color: #475569; font-size: 1.05rem; line-height: 1.5; margin: 0; }
</style>
""",
    unsafe_allow_html=True,
)

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

col_texto, col_imagem = st.columns([1.2, 1], gap="large")

with col_texto:
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Inteligência Artificial em Editais")
    st.markdown('<div class="linha-logo"></div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color: #334155; font-size: 1.2rem; line-height: 1.6;">'
        "<b>Da mesma forma que a i9+ inova em energia</b>, nossa plataforma traz "
        "a revolução de dados para a análise pública.<br><br>"
        "Utilizamos modelos avançados de IA para ler editais complexos, mapear "
        "requisitos técnicos e cruzar com o acervo da sua empresa em tempo real."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if not st.session_state["analise_concluida"]:
        st.info(
            "👈 Comece agora: Acesse a página de Upload no menu lateral.",
            icon="🚀",
        )

with col_imagem:
    st.markdown(
        '<img src="https://images.unsplash.com/photo-1466611653911-95081537e5b7?q=80&w=1000&auto=format&fit=crop" '
        'class="hero-img">',
        unsafe_allow_html=True,
    )

st.markdown(
    "<br><hr style='border-color: rgba(0,0,0,0.05);'><br>", unsafe_allow_html=True
)
st.markdown(
    "<h2 style='text-align: center; color: #0A142F; font-size: 2.5rem; font-weight: 900;'>"
    "Nossa Abordagem Única</h2>",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="grid-cards">
    <div class="meu-card">
        <img src="https://images.unsplash.com/photo-1586281380349-632531db7ed4?q=80&w=600&auto=format&fit=crop">
        <div class="meu-card-conteudo">
            <h3>1. Triagem Ágil</h3>
            <p>Upload seguro de PDFs dos editais, acervos, balanços e portfólios no nosso ambiente blindado.</p>
        </div>
    </div>
    <div class="meu-card">
        <img src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=600&auto=format&fit=crop">
        <div class="meu-card-conteudo">
            <h3>2. Motor IA de Ponta</h3>
            <p>Extração de cláusulas críticas e identificação de exigências ocultas de forma automatizada.</p>
        </div>
    </div>
    <div class="meu-card">
        <img src="https://images.unsplash.com/photo-1460925895917-afdab827c52f?q=80&w=600&auto=format&fit=crop">
        <div class="meu-card-conteudo">
            <h3>3. Decisão Estratégica</h3>
            <p>Dashboard dinâmico com Score de Fit, plano de ação estruturado e parceiros sugeridos.</p>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
