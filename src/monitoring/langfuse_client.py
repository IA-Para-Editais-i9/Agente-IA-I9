"""Cliente Langfuse para monitoramento de chamadas LLM.

Comportamento:
- Se `langfuse` nao estiver instalado OU faltar alguma das variaveis de
  ambiente (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST),
  o cliente cai num NoOpLangfuseClient que tem a mesma interface mas
  nao envia nada para fora.
- Falhas no inicializador ou em chamadas internas viram `warning` no
  logging — nunca propagam excecao para o pipeline principal.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class NoOpLangfuseClient:
    """Cliente que implementa a interface do Langfuse sem efeito.

    Usado quando o monitoramento esta desligado (sem env vars) ou quando
    o pacote `langfuse` nao esta instalado. Garante que o codigo que usa
    `client.generation(...)`, `client.trace(...)`, `client.score(...)` e
    `client.flush()` continue funcionando sem `if cliente is None: ...`.
    """

    name = "noop"

    def trace(self, *_args: Any, **_kwargs: Any) -> "NoOpLangfuseClient":
        return self

    def generation(self, *_args: Any, **_kwargs: Any) -> "NoOpLangfuseClient":
        return self

    def span(self, *_args: Any, **_kwargs: Any) -> "NoOpLangfuseClient":
        return self

    def score(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def update(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def end(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def flush(self) -> None:
        return None


def _env(name: str) -> str | None:
    valor = os.getenv(name)
    return valor.strip() if valor else None


@lru_cache(maxsize=1)
def get_langfuse_client() -> Any:
    """Retorna o cliente Langfuse configurado ou um NoOpLangfuseClient.

    O resultado e cacheado: a mesma instancia e usada durante todo o ciclo
    de vida do processo. Para resetar (em testes), chame
    `get_langfuse_client.cache_clear()`.
    """
    public_key = _env("LANGFUSE_PUBLIC_KEY")
    secret_key = _env("LANGFUSE_SECRET_KEY")
    host = _env("LANGFUSE_HOST")

    if not (public_key and secret_key and host):
        logger.info(
            "Langfuse desligado: variaveis de ambiente nao configuradas. "
            "Usando NoOpLangfuseClient."
        )
        return NoOpLangfuseClient()

    try:
        from langfuse import Langfuse  # type: ignore
    except ImportError:
        logger.warning(
            "Pacote `langfuse` nao instalado. Rode `pip install langfuse` "
            "ou aceite o NoOpLangfuseClient."
        )
        return NoOpLangfuseClient()

    try:
        return Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
    except Exception as exc:  # noqa: BLE001 — qualquer falha cai em NoOp
        logger.warning(
            "Falha ao inicializar Langfuse (%s). Usando NoOpLangfuseClient.",
            exc,
        )
        return NoOpLangfuseClient()


def flush_langfuse() -> None:
    """Garante que traces pendentes sejam enviados antes de encerrar."""
    try:
        get_langfuse_client().flush()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao dar flush no Langfuse: %s", exc)


def log_llm_call(
    name: str,
    prompt: Any,
    response: Any,
    model: str | None = None,
    tokens_input: int | None = None,
    tokens_output: int | None = None,
    latency_ms: float | None = None,
    metadata: dict | None = None,
) -> None:
    """Registra uma chamada LLM no Langfuse.

    Toda falha vira `warning` no logging — nunca propaga excecao para
    nao quebrar o pipeline principal.
    """
    try:
        client = get_langfuse_client()
        usage = {}
        if tokens_input is not None:
            usage["input"] = tokens_input
        if tokens_output is not None:
            usage["output"] = tokens_output

        client.generation(
            name=name,
            model=model,
            input=prompt,
            output=response,
            usage=usage or None,
            metadata={
                **(metadata or {}),
                "latency_ms": latency_ms,
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao registrar chamada LLM '%s': %s", name, exc)


def _extract_tokens(response: Any) -> tuple[int | None, int | None]:
    """Tenta extrair input/output tokens de objetos comuns de SDKs LLM.

    Suporta atributos `usage.prompt_tokens` / `usage.completion_tokens`
    (OpenAI-like) e dicts com chaves similares. Devolve `(None, None)`
    quando nao conseguir identificar.
    """
    if response is None:
        return None, None

    usage = getattr(response, "usage", None)
    if usage is None and isinstance(response, dict):
        usage = response.get("usage")

    if usage is None:
        return None, None

    def _get(obj: Any, *chaves: str) -> int | None:
        for chave in chaves:
            valor = getattr(obj, chave, None)
            if valor is None and isinstance(obj, dict):
                valor = obj.get(chave)
            if isinstance(valor, int):
                return valor
        return None

    tokens_input = _get(usage, "prompt_tokens", "input_tokens", "input")
    tokens_output = _get(usage, "completion_tokens", "output_tokens", "output")
    return tokens_input, tokens_output


def trace_llm_call(name: str, model: str | None = None):
    """Decorator que registra automaticamente a chamada de uma funcao LLM.

    A funcao decorada deve receber o `prompt` como primeiro argumento
    posicional ou como kwarg `prompt`. O valor de retorno e registrado
    como `response`.

    Uso:
        @trace_llm_call(name="agente_extracao", model="llama-3.1-8b-instant")
        def extrair_criterios(prompt: str) -> dict:
            ...
    """
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            prompt = kwargs.get("prompt")
            if prompt is None and args:
                prompt = args[0]

            inicio = time.perf_counter()
            response = func(*args, **kwargs)
            latency_ms = (time.perf_counter() - inicio) * 1000

            try:
                tokens_input, tokens_output = _extract_tokens(response)
                log_llm_call(
                    name=name,
                    prompt=prompt,
                    response=response,
                    model=model,
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    latency_ms=latency_ms,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Falha no trace_llm_call('%s'): %s. "
                    "Pipeline continua normalmente.",
                    name,
                    exc,
                )
            return response

        return wrapper

    return decorator
