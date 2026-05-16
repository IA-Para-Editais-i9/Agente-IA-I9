"""Utilitarios do frontend (exportacao, estilo, tema Plotly, demo, backend).

Sem re-exports neste __init__ para evitar carregamento transitivo de
streamlit/plotly em ambientes que rodam apenas testes unitarios da camada
de exportacao (ex.: CI sem dependencias de UI instaladas).

Importe sempre o submodulo direto:
    from src.frontend.utils.exportar import gerar_markdown
    from src.frontend.utils.demo_data import seed_demo
"""
