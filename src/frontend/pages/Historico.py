import streamlit as st
import pandas as pd

st.set_page_config(page_title="Histórico", page_icon="📁", layout="wide")

st.title("📁 Histórico de Análises")

dados = {
    "Empresa": [
        "Tech Solutions",
        "DataCorp",
        "VisionAI",
        "SmartGov"
    ],
    "Edital": [
        "Edital TI 2026",
        "Segurança Cloud",
        "IA Pública",
        "Infraestrutura"
    ],
    "Fit (%)": [
        78,
        62,
        91,
        48
    ],
    "Classificação": [
        "ALTO FIT",
        "MÉDIO FIT",
        "ALTO FIT",
        "BAIXO FIT"
    ]
}

df = pd.DataFrame(dados)

st.dataframe(
    df,
    use_container_width=True
)

st.divider()

st.subheader("📈 Estatísticas")

media_fit = df["Fit (%)"].mean()

st.metric(
    label="Média Geral de Fit",
    value=f"{media_fit:.1f}%"
)

st.bar_chart(df.set_index("Empresa")["Fit (%)"])