import streamlit as st

st.set_page_config(
    page_title="Analisador de Editais",
    page_icon="📄",
    layout="wide",
)

DEFAULT_STATE = {
    "analise_concluida": False,
    "edital_nome": None,
    "docs_empresa_nomes": [],
    "resultado_fit": None,
}
for chave, valor in DEFAULT_STATE.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

st.title("📄 Plataforma Inteligente de Análise de Editais")

st.markdown(
    """
Bem-vindo ao sistema de análise de aderência entre empresas e editais.

### Funcionalidades:
- Upload de edital em PDF
- Upload de documentos complementares
- Análise de fit
- Identificação de gaps
- Recomendações automáticas
"""
)

st.info("Utilize o menu lateral para acessar as páginas.")
