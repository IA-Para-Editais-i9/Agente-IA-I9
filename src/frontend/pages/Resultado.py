import streamlit as st

st.set_page_config(page_title="Resultado", page_icon="📊", layout="wide")

st.title("📊 Resultado da Análise")

fit_percent = 78
classificacao = "ALTO FIT"

criterios_ok = [
    "✅ Certidões fiscais válidas",
    "✅ Capacidade técnica comprovada",
    "✅ Tempo de mercado compatível",
    "✅ Documentação jurídica completa",
]

gaps = [
    "❌ Ausência de ISO 27001",
    "❌ Falta de comprovação financeira",
    "❌ Equipe reduzida para escopo",
]

recomendacoes = [
    "Regularizar documentação financeira",
    "Adicionar certificação ISO",
    "Expandir equipe técnica",
]

top3 = [
    "1️⃣ Enviar balanço patrimonial atualizado",
    "2️⃣ Iniciar processo de certificação ISO",
    "3️⃣ Contratar profissionais especializados",
]

st.subheader("Indicador de Compatibilidade")

st.progress(fit_percent)

if fit_percent >= 75:
    st.success(f"{fit_percent}% — {classificacao}")
elif fit_percent >= 50:
    st.warning(f"{fit_percent}% — MÉDIO FIT")
else:
    st.error(f"{fit_percent}% — BAIXO FIT")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("✅ Critérios Atendidos")

    for item in criterios_ok:
        st.markdown(item)

with col2:
    st.subheader("❌ Gaps Identificados")

    for item in gaps:
        st.markdown(item)

st.divider()

st.subheader("💡 Recomendações")

for rec in recomendacoes:
    st.info(rec)


st.subheader("🚀 Top 3 Ações Prioritárias")

for acao in top3:
    st.warning(acao)