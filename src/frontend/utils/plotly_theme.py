"""Template Plotly customizado coerente com o tema dark + rosa do frontend."""

import plotly.graph_objects as go
import plotly.io as pio

TEMPLATE_NAME = "editais_dark"

pio.templates[TEMPLATE_NAME] = go.layout.Template(
    layout=dict(
        paper_bgcolor="#0D1113",
        plot_bgcolor="#1A1F24",
        font=dict(family="Inter, sans-serif", color="#FBF9F9", size=13),
        colorway=["#E8317E", "#8193A0", "#10B981", "#F59E0B", "#FF4A93"],
        xaxis=dict(
            gridcolor="rgba(129,147,160,0.15)",
            zerolinecolor="rgba(129,147,160,0.20)",
            linecolor="rgba(129,147,160,0.20)",
            tickfont=dict(color="#8193A0"),
        ),
        yaxis=dict(
            gridcolor="rgba(129,147,160,0.15)",
            zerolinecolor="rgba(129,147,160,0.20)",
            linecolor="rgba(129,147,160,0.20)",
            tickfont=dict(color="#8193A0"),
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(129,147,160,0.20)",
            font=dict(color="#8193A0"),
        ),
    )
)


def apply_theme() -> None:
    """Define o template editais_dark como padrao global do Plotly."""
    pio.templates.default = TEMPLATE_NAME
