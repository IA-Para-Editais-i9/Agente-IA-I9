"""Utilitarios do frontend (exportacao, estilo, tema Plotly, demo, backend)."""

from src.frontend.utils.demo_data import (
    ativar_modo_demo,
    check_backend_health,
    get_mock_alto,
    render_backend_status_pill,
    seed_demo,
)
from src.frontend.utils.exportar import gerar_markdown
from src.frontend.utils.plotly_theme import apply_theme
from src.frontend.utils.styles import inject_custom_css, inject_global_ui

__all__ = [
    "apply_theme",
    "ativar_modo_demo",
    "check_backend_health",
    "gerar_markdown",
    "get_mock_alto",
    "inject_custom_css",
    "inject_global_ui",
    "render_backend_status_pill",
    "seed_demo",
]
