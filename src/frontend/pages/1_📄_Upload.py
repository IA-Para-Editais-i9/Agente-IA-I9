import os
import time

import requests
import streamlit as st

st.set_page_config(
    page_title="Upload do Edital",
    page_icon="📤",
    layout="centered",
    initial_sidebar_state="expanded",
)

from src.frontend.utils.demo_data import seed_demo
from src.frontend.utils.plotly_theme import apply_theme
from src.frontend.utils.demo_data import render_backend_status_pill
from src.frontend.utils.styles import inject_global_ui

inject_global_ui()
render_backend_status_pill()
apply_theme()


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
MAX_SIZE_MB = 100

DEFAULT_STATE = {
    "analise_concluida": False,
    "edital_nome": None,
    "docs_empresa_nomes": [],
    "resultado_fit": None,
}
for chave, valor in DEFAULT_STATE.items():
    if chave not in st.session_state:
        st.session_state[chave] = valor

MOCK_RESULTADO = {
    "_origem": "mock",
    "edital_titulo": "Edital de Inovação 001/2026",
    "orgao": "Ministério da Ciência e Tecnologia",
    "resumo_executivo": (
        "O edital busca soluções para otimização de processos públicos. "
        "A empresa possui excelente aderência técnica, mas precisa de "
        "parceiros para infraestrutura em nuvem."
    ),
    "valor_estimado": "R$ 1.500.000,00",
    "prazo_entrega_proposta": "15/06/2026",
    "classificacao": "Alto",
    "percentual": 85,
    "criterios_atendidos": [
        {
            "criterio": "Experiência Comprovada",
            "evidencia": "Portfólio apresenta 3 projetos similares.",
        }
    ],
    "gaps_identificados": [
        {
            "gap": "Servidores em Nuvem",
            "impacto": "Alto",
            "detalhe": "Exige certificação Tier III.",
        }
    ],
    "acoes_prioritarias": [
        {
            "ordem": "1",
            "titulo": "Firmar parceria AWS",
            "descricao": "Buscar parceiro Tier III.",
            "esforco": "Médio",
            "prazo_estimado": "5 dias",
            "responsavel_sugerido": "Diretoria de TI",
        }
    ],
    "parceiros_sugeridos": [
        {
            "nome": "CloudTech",
            "match": 95,
            "motivo": "Especialistas em licitações.",
            "contato": "cont@cloud.com",
        }
    ],
    "recomendacoes": [
        "Ajustar a proposta comercial.",
        "Preparar CNDs.",
    ],
}


def analisar_edital(arquivo_pdf, progresso):
    """Chama o backend (D3) e devolve o ResultadoFit. Fallback mock quando offline.

    Marca o campo `_origem` no dict de retorno:
    - "backend" quando o POST retorna 200
    - "mock"    quando ha falha de rede / erro HTTP / timeout
    """
    try:
        progresso.progress(20, text="Enviando PDF ao backend...")
        response = requests.post(
            f"{BACKEND_URL}/analisar-edital",
            files={
                "file": (
                    arquivo_pdf.name,
                    arquivo_pdf.getvalue(),
                    "application/pdf",
                )
            },
            timeout=180,
        )
        response.raise_for_status()
        progresso.progress(80, text="Processando resposta...")
        resultado = response.json()
        # Marca a origem do resultado para o banner de status no Resultado
        if isinstance(resultado, dict):
            resultado["_origem"] = "backend"
        progresso.progress(100, text="Análise concluída!")
        return resultado, None
    except requests.RequestException as exc:
        for valor, texto in [
            (25, "Lendo PDF (mock)..."),
            (55, "Extraindo critérios..."),
            (85, "Calculando fit..."),
            (100, "Pronto!"),
        ]:
            time.sleep(0.4)
            progresso.progress(valor, text=texto)
        # Copia rasa pra nao mutar o MOCK global; preserva _origem="mock"
        mock = {**MOCK_RESULTADO, "_origem": "mock", "_erro_backend": str(exc)}
        return mock, str(exc)


st.title("Upload de Documentos")
st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
st.markdown(
    "<p style='color: #475569; font-size: 1.15rem; margin-bottom: 30px;'>"
    "Inicie a varredura inteligente do seu edital público e acervos."
    "</p>",
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown(
        '<div class="step-title"><span class="step-badge">1</span> Edital (Obrigatório)</div>'
        '<p style="color:#64748B; margin-top:-5px;">Anexe o arquivo PDF principal da licitação.</p>',
        unsafe_allow_html=True,
    )
    edital_pdf = st.file_uploader(
        "Upload Edital",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed",
        key="edital",
        help=f"PDF do edital que será analisado. Tamanho máximo: {MAX_SIZE_MB} MB.",
    )
    if edital_pdf is not None:
        if edital_pdf.size > MAX_SIZE_MB * 1024 * 1024:
            st.error(
                f"O PDF tem {edital_pdf.size / (1024 * 1024):.1f} MB. "
                f"Reduza para no máximo {MAX_SIZE_MB} MB."
            )
        else:
            st.success(
                f"✅ Edital carregado: **{edital_pdf.name}** "
                f"({edital_pdf.size / 1024:.0f} KB)"
            )

with st.container(border=True):
    st.markdown(
        '<div class="step-title"><span class="step-badge" style="background:#0055FF;">2</span> Acervo (Opcional)</div>'
        '<p style="color:#64748B; margin-top:-5px;">Envie portfólios, atestados e certificações.</p>',
        unsafe_allow_html=True,
    )
    docs_empresa = st.file_uploader(
        "Upload Docs",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key="docs",
        help="Documentos complementares para enriquecer a base da empresa.",
    )
    if docs_empresa:
        st.info(f"{len(docs_empresa)} documento(s) adicional(is) carregado(s).")

edital_excedeu = (
    edital_pdf is not None and edital_pdf.size > MAX_SIZE_MB * 1024 * 1024
)

col_acao, col_demo, col_limpar = st.columns([2, 1.4, 1])
with col_acao:
    analisar = st.button(
        "🚀 Iniciar Análise IA",
        type="primary",
        use_container_width=True,
        disabled=(edital_pdf is None or edital_excedeu),
    )
with col_demo:
    if st.button(
        "✨ Modo Demo",
        use_container_width=True,
        help="Carrega 3 análises de exemplo sem PDF nem backend.",
    ):
        seed_demo(st.session_state)
        st.switch_page("pages/2_📊_Resultado.py")
with col_limpar:
    if st.button("🗑️ Limpar", use_container_width=True):
        st.session_state.clear()
        st.rerun()

if analisar and edital_pdf is not None and not edital_excedeu:
    progresso = st.progress(0, text="Iniciando análise...")
    resultado, erro_backend = analisar_edital(edital_pdf, progresso)

    if erro_backend:
        st.warning(
            f"Backend indisponível ({erro_backend}). "
            "Exibindo resultado mock para preview."
        )

    st.session_state["analise_concluida"] = True
    st.session_state["edital_nome"] = edital_pdf.name
    st.session_state["docs_empresa_nomes"] = (
        [d.name for d in docs_empresa] if docs_empresa else []
    )
    st.session_state["resultado_fit"] = resultado

    from datetime import datetime

    historico = st.session_state.get("historico") or []
    item = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "edital_nome": edital_pdf.name,
        "edital_titulo": resultado.get("edital_titulo") or edital_pdf.name,
        "orgao": resultado.get("orgao", "—"),
        "percentual": resultado.get("percentual", 0),
        "classificacao": resultado.get("classificacao", "—"),
        "resultado_completo": resultado,
    }
    historico.insert(0, item)
    st.session_state["historico"] = historico[:50]

    st.toast("✅ Análise concluída com sucesso!")

if st.session_state.get("analise_concluida"):
    nome = st.session_state.get("edital_nome") or "—"
    qtd_docs = len(st.session_state.get("docs_empresa_nomes") or [])
    st.markdown(
        f"""
        <div class="status-card">
            <h3>✅ Análise pronta</h3>
            <p>Edital: <b>{nome}</b> · Documentos adicionais: <b>{qtd_docs}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "📊 Ver Resultado",
        type="primary",
        use_container_width=True,
        key="ir_resultado",
    ):
        st.switch_page("pages/2_📊_Resultado.py")
