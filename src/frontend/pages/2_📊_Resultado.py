import re
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Resultado — i9+",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.frontend.utils.exportar import gerar_markdown  # noqa: E402
from src.frontend.utils.plotly_theme import apply_theme  # noqa: E402
from src.frontend.utils.demo_data import render_backend_status_pill  # noqa: E402
from src.frontend.utils.styles import inject_global_ui  # noqa: E402

inject_global_ui()
render_backend_status_pill()
apply_theme()



# ─────────────────────────────────────────────────────────────────────────────
# Acesso ao session_state
# ─────────────────────────────────────────────────────────────────────────────
def get_resultado():
    """Le o resultado da analise persistido pela tela de Upload (E1)."""
    return st.session_state.get("resultado_fit")


# ─────────────────────────────────────────────────────────────────────────────
# Gauge plotly — percentual de fit com cores por faixa
# ─────────────────────────────────────────────────────────────────────────────
def cor_por_percentual(percentual):
    """Paleta semantica para o gauge."""
    if percentual >= 70:
        return "#10B981"  # success — Alto
    if percentual >= 40:
        return "#F59E0B"  # warning — Medio
    return "#EF4444"      # error — Baixo/Inviavel


def render_gauge(percentual):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percentual,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Score de Fit", "font": {"size": 20, "color": "#FBF9F9"}},
            number={"suffix": "%", "font": {"color": "#E8317E", "size": 48}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": "#8193A0",
                    "tickfont": {"color": "#8193A0", "size": 11},
                },
                "bar": {"color": "#E8317E", "thickness": 0.30},
                "bgcolor": "#1A1F24",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,68,68,0.15)"},
                    {"range": [40, 70], "color": "rgba(245,158,11,0.15)"},
                    {"range": [70, 100], "color": "rgba(16,185,129,0.15)"},
                ],
            },
        )
    )
    fig.update_layout(
        height=350,
        margin=dict(t=60, b=20, l=20, r=20),
        paper_bgcolor="#0D1113",
        plot_bgcolor="#1A1F24",
        font={"color": "#FBF9F9", "family": "Inter, sans-serif"},
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# Classificacao em destaque + metric cards
# ─────────────────────────────────────────────────────────────────────────────
CLASSIFICACAO_CORES = {
    "Alto": "#10B981",
    "Médio": "#F59E0B",
    "Medio": "#F59E0B",
    "Baixo": "#EF4444",
    "Inviável": "#EF4444",
    "Inviavel": "#EF4444",
}


def render_classificacao(classificacao):
    cor = CLASSIFICACAO_CORES.get(classificacao, "#E8317E")
    st.markdown(
        f"""
        <div style="background:#1A1F24;
                    padding:28px 24px;
                    border:1px solid rgba(129, 147, 160, 0.12);
                    border-top:2px solid {cor};
                    border-radius:16px;
                    text-align:center; color:#FBF9F9;
                    margin-bottom:8px;
                    transition: border-color 0.25s ease;">
            <div style="font-size:0.72rem; font-weight:600;
                        text-transform:uppercase; letter-spacing:0.24em;
                        color:{cor};
                        margin-bottom:14px;">
                · Classificação ·
            </div>
            <div style="font-family:'Inter',sans-serif;
                        font-size:2.8rem; font-weight:700;
                        color:{cor};
                        letter-spacing:-0.02em;
                        line-height: 1;">
                {classificacao.upper()}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards(resultado):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Classificação", resultado.get("classificacao", "—"))
    with col2:
        st.metric("Valor estimado", resultado.get("valor_estimado", "—"))
    with col3:
        st.metric("Prazo entrega proposta", resultado.get("prazo_entrega_proposta", "—"))


# ─────────────────────────────────────────────────────────────────────────────
# Justificativa do percentual
# ─────────────────────────────────────────────────────────────────────────────
def render_justificativa(resultado):
    texto = resultado.get(
        "justificativa_percentual",
        resultado.get("resumo_executivo", ""),
    )
    if not texto:
        return
    st.subheader("Justificativa do percentual")
    st.markdown(
        f"""
        <div style="background:#1A1F24;
                    border:1px solid rgba(129, 147, 160, 0.12);
                    border-left:3px solid #E8317E;
                    padding:22px 26px; border-radius:16px;
                    color:#8193A0; line-height:1.65; font-size:0.98rem;
                    margin-top:8px;">
            {texto}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper: renderiza lista de criterios ou gaps em cards visuais
# ─────────────────────────────────────────────────────────────────────────────
def render_lista_criterios(lista, tipo):
    """Renderiza lista de criterios ou gaps em cards visuais.

    Aceita itens como string ou dict (com chaves 'criterio'/'gap',
    'evidencia'/'detalhe' e opcionalmente 'impacto').

    Args:
        lista: list[str] ou list[dict]
        tipo: "atendido" (verde) ou "gap" (vermelho)
    """
    if not lista:
        msg = (
            "Nenhum criterio atendido identificado."
            if tipo == "atendido"
            else "Nenhum gap identificado."
        )
        st.info(msg)
        return

    card_class = "criterio-card-atendido" if tipo == "atendido" else "criterio-card-gap"
    icone = "✅" if tipo == "atendido" else "❌"

    for item in lista:
        if isinstance(item, str):
            titulo = item
            descricao = ""
            impacto = ""
        elif isinstance(item, dict):
            titulo = item.get("criterio") or item.get("gap") or item.get("titulo") or ""
            descricao = (
                item.get("evidencia") or item.get("detalhe") or item.get("descricao") or ""
            )
            impacto = item.get("impacto", "") if tipo == "gap" else ""
        else:
            titulo = str(item)
            descricao = ""
            impacto = ""

        badge_impacto = (
            f'<span class="criterio-impacto-badge">Impacto: {impacto}</span>'
            if impacto
            else ""
        )
        descricao_html = (
            f'<div class="criterio-descricao">{descricao}</div>' if descricao else ""
        )

        st.markdown(
            f"""
            <div class="{card_class}">
                <div class="criterio-titulo">{icone} {titulo}{badge_impacto}</div>
                {descricao_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Helper: renderiza um card de acao prioritaria com numero em destaque
# ─────────────────────────────────────────────────────────────────────────────
def render_acao_prioritaria(acao, numero):
    """Renderiza card de acao prioritaria com numero grande em destaque.

    Aceita acao como string ou dict com chaves 'titulo', 'descricao',
    'prazo_estimado'/'prazo', 'esforco' e 'responsavel_sugerido'.

    Args:
        acao: str ou dict
        numero: 1, 2 ou 3 (posicao no top 3)
    """
    if isinstance(acao, str):
        titulo = acao
        descricao = ""
        prazo = ""
        esforco = ""
        responsavel = ""
    elif isinstance(acao, dict):
        titulo = acao.get("titulo") or acao.get("acao") or ""
        descricao = acao.get("descricao") or acao.get("detalhe") or ""
        prazo = acao.get("prazo_estimado") or acao.get("prazo") or ""
        esforco = acao.get("esforco", "")
        responsavel = acao.get("responsavel_sugerido") or acao.get("responsavel") or ""
    else:
        titulo = str(acao)
        descricao = prazo = esforco = responsavel = ""

    tags_html = []
    if prazo:
        tags_html.append(f'<span class="acao-tag">⏱ {prazo}</span>')
    if esforco:
        tags_html.append(f'<span class="acao-tag">⚡ Esforço: {esforco}</span>')
    if responsavel:
        tags_html.append(f'<span class="acao-tag">👤 {responsavel}</span>')
    tags_render = "".join(tags_html)

    descricao_html = (
        f'<div class="acao-descricao">{descricao}</div>' if descricao else ""
    )

    st.markdown(
        f"""
        <div class="acao-card-prioritaria">
            <span class="acao-numero-badge">{numero}</span>
            <div class="acao-titulo">{titulo}</div>
            {descricao_html}
            <div class="acao-tags">{tags_render}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper: renderiza um card de recomendacao
# ─────────────────────────────────────────────────────────────────────────────
def render_recomendacao(rec):
    """Renderiza card de recomendacao. Aceita str ou dict."""
    if isinstance(rec, str):
        titulo = rec
        descricao = ""
    elif isinstance(rec, dict):
        titulo = rec.get("titulo") or rec.get("recomendacao") or ""
        descricao = rec.get("descricao") or rec.get("detalhe") or ""
    else:
        titulo = str(rec)
        descricao = ""

    descricao_html = (
        f'<div class="recomendacao-descricao">{descricao}</div>' if descricao else ""
    )

    st.markdown(
        f"""
        <div class="recomendacao-card">
            <div class="recomendacao-titulo">💡 {titulo}</div>
            {descricao_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Helper: renderiza um card de parceiro sugerido
# ─────────────────────────────────────────────────────────────────────────────
PARCEIRO_TIPO_CORES = {
    "ICT": "#0055FF",
    "Universidade": "#27ae60",
    "Instituto": "#f39c12",
    "Empresa": "#9b59b6",
}


def render_parceiro(parceiro):
    """Renderiza card horizontal de parceiro sugerido. Aceita str ou dict.

    Dict suporta chaves: nome, tipo, motivo/justificativa, match, contato.
    """
    if isinstance(parceiro, str):
        nome = parceiro
        tipo = ""
        motivo = ""
        match = None
        contato = ""
    elif isinstance(parceiro, dict):
        nome = parceiro.get("nome") or parceiro.get("parceiro") or ""
        tipo = parceiro.get("tipo", "")
        motivo = parceiro.get("motivo") or parceiro.get("justificativa") or ""
        match = parceiro.get("match")
        contato = parceiro.get("contato", "")
    else:
        nome = str(parceiro)
        tipo = motivo = contato = ""
        match = None

    tipo_html = ""
    if tipo:
        cor = PARCEIRO_TIPO_CORES.get(tipo, "#475569")
        tipo_html = (
            f'<span class="parceiro-tipo-badge" style="background:{cor};">{tipo}</span>'
        )

    match_html = (
        f'<span class="parceiro-match">Match {match}%</span>' if match is not None else ""
    )
    motivo_html = (
        f'<div class="parceiro-motivo">{motivo}</div>' if motivo else ""
    )
    contato_html = (
        f'<div class="parceiro-contato">📧 {contato}</div>' if contato else ""
    )

    st.markdown(
        f"""
        <div class="parceiro-card">
            <div class="parceiro-header">
                <span class="parceiro-nome">🤝 {nome}</span>
                {tipo_html}
                {match_html}
            </div>
            {motivo_html}
            {contato_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tabs — esqueleto para incremento de E3 e E4
# ─────────────────────────────────────────────────────────────────────────────
def render_tabs_placeholders(resultado):
    tab_geral, tab_criterios, tab_acoes = st.tabs(
        ["📋 Visão Geral", "✓ Critérios", "🎯 Ações e Recomendações"]
    )

    with tab_geral:
        st.markdown("##### Resumo do diagnostico")
        n_criterios = len(resultado.get("criterios_atendidos", []))
        n_gaps = len(resultado.get("gaps_identificados", []))
        n_acoes = len(resultado.get("acoes_prioritarias", []))
        st.write(
            f"Foram identificados **{n_criterios}** criterios atendidos, "
            f"**{n_gaps}** gaps e **{n_acoes}** acoes prioritarias. "
            "Use as abas ao lado para o detalhamento completo."
        )

    with tab_criterios:
        # ─────────────────────────────────────────────────────────────────
        # [E3] Tab: Criterios e Gaps — implementado
        # Consome: resultado["criterios_atendidos"] e resultado["gaps_identificados"]
        # ─────────────────────────────────────────────────────────────────
        st.markdown(
            "##### Diagnostico detalhado\n"
            "Comparativo entre o que a empresa **atende** no edital e os **gaps** "
            "que precisam ser endereçados antes da submissao."
        )

        criterios = resultado.get("criterios_atendidos", [])
        gaps = resultado.get("gaps_identificados", [])

        col_atendidos, col_gaps = st.columns(2)

        with col_atendidos:
            st.markdown(
                f"""
                <div class="criterio-coluna-header criterio-header-atendido">
                    <span class="criterio-coluna-titulo">✅ Criterios Atendidos</span>
                    <span class="criterio-counter">{len(criterios)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_lista_criterios(criterios, "atendido")

        with col_gaps:
            st.markdown(
                f"""
                <div class="criterio-coluna-header criterio-header-gap">
                    <span class="criterio-coluna-titulo">❌ Gaps Identificados</span>
                    <span class="criterio-counter">{len(gaps)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            render_lista_criterios(gaps, "gap")

    with tab_acoes:
        # ─────────────────────────────────────────────────────────────────
        # [E4] Tab: Acoes e Recomendacoes — implementado
        # Consome: resultado["acoes_prioritarias"], resultado["recomendacoes"],
        #          resultado["parceiros_sugeridos"], resultado["necessidade_parceria_ict"]
        # ─────────────────────────────────────────────────────────────────
        st.markdown(
            "##### Plano de acao\n"
            "Acoes priorizadas, recomendacoes de adequacao e parceiros sugeridos "
            "para aumentar o fit do edital."
        )

        acoes = resultado.get("acoes_prioritarias", [])

        st.markdown(
            '<div class="acao-section-header">🎯 Top 3 Acoes Prioritarias</div>',
            unsafe_allow_html=True,
        )

        if not acoes:
            st.info("Nenhuma acao prioritaria identificada.")
        else:
            top3 = acoes[:3]
            cols = st.columns(len(top3))
            for idx, (col, acao) in enumerate(zip(cols, top3), start=1):
                with col:
                    render_acao_prioritaria(acao, idx)

        st.markdown(
            '<div class="acao-section-header">💡 Recomendacoes de Adequacao</div>',
            unsafe_allow_html=True,
        )

        recomendacoes = resultado.get("recomendacoes", [])
        if not recomendacoes:
            st.info("Nenhuma recomendacao adicional para este edital.")
        else:
            for rec in recomendacoes:
                render_recomendacao(rec)

        st.markdown(
            '<div class="acao-section-header">🤝 Parceiros Sugeridos</div>',
            unsafe_allow_html=True,
        )

        parceiros = resultado.get("parceiros_sugeridos", [])
        precisa_ict = resultado.get("necessidade_parceria_ict", False)

        if parceiros:
            for parceiro in parceiros:
                render_parceiro(parceiro)
        elif precisa_ict:
            st.warning(
                "⚠️ Parceria com ICT recomendada — nenhum parceiro especifico sugerido."
            )
        else:
            st.success(
                "✅ Nenhum parceiro adicional necessario para esse edital."
            )


# ─────────────────────────────────────────────────────────────────────────────
# Botoes de navegacao no rodape
# ─────────────────────────────────────────────────────────────────────────────
def _slug(texto: str) -> str:
    """Converte titulo em slug seguro para nome de arquivo."""
    if not texto:
        return "analise"
    base = re.sub(r"[^a-zA-Z0-9_-]+", "_", texto).strip("_").lower()
    return base[:60] or "analise"


def render_navigation(resultado):
    st.divider()
    col_voltar, col_exportar, col_nova = st.columns(3)

    with col_voltar:
        if st.button("← Voltar ao Upload", use_container_width=True):
            st.switch_page("pages/1_📄_Upload.py")

    with col_exportar:
        markdown_relatorio = gerar_markdown(resultado)
        slug = _slug(resultado.get("edital_titulo", ""))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button(
            label="📥 Exportar Relatorio",
            data=markdown_relatorio,
            file_name=f"analise_{slug}_{timestamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col_nova:
        if st.button(
            "🔄 Nova Analise",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["analise_concluida"] = False
            st.session_state["resultado_fit"] = None
            st.switch_page("pages/1_📄_Upload.py")


# ─────────────────────────────────────────────────────────────────────────────
# Empty state — quando o usuario acessa direto sem ter feito upload
# ─────────────────────────────────────────────────────────────────────────────
def render_empty_state():
    st.warning(
        "Nenhuma analise disponivel. Faca o upload de um edital "
        "na pagina **Upload** antes de visualizar o resultado."
    )
    if st.button("Ir para Upload", type="primary", use_container_width=True):
        st.switch_page("pages/1_📄_Upload.py")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
def render_header(resultado):
    titulo = resultado.get("edital_titulo", "Edital sem titulo")
    orgao = resultado.get("orgao", "Orgao nao informado")
    st.title("Diagnostico de Viabilidade")
    st.markdown('<div class="accent-bar"></div>', unsafe_allow_html=True)
    st.caption(f"{titulo} — {orgao}")


# ─────────────────────────────────────────────────────────────────────────────
# Banner informativo: aparece quando o resultado NAO vem do backend real
# (origem == "mock" ou "demo"). Backend == "backend" nao mostra nada.
# ─────────────────────────────────────────────────────────────────────────────
def render_backend_status_banner(resultado):
    origem = (resultado or {}).get("_origem", "backend")
    if origem not in ("mock", "demo"):
        return

    msg_origem = "exemplo (Modo Demo)" if origem == "demo" else "fallback offline"
    icone = "✨" if origem == "demo" else "🔧"

    st.markdown(
        f"""
        <div class="backend-status-banner">
            <div class="banner-icon">{icone}</div>
            <div class="banner-content">
                <strong>Dados de {msg_origem}</strong>
                <p>O backend de análise IA (Squad D — FastAPI) ainda está em
                desenvolvimento. Quando estiver pronto, os resultados refletirão
                a análise real do seu edital. Por enquanto, você está
                visualizando dados de demonstração para validar a interface.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    resultado = get_resultado()
    if not resultado:
        render_empty_state()
    render_header(resultado)
    render_backend_status_banner(resultado)
    render_metric_cards(resultado)
    col_gauge, col_class = st.columns([1.4, 1])
    with col_gauge:
        render_gauge(resultado.get("percentual", 0))
    with col_class:
        render_classificacao(resultado.get("classificacao", "—"))
    render_justificativa(resultado)
    render_tabs_placeholders(resultado)
    render_navigation(resultado)


main()
