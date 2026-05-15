"""
Squad Responsável: Squad D — Orquestração & Backend

Responsabilidades:
- Ponto de entrada da aplicação FastAPI (Task D3, D4)
- Registrar os routers de `analyze.py` e `index.py`
- Implementar tratamento de erros global e middlewares (ex: limite de free tier) (Task D2, D5)
"""

import logging
import math
import time

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.api.routers import analyze
from src.api.routers.analyze import (
    RateLimitConfig,
    counter,
    get_client_ip,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Agente-IA-I9 API")


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting global por IP, aplicado a todas as rotas."""
    path = request.url.path

    exempt_paths = ("/docs", "/redoc", "/openapi.json", "/analyze/health")
    if path in exempt_paths:
        return await call_next(request)

    ip = get_client_ip(request)
    stats = counter.register(ip)
    requests_in_window = stats["requests_last_minute_ip"]

    # Limite global mais alto que o do /analyze (camada grossa)
    global_limit = 200

    if requests_in_window > global_limit:
        retry_after = RateLimitConfig.WINDOW_SECONDS
        logger.warning(
            "Rate limit global excedido | ip=%s path=%s req=%d limite=%d",
            ip,
            path,
            requests_in_window,
            global_limit,
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": (
                    f"Limite global de {global_limit} requisições/minuto "
                    f"excedido para o IP {ip}."
                ),
                "retry_after_seconds": retry_after,
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(global_limit),
                "X-RateLimit-Remaining": "0",
            },
        )

    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    remaining = max(0, global_limit - requests_in_window)
    response.headers["X-RateLimit-Limit"] = str(global_limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Window-Seconds"] = str(RateLimitConfig.WINDOW_SECONDS)
    response.headers["X-Response-Time-ms"] = str(math.floor(elapsed_ms))

    return response


app.include_router(analyze.router)


@app.get("/")
async def root() -> dict:
    return {
        "service": "Agente-IA-I9",
        "status": "ok",
        "docs": "/docs",
    }
