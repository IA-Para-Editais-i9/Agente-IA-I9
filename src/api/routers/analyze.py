"""
Squad Responsável: Squad D — Orquestração & Backend

Responsabilidades (Task D3):
- Criar endpoint `POST /analisar-edital`
- Receber upload de PDF de edital (validação: só PDF, máx 100MB)
- Acionar o pipeline completo (PyMuPDF + Tesseract → ChromaDB → Agente 1 → Agente 2)
- Retornar o JSON final com o `ResultadoFit`

Task D5 — Rate Limiting:
- Adiciona contador de requisições por IP com janela deslizante
- Aplica delay progressivo (soft/hard) antes de bloquear com HTTP 429
- Estrutura compartilhada (RateLimitConfig, counter, get_client_ip) usada também
  pelo middleware global em `src/api/main.py`
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime
from threading import Lock
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/analyze", tags=["analyze"])


class RateLimitConfig:

    WINDOW_SECONDS: int = 60

    SOFT_LIMIT_PER_MINUTE: int = 30
    HARD_LIMIT_PER_MINUTE: int = 60
    BLOCK_LIMIT_PER_MINUTE: int = 120

    BASE_DELAY: float = 0.0
    SOFT_DELAY: float = 0.5
    HARD_DELAY: float = 2.0


class RequestCounter:
    """Mantém contadores globais e por IP usando janela deslizante."""

    def __init__(self, window_seconds: int = 60) -> None:
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._total_requests: int = 0
        self._started_at: float = time.time()

        self._ip_timestamps: dict[str, deque[float]] = defaultdict(deque)

        self._global_timestamps: deque[float] = deque()

    def _purge_old(self, dq: deque[float], now: float) -> None:
        """Remove timestamps fora da janela."""
        cutoff = now - self.window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()

    def register(self, ip: str) -> dict:
        """Registra uma requisição e retorna o estado atual."""
        now = time.time()
        with self._lock:
            self._total_requests += 1

            self._global_timestamps.append(now)
            self._purge_old(self._global_timestamps, now)

            ip_dq = self._ip_timestamps[ip]
            ip_dq.append(now)
            self._purge_old(ip_dq, now)

            return {
                "total_requests": self._total_requests,
                "requests_last_minute_global": len(self._global_timestamps),
                "requests_last_minute_ip": len(ip_dq),
                "uptime_seconds": round(now - self._started_at, 2),
            }

    def snapshot(self) -> dict:
        """Retorna métricas atuais sem registrar nova requisição."""
        now = time.time()
        with self._lock:
            self._purge_old(self._global_timestamps, now)
            active_ips = {}
            for ip, dq in list(self._ip_timestamps.items()):
                self._purge_old(dq, now)
                if dq:
                    active_ips[ip] = len(dq)
                else:
                    del self._ip_timestamps[ip]

            return {
                "total_requests": self._total_requests,
                "requests_last_minute_global": len(self._global_timestamps),
                "active_ips": active_ips,
                "uptime_seconds": round(now - self._started_at, 2),
                "started_at": datetime.fromtimestamp(self._started_at).isoformat(),
            }


counter = RequestCounter(window_seconds=RateLimitConfig.WINDOW_SECONDS)


def compute_delay(requests_in_window: int) -> float:
    """Calcula o delay com base no número de requisições recentes do IP."""
    cfg = RateLimitConfig
    if requests_in_window >= cfg.HARD_LIMIT_PER_MINUTE:
        return cfg.HARD_DELAY
    if requests_in_window >= cfg.SOFT_LIMIT_PER_MINUTE:
        return cfg.SOFT_DELAY
    return cfg.BASE_DELAY


def get_client_ip(request: Request) -> str:
    """Pega o IP real, considerando proxies (X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Texto a ser analisado")
    options: Optional[dict] = Field(default=None, description="Opções extras")


class AnalyzeResponse(BaseModel):
    result: str
    metrics: dict
    delay_applied_seconds: float


@router.post("/", response_model=AnalyzeResponse, status_code=status.HTTP_200_OK)
async def analyze(payload: AnalyzeRequest, request: Request) -> AnalyzeResponse:
    """
    Endpoint placeholder com rate limiting (Task D5).
    A lógica real do /analisar-edital (Task D3) substituirá este placeholder,
    mantendo a estrutura de rate limiting abaixo.
    """
    ip = get_client_ip(request)
    stats = counter.register(ip)

    if stats["requests_last_minute_ip"] > RateLimitConfig.BLOCK_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Limite de {RateLimitConfig.BLOCK_LIMIT_PER_MINUTE} "
                f"requisições/minuto excedido para este IP."
            ),
        )

    delay = compute_delay(stats["requests_last_minute_ip"])
    if delay > 0:
        await asyncio.sleep(delay)

    resultado = f"Análise do texto ({len(payload.text)} chars) concluída."

    return AnalyzeResponse(
        result=resultado,
        metrics=stats,
        delay_applied_seconds=delay,
    )


@router.get("/metrics")
async def metrics() -> dict:
    """Expõe contadores atuais. Útil para dashboards e monitoramento."""
    return counter.snapshot()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
