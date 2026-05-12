import streamlit as st
import time

st.set_page_config(page_title="Upload", page_icon="📄", layout="wide")

st.title("📄 Upload de Edital")

st.markdown("Faça upload do edital principal e documentos adicionais da empresa.")

col1, col2 = st.columns(2)

with col1:
    edital_pdf = st.file_uploader(
        "Upload do Edital (PDF)",
        type=["pdf"]
    )

with col2:
    docs_empresa = st.file_uploader(
        "Documentos adicionais da empresa",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True
    )

st.divider()

if st.button("🔍 Analisar", use_container_width=True):

    if edital_pdf is None:
        st.error("Envie o edital em PDF para continuar.")
    else:
        progress = st.progress(0)
        status = st.empty()

        for i in range(101):
            time.sleep(0.02)
            progress.progress(i)
            status.text(f"Processando análise... {i}%")

        st.success("Análise concluída com sucesso!")

        st.switch_page("src\frontend\pages\Resultado.py")