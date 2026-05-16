"""Dados de exemplo para o modo demonstrativo (sem backend) +
health check do backend FastAPI (Squad D).

Tres analises variadas (alto / medio / baixo) que cobrem as 3 faixas do
gauge e populam o historico para uma demo visualmente rica.

Tambem expõe `check_backend_health()` e `render_backend_status_pill()`
para indicar se o backend FastAPI esta online. Mantemos essa logica
aqui (e nao em um modulo separado) por exigencia arquitetural do
CONTRIBUTING.md — Squad E so pode ter os arquivos previstos em
`src/frontend/`.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Literal

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 3 mocks variados (alto / medio / baixo)
# ─────────────────────────────────────────────────────────────────────────────
MOCK_ALTO = {
    "_origem": "demo",
    "edital_titulo": "Edital FINEP Inovação 042/2026",
    "orgao": "FINEP — Financiadora de Estudos e Projetos",
    "resumo_executivo": (
        "O edital busca soluções de IA aplicada a serviços públicos. "
        "A i9+ tem fit excelente: portfólio já contempla 3 projetos similares "
        "com ICTs parceiras e equipe sênior em LLMs."
    ),
    "valor_estimado": "R$ 2.300.000,00",
    "prazo_entrega_proposta": "18/06/2026",
    "classificacao": "Alto",
    "percentual": 85,
    "necessidade_parceria_ict": False,
    "justificativa_percentual": (
        "Aderência técnica forte (40/40), alinhamento temático alto (28/30), "
        "documentação completa (18/20) e histórico relevante em editais "
        "similares (9/10). Soma: 95/100 — ajuste para 85% por margem de risco."
    ),
    "criterios_atendidos": [
        {"criterio": "Experiência comprovada", "evidencia": "Portfólio com 3 projetos de IA aplicada a serviços públicos."},
        {"criterio": "Equipe técnica sênior", "evidencia": "5 desenvolvedores com 7+ anos em IA/ML."},
        {"criterio": "Certificações ISO", "evidencia": "ISO 27001 e ISO 9001 vigentes."},
        {"criterio": "Capacidade financeira", "evidencia": "Balanço 2025 com reservas superiores ao mínimo exigido."},
    ],
    "gaps_identificados": [
        {"gap": "Documento de habilitação técnica", "impacto": "Médio", "detalhe": "Falta versão atualizada do contrato social."},
    ],
    "acoes_prioritarias": [
        {
            "titulo": "Atualizar contrato social",
            "descricao": "Solicitar via cartório com prazo de 5 dias úteis.",
            "prazo_estimado": "5 dias", "esforco": "Baixo",
            "responsavel_sugerido": "Jurídico interno",
        },
        {
            "titulo": "Preparar carta de intenção",
            "descricao": "Modelo já existe — adaptar para o edital.",
            "prazo_estimado": "2 dias", "esforco": "Baixo",
            "responsavel_sugerido": "Diretoria",
        },
        {
            "titulo": "Compilar dossiê técnico",
            "descricao": "Consolidar evidências dos 3 projetos similares anteriores.",
            "prazo_estimado": "7 dias", "esforco": "Médio",
            "responsavel_sugerido": "Equipe técnica",
        },
    ],
    "parceiros_sugeridos": [
        {"nome": "Faculdade Positivo Ecoville", "tipo": "Universidade", "match": 92,
         "motivo": "Já parceiros em projeto anterior de NLP em editais.",
         "contato": "parcerias@up.edu.br"},
    ],
    "recomendacoes": [
        "Submeter dentro da primeira semana — janela de avaliação prioritária.",
        "Incluir cartas de recomendação de clientes públicos no anexo.",
        "Reforçar narrativa de impacto social no resumo da proposta.",
    ],
}

MOCK_MEDIO = {
    "_origem": "demo",
    "edital_titulo": "Chamada EMBRAPII 03/2026",
    "orgao": "EMBRAPII — Empresa Brasileira de Pesquisa e Inovação Industrial",
    "resumo_executivo": (
        "Edital foca em manufatura avançada com IoT. A i9+ atende parcialmente: "
        "tem expertise em IA mas precisa de parceira na frente de hardware "
        "industrial e certificação de manufatura."
    ),
    "valor_estimado": "R$ 1.450.000,00",
    "prazo_entrega_proposta": "30/07/2026",
    "classificacao": "Médio",
    "percentual": 62,
    "necessidade_parceria_ict": True,
    "justificativa_percentual": (
        "Elegibilidade técnica parcial (25/40) por falta de experiência em "
        "hardware industrial. Alinhamento temático moderado (20/30). "
        "Documentação OK (16/20). Sem histórico em editais similares (1/10). "
        "Total: 62/100."
    ),
    "criterios_atendidos": [
        {"criterio": "Expertise em IA/ML", "evidencia": "Equipe com vivência em modelos preditivos."},
        {"criterio": "Capacidade de execução", "evidencia": "Estrutura de projeto madura."},
    ],
    "gaps_identificados": [
        {"gap": "Experiência em hardware industrial", "impacto": "Alto",
         "detalhe": "Edital exige protótipo físico — i9+ é majoritariamente software."},
        {"gap": "Certificação ISO 9001 para manufatura", "impacto": "Médio",
         "detalhe": "Necessária para a fase de prototipagem industrial."},
        {"gap": "Parceria com ICT obrigatória", "impacto": "Alto",
         "detalhe": "Edital exige co-execução com universidade ou instituto."},
    ],
    "acoes_prioritarias": [
        {
            "titulo": "Firmar parceria com ICT",
            "descricao": "Contatar SENAI-PR ou UFPR para co-submissão.",
            "prazo_estimado": "14 dias", "esforco": "Alto",
            "responsavel_sugerido": "Diretoria + Comercial",
        },
        {
            "titulo": "Avaliar consórcio com fabricante",
            "descricao": "Buscar empresa de hardware como subcontratada.",
            "prazo_estimado": "10 dias", "esforco": "Médio",
            "responsavel_sugerido": "BD",
        },
        {
            "titulo": "Iniciar processo de ISO 9001",
            "descricao": "Cronograma agressivo de 60 dias com consultoria.",
            "prazo_estimado": "60 dias", "esforco": "Alto",
            "responsavel_sugerido": "Qualidade",
        },
    ],
    "parceiros_sugeridos": [
        {"nome": "SENAI-PR", "tipo": "ICT", "match": 78,
         "motivo": "Laboratórios de manufatura avançada + experiência em editais.",
         "contato": "inovacao@senaipr.org.br"},
        {"nome": "UFPR", "tipo": "Universidade", "match": 71,
         "motivo": "Grupo de pesquisa em IoT industrial.",
         "contato": "prppg@ufpr.br"},
    ],
    "recomendacoes": [
        "Postergar submissão se a parceria com ICT não fechar em 14 dias.",
        "Considerar atuar como subcontratada de uma empresa de manufatura.",
        "Investir em pipeline próprio de hardware no longo prazo.",
    ],
}

MOCK_BAIXO = {
    "_origem": "demo",
    "edital_titulo": "Edital BNDES Bioeconomia 18/2026",
    "orgao": "BNDES — Banco Nacional de Desenvolvimento Econômico e Social",
    "resumo_executivo": (
        "Edital para empresas com atuação consolidada em bioeconomia, "
        "agricultura de precisão ou energia renovável de biomassa. "
        "A i9+ não tem fit nesse vertical."
    ),
    "valor_estimado": "R$ 4.800.000,00",
    "prazo_entrega_proposta": "12/08/2026",
    "classificacao": "Baixo",
    "percentual": 28,
    "necessidade_parceria_ict": True,
    "justificativa_percentual": (
        "Elegibilidade técnica baixa (8/40) — i9+ não tem produto em "
        "bioeconomia. Alinhamento temático fraco (10/30). Documentação OK "
        "(10/20). Sem histórico (0/10). Total: 28/100. Recomendação: não submeter."
    ),
    "criterios_atendidos": [
        {"criterio": "Estrutura empresarial mínima", "evidencia": "Documentação societária válida."},
    ],
    "gaps_identificados": [
        {"gap": "Atuação em bioeconomia", "impacto": "Alto",
         "detalhe": "Setor totalmente fora do escopo atual da i9+."},
        {"gap": "Experiência em agricultura/biomassa", "impacto": "Alto",
         "detalhe": "Nenhum projeto anterior nesse domínio."},
        {"gap": "Parceria com instituto de pesquisa agrícola", "impacto": "Alto",
         "detalhe": "Obrigatória pelo edital — não há histórico de parceria com EMBRAPA ou similares."},
        {"gap": "Patentes ou propriedade intelectual", "impacto": "Médio",
         "detalhe": "Edital favorece empresas com PI registrada na área."},
    ],
    "acoes_prioritarias": [
        {
            "titulo": "Avaliar pivotagem ou não submeter",
            "descricao": "Discussão estratégica com diretoria — fit muito baixo.",
            "prazo_estimado": "Imediato", "esforco": "Baixo",
            "responsavel_sugerido": "Diretoria",
        },
        {
            "titulo": "Mapear editais alternativos",
            "descricao": "Buscar editais BNDES alinhados ao vertical de IA.",
            "prazo_estimado": "5 dias", "esforco": "Baixo",
            "responsavel_sugerido": "BD",
        },
    ],
    "parceiros_sugeridos": [],
    "recomendacoes": [
        "Não submeter neste ciclo — fit insuficiente.",
        "Considerar este edital apenas se houver pivotagem estratégica formal.",
        "Mapear próximos editais BNDES alinhados a IA aplicada (não bioeconomia).",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _historico_item(mock: dict, dias_atras: int) -> dict:
    """Monta um item do historico no schema usado pela tela Upload."""
    timestamp = datetime.now() - timedelta(days=dias_atras, hours=dias_atras * 3)
    return {
        "timestamp": timestamp.isoformat(timespec="seconds"),
        "edital_nome": f"{mock['edital_titulo']}.pdf",
        "edital_titulo": mock["edital_titulo"],
        "orgao": mock["orgao"],
        "percentual": mock["percentual"],
        "classificacao": mock["classificacao"],
        "resultado_completo": mock,
    }


def seed_demo(state) -> None:
    """Popula `st.session_state` com dados de demo (3 analises variadas).

    Deixa MOCK_ALTO como `resultado_fit` corrente e adiciona as 3 ao
    historico (mais recente primeiro: alto, medio, baixo).
    """
    state["resultado_fit"] = MOCK_ALTO
    state["analise_concluida"] = True
    state["edital_nome"] = f"{MOCK_ALTO['edital_titulo']}.pdf"
    state["docs_empresa_nomes"] = ["portfolio_2025.pdf", "balanco_2025.pdf"]
    state["historico"] = [
        _historico_item(MOCK_ALTO, dias_atras=0),
        _historico_item(MOCK_MEDIO, dias_atras=2),
        _historico_item(MOCK_BAIXO, dias_atras=5),
    ]


def get_mock_alto() -> dict:
    """Acesso direto ao mock de score alto (para uso fora do seed completo)."""
    return MOCK_ALTO


def ativar_modo_demo() -> None:
    """Alias publico que ativa o modo demo no `st.session_state` atual.

    Equivalente a chamar `seed_demo(st.session_state)`. Existe para que
    os botoes 'Modo Demo' tenham um nome de funcao mais intencional
    quando chamados de varios lugares.
    """
    seed_demo(st.session_state)
    st.session_state["modo_demo_ativo"] = True


# ─────────────────────────────────────────────────────────────────────────────
# Health check do backend FastAPI (Squad D)
# Mantemos esta logica dentro de demo_data.py por exigencia arquitetural do
# CONTRIBUTING.md (Squad E so possui os arquivos previstos em src/frontend/).
# ─────────────────────────────────────────────────────────────────────────────
def _backend_url() -> str:
    return os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=30, show_spinner=False)
def check_backend_health(timeout: float = 2.0) -> Literal["online", "offline"]:
    """Retorna 'online' / 'offline'. Cache de 30s para nao re-checar a cada rerun."""
    try:
        response = requests.get(f"{_backend_url()}/health", timeout=timeout)
        return "online" if response.status_code == 200 else "offline"
    except Exception:  # noqa: BLE001 — qualquer falha vira offline
        return "offline"


def render_backend_status_pill() -> None:
    """Renderiza um pill com bolinha verde/amarela na sidebar.

    Online  -> verde, pulsando, "Backend: online"
    Offline -> amarelo, estatico, "Backend: offline (modo demo)"
    """
    status = check_backend_health()
    if status == "online":
        cls = "backend-online"
        label = "Backend: online"
    else:
        cls = "backend-offline"
        label = "Backend: offline (modo demo)"

    st.sidebar.markdown(
        f"""
        <div class="backend-badge {cls}" title="Backend FastAPI · Squad D">
            <span class="badge-dot"></span>
            <span class="badge-label">{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
