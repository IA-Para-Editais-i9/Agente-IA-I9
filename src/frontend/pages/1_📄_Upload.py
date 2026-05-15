import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MAX_SIZE_MB = 100

st.title("📄 Upload de Edital")

st.markdown(
    "Faça upload do edital principal e, opcionalmente, "
    "documentos complementares da empresa."
)

col1, col2 = st.columns(2)

with col1:
    edital_pdf = st.file_uploader(
        "Upload do Edital (PDF)",
        type=["pdf"],
        help=f"PDF do edital que será analisado. Tamanho máximo: {MAX_SIZE_MB} MB.",
    )

with col2:
    docs_empresa = st.file_uploader(
        "Documentos adicionais da empresa (opcional)",
        type=["pdf", "docx", "xlsx"],
        accept_multiple_files=True,
        help="Documentos complementares para enriquecer a base da empresa.",
    )

edital_excedeu_limite = (
    edital_pdf is not None and edital_pdf.size > MAX_SIZE_MB * 1024 * 1024
)

if edital_pdf is not None:
    if edital_excedeu_limite:
        st.error(
            f"O PDF tem {edital_pdf.size / (1024 * 1024):.1f} MB. "
            f"Reduza para no máximo {MAX_SIZE_MB} MB."
        )
    else:
        st.success(
            f"Edital carregado: **{edital_pdf.name}** "
            f"({edital_pdf.size / 1024:.0f} KB)"
        )
        st.session_state["edital_nome"] = edital_pdf.name

if docs_empresa:
    st.info(f"{len(docs_empresa)} documento(s) adicional(is) carregado(s).")
    st.session_state["docs_empresa_nomes"] = [d.name for d in docs_empresa]

st.divider()

if st.button("Analisar", use_container_width=True, type="primary"):
    if edital_pdf is None:
        st.error("Envie o edital em PDF para continuar.")
    elif edital_excedeu_limite:
        st.error("O edital excede o tamanho permitido.")
    else:
        with st.spinner("Processando análise..."):
            try:
                # TODO(D3): substituir pelo endpoint real quando o Squad D entregar.
                response = requests.post(
                    f"{BACKEND_URL}/analisar-edital",
                    files={
                        "file": (
                            edital_pdf.name,
                            edital_pdf.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=180,
                )
                response.raise_for_status()
                resultado = response.json()
            except requests.RequestException as exc:
                st.warning(
                    f"Backend indisponível ({exc}). "
                    "Exibindo resultado mock para preview."
                )
                resultado = {
                    "percentual_fit": 78,
                    "classificacao": "Alto",
                    "criterios_atendidos": [],
                    "gaps_identificados": [],
                    "recomendacoes_adequacao": [],
                    "necessidade_parceria_ict": False,
                    "sugestao_parceiros": [],
                    "justificativa_percentual": "Mock — backend ainda não integrado (D3).",
                    "acoes_prioritarias": [],
                }

        st.session_state["resultado_fit"] = resultado
        st.session_state["analise_concluida"] = True
        st.success(
            "Análise concluída! Acesse o painel de **Resultado** no menu lateral."
        )
