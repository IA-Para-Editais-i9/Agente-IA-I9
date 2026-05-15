import plotly.graph_objects as go
import streamlit as st


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
    if percentual >= 80:
        return "#27ae60"  # verde — Alto
    if percentual >= 60:
        return "#f1c40f"  # amarelo — Medio
    if percentual >= 40:
        return "#f39c12"  # laranja — Baixo
    return "#e74c3c"      # vermelho — Inviavel


def render_gauge(percentual):
    cor = cor_por_percentual(percentual)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=percentual,
            number={"suffix": "%", "font": {"size": 48, "color": cor}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": cor},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 40], "color": "#fde2e2"},
                    {"range": [40, 60], "color": "#fdecd2"},
                    {"range": [60, 80], "color": "#fdf6c2"},
                    {"range": [80, 100], "color": "#d6f3df"},
                ],
            },
        )
    )
    fig.update_layout(height=320, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)


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
    st.caption(f"{titulo} — {orgao}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
def main():
    resultado = get_resultado()
    if not resultado:
        render_empty_state()
    render_header(resultado)
    render_gauge(resultado.get("percentual", 0))


main()
