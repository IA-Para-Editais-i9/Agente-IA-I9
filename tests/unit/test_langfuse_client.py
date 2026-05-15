"""Testes unitarios do cliente Langfuse (Squad E)."""

from __future__ import annotations

import pytest

from src.monitoring.langfuse_client import (
    NoOpLangfuseClient,
    get_langfuse_client,
    log_llm_call,
    trace_llm_call,
)


@pytest.fixture(autouse=True)
def limpar_cache_e_env(monkeypatch):
    """Garante que cada teste comeca com cache limpo e sem env vars."""
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    get_langfuse_client.cache_clear()
    yield
    get_langfuse_client.cache_clear()


def test_get_langfuse_client_sem_env_retorna_noop():
    cliente = get_langfuse_client()
    assert isinstance(cliente, NoOpLangfuseClient)


def test_get_langfuse_client_com_env_parcial_retorna_noop(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-fake")
    # Faltando SECRET e HOST — deve cair em NoOp
    cliente = get_langfuse_client()
    assert isinstance(cliente, NoOpLangfuseClient)


def test_noop_client_nao_levanta_excecao_em_metodos():
    cliente = NoOpLangfuseClient()
    cliente.trace(name="x")
    cliente.generation(name="x", input="prompt", output="response")
    cliente.span(name="x")
    cliente.score(name="x", value=1.0)
    cliente.update(metadata={})
    cliente.end()
    cliente.flush()


def test_log_llm_call_com_noop_nao_quebra():
    log_llm_call(
        name="agente_teste",
        prompt="qual a capital do brasil?",
        response="brasilia",
        model="llama-3.1-8b-instant",
        tokens_input=10,
        tokens_output=5,
        latency_ms=120.0,
    )


def test_trace_llm_call_preserva_retorno_da_funcao():
    @trace_llm_call(name="funcao_teste", model="llama-3.1-8b-instant")
    def gerar(prompt: str) -> str:
        return f"resposta para: {prompt}"

    resultado = gerar("oi")
    assert resultado == "resposta para: oi"


def test_trace_llm_call_funciona_com_kwarg_prompt():
    @trace_llm_call(name="funcao_teste")
    def gerar(prompt: str) -> dict:
        return {"output": prompt.upper()}

    resultado = gerar(prompt="ola")
    assert resultado == {"output": "OLA"}


def test_trace_llm_call_nao_quebra_se_log_falhar(monkeypatch):
    """Mesmo com log_llm_call quebrando, a funcao decorada retorna normal.

    O wrapper do trace_llm_call envolve a chamada de log num try/except
    pra garantir que falhas de monitoramento NAO derrubem o pipeline.
    """

    def raise_em_log(*_args, **_kwargs):
        raise RuntimeError("simulando falha no langfuse")

    monkeypatch.setattr(
        "src.monitoring.langfuse_client.log_llm_call", raise_em_log
    )

    @trace_llm_call(name="funcao_teste")
    def gerar(prompt: str) -> str:
        return "ok"

    # Comportamento esperado: retorna "ok" mesmo com log quebrando
    resultado = gerar("oi")
    assert resultado == "ok"


def test_get_langfuse_client_e_cacheado():
    primeira = get_langfuse_client()
    segunda = get_langfuse_client()
    assert primeira is segunda
