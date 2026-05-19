"""
Teste de carga para validar o rate limiter.

Dispara N requisições contra /analyze/ em paralelo e mede:
- Quantas retornaram 200, 429, ou outros
- Tempo de resposta de cada uma
- Distribuição de delays aplicados

Como rodar (com a API rodando em outro terminal via uvicorn):
    python -m scripts.load_test_rate_limit
"""

import time
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

URL = "http://127.0.0.1:8000/analyze/"
PAYLOAD = {"text": "teste de carga"}
TOTAL_REQUESTS = 150  # quantas requisições disparar
CONCURRENCY = 10  # quantas em paralelo


def single_request(i: int) -> dict:
    """Faz uma requisição e retorna métricas dela."""
    start = time.perf_counter()
    try:
        resp = httpx.post(URL, json=PAYLOAD, timeout=30.0)
        elapsed = time.perf_counter() - start
        body = (
            resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        return {
            "index": i,
            "status": resp.status_code,
            "elapsed_s": round(elapsed, 3),
            "delay_applied": body.get("delay_applied_seconds"),
            "remaining": resp.headers.get("x-ratelimit-remaining"),
        }
    except Exception as exc:
        return {"index": i, "status": "error", "error": str(exc)}


def main() -> None:
    print(f"Disparando {TOTAL_REQUESTS} requisições com concorrência {CONCURRENCY}...")
    start = time.perf_counter()
    results = []

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(single_request, i) for i in range(TOTAL_REQUESTS)]
        for future in as_completed(futures):
            results.append(future.result())

    total_time = time.perf_counter() - start

    # Estatísticas
    status_counts = Counter(r["status"] for r in results)
    success = [r for r in results if r["status"] == 200]
    delays = Counter(r.get("delay_applied") for r in success)
    elapsed_values = [r["elapsed_s"] for r in success]

    print("\n" + "=" * 50)
    print("RESULTADO DO TESTE DE CARGA")
    print("=" * 50)
    print(f"Total de requisições:    {TOTAL_REQUESTS}")
    print(f"Concorrência:            {CONCURRENCY}")
    print(f"Tempo total:             {total_time:.2f}s")
    print(f"Taxa média:              {TOTAL_REQUESTS / total_time:.1f} req/s")
    print()
    print("Status code distribution:")
    for status, count in sorted(status_counts.items(), key=lambda x: str(x[0])):
        print(f"  {status}: {count}")
    print()
    print("Delays aplicados (nas respostas 200):")
    for delay, count in sorted(delays.items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {delay}s: {count}")
    print()
    if elapsed_values:
        print("Tempo de resposta (apenas 200):")
        print(f"  min:    {min(elapsed_values):.3f}s")
        print(f"  max:    {max(elapsed_values):.3f}s")
        print(f"  média:  {sum(elapsed_values) / len(elapsed_values):.3f}s")

    # Salva resultados completos em JSON pra análise posterior
    with open("scripts/load_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nDetalhes salvos em scripts/load_test_results.json")


if __name__ == "__main__":
    main()
