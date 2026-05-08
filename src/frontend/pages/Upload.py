import streamlit as st
import requests

st.title("📄 Upload de Edital")

api_url = st.secrets["FASTAPI_URL"]

edital = st.file_uploader("Upload do PDF do Edital", type=["pdf"])
docs_empresa = st.file_uploader(
    "Upload de documentos da empresa (opcional)",
    accept_multiple_files=True
)

if st.button("🔍 Analisar"):
    if not edital:
        st.warning("Envie o edital primeiro.")
    else:
        with st.spinner("Analisando..."):
            files = {
                "edital": edital
            }

            if docs_empresa:
                for i, doc in enumerate(docs_empresa):
                    files[f"doc_{i}"] = doc

            response = requests.post(api_url, files=files)

            if response.status_code == 200:
                st.session_state["resultado"] = response.json()
                st.success("Análise concluída!")
                st.switch_page("pages/2_📊_Resultado.py")
            else:
                st.error("Erro ao processar análise.")