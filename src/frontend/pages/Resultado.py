import streamlit as st

st.title("📊 Resultado da Análise")

resultado = st.session_state.get("resultado")

if not resultado:
    st.warning("Nenhuma análise encontrada.")
    st.stop()

fit = resultado.get("fit_percentual", 0)
classificacao = resultado.get("classificacao", "N/A")
justificativa = resultado.get("justificativa", "")

criterios_ok = resultado.get("criterios_atendidos", [])
gaps = resultado.get("gaps", [])

recomendacoes = resultado.get("recomendacoes", [])
top3 = resultado.get("top_3_acoes", [])
parceiros = resultado.get("parceiros", [])

st.subheader("📈 Nível de Fit")

st.progress(fit / 100)

col1, col2 = st.columns(2)
col1.metric("Fit (%)", f"{fit}%")
col2.metric("Classificação", classificacao)

st.markdown(f"**Justificativa:** {justificativa}")

st.subheader("📌 Critérios e Gaps")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✅ Critérios Atendidos")
    for c in criterios_ok:
        st.success(c)

with col2:
    st.markdown("### ❌ Gaps Identificados")
    for g in gaps:
        st.error(g)


st.subheader("🚀 Recomendações")

st.markdown("### 📋 Lista Geral")
for r in recomendacoes:
    st.write(f"- {r}")

st.markdown("### 🔥 Top 3 Ações Prioritárias")
for t in top3:
    st.warning(t)

if parceiros:
    st.markdown("### 🤝 Parceiros Sugeridos")
    for p in parceiros:
        st.info(p)