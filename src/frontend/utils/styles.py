"""CSS global + UI fixa (botão toggle, badge i9+) do frontend i9+.

Uso recomendado: chamar `inject_global_ui()` no topo de CADA pagina
Streamlit (depois do `st.set_page_config`).
- `inject_custom_css()` continua disponivel para retrocompatibilidade
  e injeta apenas o CSS.
- `inject_global_ui()` injeta CSS + HTML do badge "i9+" no canto direito.

Paleta (em sintonia com .streamlit/config.toml):
- Background primario: #0D1113
- Background secundario: #1A1F24 (cards, containers, sidebar items)
- Accent primary: #E8317E (botoes, gauge, links, badges)
- Accent hover: #FF4A93
- Text primary: #FBF9F9
- Text secondary: #8193A0
- Success: #10B981 / Warning: #F59E0B / Error: #EF4444
"""

import streamlit as st

_CSS = """
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --bg-primary: #0D1113;
        --bg-secondary: #1A1F24;
        --bg-elevated: #232830;
        --accent: #E8317E;
        --accent-deep: #C7166B;
        --accent-hover: #FF4A93;
        --accent-soft: rgba(232, 49, 126, 0.12);
        --accent-glow: rgba(232, 49, 126, 0.30);
        --text-primary: #FBF9F9;
        --text-secondary: #8193A0;
        --text-muted: #5C6873;
        --border: rgba(129, 147, 160, 0.12);
        --border-strong: rgba(129, 147, 160, 0.22);
        --success: #10B981;
        --warning: #F59E0B;
        --error: #EF4444;
        --radius-sm: 10px;
        --radius: 16px;
        --radius-lg: 20px;
        --radius-pill: 999px;
        --ease-out: cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ─────────────────────────────────────────────────────────────────
       LIMPEZA DO CHROME STREAMLIT
       Esconde menu hamburger nativo, footer "Made with Streamlit",
       botao Deploy e indicador "Running". Header fica transparente
       pra dar espaco aos elementos fixos i9+.
       ───────────────────────────────────────────────────────────────── */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }
    .stDeployButton { display: none !important; }
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    header[data-testid="stHeader"] {
        background: transparent !important;
        height: 0 !important;
    }

    /* Scroll suave em toda a aplicacao */
    html { scroll-behavior: smooth; }

    /* ─────────────────────────────────────────────────────────────────
       TYPOGRAPHY + BACKGROUND
       ───────────────────────────────────────────────────────────────── */
    html, body, .stApp, [data-testid="stAppViewContainer"], [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif !important;
        color: var(--text-primary) !important;
    }
    .stApp { background-color: var(--bg-primary); }

    /* Glow rosa sutil (apenas decorativo, sem interferir em fixed UI) */
    .stApp::before {
        content: "";
        position: fixed;
        top: -200px; right: -200px;
        width: 800px; height: 800px;
        background: radial-gradient(circle, var(--accent-soft) 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(40px);
    }
    .stApp::after {
        content: "";
        position: fixed;
        bottom: -300px; left: -200px;
        width: 700px; height: 700px;
        background: radial-gradient(circle, rgba(232, 49, 126, 0.06) 0%, transparent 65%);
        pointer-events: none;
        z-index: 0;
        filter: blur(60px);
    }
    .main .block-container {
        position: relative;
        z-index: 1;
        max-width: 1200px;
        padding-top: 72px !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em !important;
        font-weight: 700 !important;
    }
    h1 { font-size: clamp(2rem, 4vw, 2.8rem) !important; line-height: 1.1 !important; }
    h2 { font-size: clamp(1.6rem, 3vw, 2rem) !important; }
    h3 { font-size: 1.35rem !important; font-weight: 600 !important; }
    p, label, span, li { color: var(--text-secondary); }
    [data-testid="stCaptionContainer"] {
        color: var(--text-secondary) !important;
        font-size: 0.85rem;
    }

    /* ─────────────────────────────────────────────────────────────────
       SIDEBAR — fundo escuro + logo no topo via ::before
       ───────────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--bg-primary) !important;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebarNav"]::before {
        content: "i9+";
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 1.45rem;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, var(--accent), #FF4A93);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 22px 18px 6px;
        margin: 0;
        border-bottom: 1px solid var(--border);
    }
    [data-testid="stSidebarNav"]::after {
        content: "Pipeline de Análise";
        display: block;
        font-size: 0.65rem;
        letter-spacing: 0.20em;
        text-transform: uppercase;
        color: var(--text-muted);
        font-weight: 600;
        text-align: center;
        margin: 6px 0 14px;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--border);
    }
    [data-testid="stSidebarNav"] span,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] h2 {
        color: var(--text-secondary) !important;
        font-weight: 500;
    }
    [data-testid="stSidebarNav"] a {
        border-radius: 12px;
        margin: 2px 8px;
        padding: 4px 10px !important;
        transition: all 0.22s var(--ease-out);
    }
    [data-testid="stSidebarNav"] a:hover { background: var(--accent-soft); }
    [data-testid="stSidebarNav"] a:hover span,
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: var(--accent) !important;
        font-weight: 600;
    }
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: var(--accent-soft);
        border-left: 2px solid var(--accent);
    }

    /* ─────────────────────────────────────────────────────────────────
       BOTÃO TOGGLE DA SIDEBAR — ALTA ESPECIFICIDADE + FALLBACKS
       Streamlit muda o data-testid entre versoes; cobrimos os 3 mais
       comuns. Botao sempre fixed top-left, rosa circular, alto z-index.
       ───────────────────────────────────────────────────────────────── */
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 12px !important;
        left: 12px !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%) !important;
        border: none !important;
        border-radius: 50% !important;
        width: 44px !important;
        height: 44px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 4px 14px rgba(232, 49, 126, 0.40),
                    0 0 0 1px rgba(255, 255, 255, 0.08) inset !important;
        cursor: pointer !important;
        opacity: 1 !important;
        visibility: visible !important;
        transition: transform 200ms var(--ease-out),
                    box-shadow 200ms var(--ease-out) !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover,
    [data-testid="collapsedControl"]:hover {
        transform: scale(1.08) !important;
        box-shadow: 0 6px 20px rgba(232, 49, 126, 0.55),
                    0 0 0 1px rgba(255, 255, 255, 0.12) inset !important;
    }
    [data-testid="stSidebarCollapsedControl"]:active,
    [data-testid="collapsedControl"]:active {
        transform: scale(0.96) !important;
    }
    [data-testid="stSidebarCollapsedControl"]:focus-visible,
    [data-testid="collapsedControl"]:focus-visible {
        outline: 3px solid var(--accent) !important;
        outline-offset: 3px !important;
    }
    /* Container interno (alguns builds embrulham em um button) */
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="collapsedControl"] button {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        height: 100% !important;
        min-height: unset !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    /* Icone */
    [data-testid="stSidebarCollapsedControl"] svg,
    [data-testid="collapsedControl"] svg {
        fill: white !important;
        color: white !important;
        width: 22px !important;
        height: 22px !important;
        transition: transform 300ms var(--ease-out) !important;
    }
    [data-testid="stSidebarCollapsedControl"]:hover svg,
    [data-testid="collapsedControl"]:hover svg {
        transform: translateX(2px);
    }

    /* Botao FECHAR (sidebar aberta) — discreto, dentro da sidebar */
    [data-testid="stSidebarCollapseButton"] {
        background: rgba(232, 49, 126, 0.15) !important;
        border: 1px solid var(--border) !important;
        border-radius: 50% !important;
        padding: 6px !important;
        transition: all 200ms var(--ease-out) !important;
    }
    [data-testid="stSidebarCollapseButton"]:hover {
        background: rgba(232, 49, 126, 0.30) !important;
        border-color: var(--accent) !important;
    }
    [data-testid="stSidebarCollapseButton"] svg {
        color: var(--accent) !important;
        fill: var(--accent) !important;
    }

    /* ─────────────────────────────────────────────────────────────────
       BADGE i9+ NO CANTO SUPERIOR DIREITO
       Renderizado como HTML real (mais flexivel que pseudo-element).
       ───────────────────────────────────────────────────────────────── */
    .i9-brand-badge {
        position: fixed;
        top: 12px;
        right: 16px;
        z-index: 999998;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 16px;
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-deep) 100%);
        border-radius: var(--radius-pill);
        box-shadow: 0 4px 14px rgba(232, 49, 126, 0.35),
                    0 0 0 1px rgba(255, 255, 255, 0.08) inset;
        color: white;
        font-family: 'Inter', sans-serif;
        cursor: default;
        transition: transform 250ms var(--ease-out),
                    box-shadow 250ms var(--ease-out);
        user-select: none;
    }
    .i9-brand-badge:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 22px rgba(232, 49, 126, 0.50),
                    0 0 0 1px rgba(255, 255, 255, 0.12) inset;
    }
    .i9-brand-text {
        font-size: 0.95rem;
        font-weight: 800;
        letter-spacing: -0.01em;
        line-height: 1;
    }
    .i9-brand-plus {
        color: #FFE4F0;
        margin-left: 1px;
    }
    .i9-brand-version {
        font-size: 0.62rem;
        font-weight: 700;
        background: rgba(255, 255, 255, 0.18);
        padding: 2px 8px;
        border-radius: var(--radius-pill);
        letter-spacing: 0.16em;
        text-transform: uppercase;
        line-height: 1.2;
    }

    /* ─────────────────────────────────────────────────────────────────
       BUTTONS — primarios rosa, secundarios borda
       ───────────────────────────────────────────────────────────────── */
    .stButton > button, .stDownloadButton > button {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-pill);
        padding: 10px 28px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 250ms var(--ease-out);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--accent);
        color: var(--accent);
        background: var(--accent-soft);
        transform: translateY(-1px);
    }
    .stButton > button:active, .stDownloadButton > button:active {
        transform: translateY(0);
    }
    .stButton > button:focus-visible {
        outline: 2px solid var(--accent) !important;
        outline-offset: 4px !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--accent) !important;
        color: var(--text-primary) !important;
        border: none !important;
        box-shadow: 0 4px 16px var(--accent-glow);
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--accent-hover) !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 28px var(--accent-glow);
    }

    /* ─────────────────────────────────────────────────────────────────
       FILE UPLOADER
       ───────────────────────────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: var(--bg-secondary);
        border: 2px dashed rgba(232, 49, 126, 0.40);
        border-radius: var(--radius);
        padding: 24px;
        transition: all 250ms var(--ease-out);
    }
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent);
        box-shadow: 0 0 0 4px var(--accent-soft);
    }
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: none !important;
        padding: 16px;
    }
    [data-testid="stFileUploadDropzone"] small,
    [data-testid="stFileUploadDropzone"] span,
    [data-testid="stFileUploadDropzone"] div {
        color: var(--text-secondary) !important;
    }
    [data-testid="stFileUploadDropzone"] button {
        background: var(--accent) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: var(--radius-pill) !important;
        font-weight: 600 !important;
    }

    /* ─────────────────────────────────────────────────────────────────
       CONTAINERS, TABS, METRICS, ALERTS, INPUTS, PROGRESS
       ───────────────────────────────────────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 24px !important;
        transition: border-color 250ms var(--ease-out);
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--border-strong) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 0.92rem;
        padding: 12px 18px;
        border: none;
        border-bottom: 2px solid transparent;
        border-radius: 0;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-primary); }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--accent) !important;
        border-bottom: 2px solid var(--accent) !important;
    }

    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 22px;
        transition: all 250ms var(--ease-out);
    }
    [data-testid="stMetric"]:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
    }
    [data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--accent) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }

    .stAlert {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox > div[data-baseweb="select"] {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-primary) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-soft) !important;
    }
    [data-testid="stCheckbox"] label p { color: var(--text-secondary) !important; }
    [data-testid="stCheckbox"] [data-baseweb="checkbox"] { accent-color: var(--accent); }
    [data-testid="stProgress"] > div > div > div {
        background: var(--accent) !important;
    }
    [data-testid="stDataFrame"] {
        background: var(--bg-secondary) !important;
        border-radius: var(--radius) !important;
        border: 1px solid var(--border) !important;
    }
    hr { border-color: var(--border) !important; }

    /* ─────────────────────────────────────────────────────────────────
       HELPERS visuais
       ───────────────────────────────────────────────────────────────── */
    .eyebrow {
        font-size: 11px;
        letter-spacing: 0.24em;
        text-transform: uppercase;
        color: var(--accent);
        font-weight: 600;
        margin-bottom: 12px;
    }
    .accent-bar {
        height: 3px;
        width: 60px;
        background: var(--accent);
        border-radius: 2px;
        margin: 14px 0 24px;
    }
    .pill-soft {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: var(--radius-pill);
        background: var(--accent-soft);
        color: var(--accent);
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }

    /* ─────────────────────────────────────────────────────────────────
       RESULTADO — Criterios/Gaps, Acoes, Recomendacoes, Parceiros
       ───────────────────────────────────────────────────────────────── */
    .criterio-coluna-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 12px 16px;
        border-radius: var(--radius-sm);
        margin-bottom: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.82rem;
        border: 1px solid var(--border);
    }
    .criterio-header-atendido {
        background: rgba(16, 185, 129, 0.08);
        border-color: rgba(16, 185, 129, 0.25);
        color: var(--success);
    }
    .criterio-header-gap {
        background: rgba(239, 68, 68, 0.08);
        border-color: rgba(239, 68, 68, 0.25);
        color: var(--error);
    }
    .criterio-coluna-titulo { font-size: 0.9rem; }
    .criterio-counter {
        background: rgba(255,255,255,0.06);
        padding: 2px 12px;
        border-radius: var(--radius-pill);
        font-size: 0.85rem;
        font-weight: 700;
        color: inherit;
    }
    .criterio-card-atendido, .criterio-card-gap {
        padding: 14px 18px;
        border-radius: var(--radius-sm);
        margin-bottom: 10px;
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        transition: transform 200ms var(--ease-out), border-color 200ms var(--ease-out);
    }
    .criterio-card-atendido { border-left: 3px solid var(--success); }
    .criterio-card-gap { border-left: 3px solid var(--error); }
    .criterio-card-atendido:hover { transform: translateX(3px); border-color: rgba(16, 185, 129, 0.40); }
    .criterio-card-gap:hover { transform: translateX(3px); border-color: rgba(239, 68, 68, 0.40); }
    .criterio-titulo {
        font-weight: 600; color: var(--text-primary); margin-bottom: 4px;
        display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    }
    .criterio-descricao { font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; }
    .criterio-impacto-badge {
        background: rgba(239, 68, 68, 0.14);
        color: var(--error);
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: var(--radius-pill);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-left: 6px;
        border: 1px solid rgba(239, 68, 68, 0.30);
    }
    .acao-section-header {
        margin-top: 28px; margin-bottom: 14px;
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border);
        padding-bottom: 10px;
        text-transform: uppercase;
        letter-spacing: 0.10em;
    }
    .acao-card-prioritaria {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-top: 2px solid var(--accent);
        color: var(--text-primary);
        padding: 22px;
        border-radius: var(--radius);
        margin-bottom: 12px;
        min-height: 200px;
        transition: all 250ms var(--ease-out);
    }
    .acao-card-prioritaria:hover {
        transform: translateY(-3px);
        border-color: var(--accent);
        box-shadow: 0 8px 24px var(--accent-glow);
    }
    .acao-numero-badge {
        display: inline-block;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1;
        color: var(--accent);
        background: var(--accent-soft);
        border: 1px solid rgba(232, 49, 126, 0.25);
        border-radius: var(--radius-sm);
        padding: 6px 16px;
        margin-bottom: 12px;
    }
    .acao-titulo {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 8px; margin-bottom: 8px;
        line-height: 1.3;
        color: var(--text-primary);
        letter-spacing: -0.01em;
    }
    .acao-descricao { font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 10px; }
    .acao-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .acao-tag {
        background: rgba(255, 255, 255, 0.05);
        color: var(--text-secondary);
        padding: 3px 10px;
        border-radius: var(--radius-pill);
        font-size: 0.72rem;
        font-weight: 500;
        white-space: nowrap;
        border: 1px solid var(--border);
        letter-spacing: 0.04em;
    }
    .recomendacao-card {
        border-left: 3px solid var(--accent);
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        padding: 13px 16px;
        border-radius: var(--radius-sm);
        margin-bottom: 8px;
        transition: transform 200ms var(--ease-out), border-color 200ms var(--ease-out);
    }
    .recomendacao-card:hover { transform: translateX(3px); border-color: var(--accent); }
    .recomendacao-titulo { font-weight: 600; color: var(--accent); margin-bottom: 4px; }
    .recomendacao-descricao { font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; }
    .parceiro-card {
        border: 1px solid var(--border);
        background: var(--bg-secondary);
        padding: 16px 20px;
        border-radius: var(--radius-sm);
        margin-bottom: 10px;
        transition: all 220ms var(--ease-out);
    }
    .parceiro-card:hover { border-color: var(--accent); transform: translateY(-2px); }
    .parceiro-header { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
    .parceiro-nome { font-weight: 600; color: var(--text-primary); font-size: 1.02rem; letter-spacing: -0.01em; }
    .parceiro-tipo-badge {
        color: white;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: var(--radius-pill);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .parceiro-match {
        background: rgba(16, 185, 129, 0.10);
        color: var(--success);
        font-size: 0.7rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: var(--radius-pill);
        border: 1px solid rgba(16, 185, 129, 0.28);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .parceiro-motivo { font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5; margin-top: 4px; }
    .parceiro-contato { font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; }

    /* ─────────────────────────────────────────────────────────────────
       BANNER DE STATUS DO BACKEND (mock/demo) — amarelo suave
       Aparece no topo do Resultado quando _origem != "backend".
       Tom informativo, NAO alarmante (nao usar vermelho aqui).
       ───────────────────────────────────────────────────────────────── */
    .backend-status-banner {
        display: flex;
        gap: 16px;
        align-items: flex-start;
        background: linear-gradient(135deg,
            rgba(241, 196, 15, 0.14) 0%,
            rgba(243, 156, 18, 0.08) 100%);
        border-left: 4px solid #f1c40f;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0 24px;
        box-shadow: 0 2px 10px rgba(241, 196, 15, 0.10);
    }
    .banner-icon {
        font-size: 28px;
        line-height: 1;
        flex-shrink: 0;
    }
    .banner-content strong {
        color: #f39c12 !important;
        font-size: 1.02rem;
        display: block;
        margin-bottom: 4px;
        font-weight: 700;
    }
    .banner-content p {
        margin: 0;
        color: var(--text-secondary);
        font-size: 0.9rem;
        line-height: 1.55;
    }

    /* ─────────────────────────────────────────────────────────────────
       INDICADOR DE STATUS DO BACKEND NA SIDEBAR
       (.backend-badge .badge-dot .badge-label)
       ───────────────────────────────────────────────────────────────── */
    .backend-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        margin: 6px 8px 14px;
        border-radius: var(--radius-pill);
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid var(--border);
    }
    .backend-badge.backend-online {
        background: rgba(39, 174, 96, 0.12);
        color: #27ae60;
        border-color: rgba(39, 174, 96, 0.30);
    }
    .backend-badge.backend-offline {
        background: rgba(241, 196, 15, 0.12);
        color: #f39c12;
        border-color: rgba(241, 196, 15, 0.30);
    }
    .backend-badge .badge-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .backend-online .badge-dot {
        background: #27ae60;
        box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.18);
        animation: backend-pulse 2.4s ease-in-out infinite;
    }
    .backend-offline .badge-dot {
        background: #f39c12;
        box-shadow: 0 0 0 3px rgba(241, 196, 15, 0.18);
    }
    @keyframes backend-pulse {
        0%, 100% { box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.18); }
        50%      { box-shadow: 0 0 0 6px rgba(39, 174, 96, 0.06); }
    }

    .step-badge {
        background: var(--accent);
        color: var(--text-primary);
        padding: 4px 12px;
        border-radius: var(--radius-pill);
        font-size: 0.74rem;
        font-weight: 700;
        margin-right: 10px;
        letter-spacing: 0.04em;
    }
    .step-title {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.01em;
    }

    /* ─────────────────────────────────────────────────────────────────
       RESPONSIVIDADE
       Mobile-first: ajustamos elementos fixos e padding em telas menores
       ───────────────────────────────────────────────────────────────── */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 64px !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            width: 38px !important;
            height: 38px !important;
            top: 10px !important;
            left: 10px !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg {
            width: 18px !important;
            height: 18px !important;
        }
        .i9-brand-badge {
            padding: 6px 12px;
            top: 10px;
            right: 10px;
            gap: 6px;
        }
        .i9-brand-version { display: none; }
        [data-testid="stSidebarNav"]::before {
            font-size: 1.2rem;
            padding: 16px 14px 4px;
        }
        [data-testid="stSidebarNav"]::after {
            font-size: 0.58rem;
        }
    }
    @media (max-width: 480px) {
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="collapsedControl"] {
            width: 34px !important;
            height: 34px !important;
        }
        [data-testid="stSidebarCollapsedControl"] svg,
        [data-testid="collapsedControl"] svg {
            width: 16px !important;
            height: 16px !important;
        }
        .i9-brand-text { font-size: 0.85rem; }
    }
</style>
"""

_BADGE_HTML = """
<div class="i9-brand-badge" role="banner" aria-label="i9+ Pipeline">
    <span class="i9-brand-text">i9<span class="i9-brand-plus">+</span></span>
    <span class="i9-brand-version">BETA</span>
</div>
"""


def inject_custom_css() -> None:
    """Injeta apenas o CSS global. Mantido para retrocompatibilidade."""
    st.markdown(_CSS, unsafe_allow_html=True)


def inject_global_ui() -> None:
    """Injeta CSS global + badge i9+ fixo no canto superior direito.

    Chame essa funcao no topo de CADA pagina Streamlit (depois do
    `st.set_page_config`) para garantir consistencia.
    """
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown(_BADGE_HTML, unsafe_allow_html=True)
