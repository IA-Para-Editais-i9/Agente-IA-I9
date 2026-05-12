import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

st.title("📈 Dashboard Executivo")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Análises Realizadas", 128)

with col2:
    st.metric("Média de Fit", "74%")

with col3:
    st.metric("Alto Fit", "63")

with col4:
    st.metric("Gaps Críticos", "17")

st.divider()


dados = pd.DataFrame({
    "Mês": ["Jan", "Fev", "Mar", "Abr", "Mai"],
    "Fit Médio": [62, 70, 74, 81, 78]
})

st.subheader("📊 Evolução do Fit Médio")

st.line_chart(
    dados.set_index("Mês")
)

st.divider()

st.subheader("📌 Principais Gaps Encontrados")

gaps = pd.DataFrame({
    "Gap": [
        "ISO 27001",
        "Capacidade Financeira",
        "Equipe Técnica",
        "LGPD"
    ],
    "Quantidade": [15, 11, 8, 6]
})

st.bar_chart(
    gaps.set_index("Gap")
)