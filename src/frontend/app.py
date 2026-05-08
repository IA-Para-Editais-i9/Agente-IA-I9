import streamlit as st

st.set_page_config(
    page_title="Análise de Editais",
    layout="wide"
)

st.title("📊 Plataforma de Análise de Fit para Editais")

st.markdown("""
Bem-vindo!

Esta ferramenta analisa editais e compara com os documentos da sua empresa,
indicando o nível de aderência (fit).

### 🚀 Como usar:
1. Vá para a aba **Upload**
2. Envie o edital e documentos
3. Clique em **Analisar**
4. Veja o resultado na aba **Resultado**
""")