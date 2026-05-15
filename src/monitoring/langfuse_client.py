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
