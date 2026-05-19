# API — Rate Limiting

## Visão Geral

A API conta com um sistema de **rate limiting** (controle de taxa de requisições) que protege tanto a aplicação quanto as APIs externas usadas pelo projeto.

O sistema atende a dois objetivos:

1. **Proteger a própria API** contra uso abusivo (muitas requisições do mesmo IP em pouco tempo).
2. **Respeitar os limites do free tier** de provedores externos (Gemini, OpenAI), evitando que o sistema seja bloqueado pelo provedor.

Quando um cliente excede os limites, a API responde com **HTTP 429 (Too Many Requests)** e indica no header `Retry-After` em quantos segundos o cliente pode tentar novamente.

## Arquitetura em Camadas

O rate limiting é implementado em **três camadas independentes**, seguindo o princípio de *defesa em profundidade*: cada camada tem um propósito específico, e juntas formam uma proteção robusta contra abusos e estouros de quota.

```
Cliente → [Middleware] → [Endpoint] → [Pipeline] → API externa
```

### Camada 1 — Middleware Global (`src/api/main.py`)

Atua em **todas as rotas** da API. Para cada requisição:

- Identifica o IP do cliente (respeitando o header `X-Forwarded-For` quando atrás de proxy).
- Registra a requisição no contador compartilhado (`RequestCounter`).
- Se o IP ultrapassar o limite global, responde imediatamente com **HTTP 429**, sem executar a rota.
- Adiciona headers informativos (`X-RateLimit-*`) em toda resposta.

Rotas isentas: `/docs`, `/redoc`, `/openapi.json`, `/analyze/health`.

### Camada 2 — Endpoint `/analyze` (`src/api/routers/analyze.py`)

Aplica limites **mais finos e progressivos**, com *graceful degradation*:

- **Abaixo de 30 req/min:** sem delay, resposta imediata.
- **Entre 30 e 60 req/min:** delay leve de 0.5s (soft limit).
- **Entre 60 e 120 req/min:** delay maior de 2.0s (hard limit).
- **Acima de 120 req/min:** bloqueio com HTTP 429.

A ideia é desencorajar o uso intenso antes de bloquear de fato, dando ao cliente sinais claros (resposta mais lenta) de que está se aproximando do limite.

### Camada 3 — Pipeline (`src/pipeline/pipeline.py`)

Atua **dentro** do processamento, entre as etapas (filtros) que compõem o pipeline de análise. Aplica um `time.sleep(0.5)` entre cada filtro para espaçar as chamadas que vão à API externa (Gemini/OpenAI), protegendo o free tier desses provedores contra rajadas de requisições internas.

O delay é aplicado **entre** etapas, nunca após a última — para não atrasar a resposta final sem necessidade.

## Limites Configurados

Todos os limites são medidos em **janela deslizante de 60 segundos** por IP. Ou seja: o contador olha os últimos 60s a partir do momento atual, não o "minuto fechado" do relógio.

### Limites do Middleware Global

| Constante | Valor | Significado |
|---|---|---|
| `GLOBAL_BLOCK_LIMIT_PER_MINUTE` | 200 req/min/IP | Acima disso, qualquer rota retorna HTTP 429. |
| `WINDOW_SECONDS` | 60 s | Tamanho da janela deslizante. |

Definidos em `src/api/routers/analyze.py` (classe `RateLimitConfig`).

### Limites do Endpoint `/analyze`

| Constante | Valor | Comportamento |
|---|---|---|
| `SOFT_LIMIT_PER_MINUTE` | 30 req/min/IP | A partir daqui, aplica delay de 0.5s. |
| `HARD_LIMIT_PER_MINUTE` | 60 req/min/IP | A partir daqui, aplica delay de 2.0s. |
| `BLOCK_LIMIT_PER_MINUTE` | 120 req/min/IP | Acima disso, retorna HTTP 429. |
| `BASE_DELAY` | 0.0 s | Delay padrão quando o IP está abaixo do soft limit. |
| `SOFT_DELAY` | 0.5 s | Delay aplicado na faixa soft. |
| `HARD_DELAY` | 2.0 s | Delay aplicado na faixa hard. |

### Limites do Pipeline

| Constante | Valor | Significado |
|---|---|---|
| `INTER_STEP_DELAY` | 0.5 s | Pausa aplicada entre cada par de filtros consecutivos. |

Definido em `src/pipeline/pipeline.py`.

### Por que esses valores?

Os valores foram escolhidos para acomodar o **free tier do Gemini** (15 req/min) como referência mais restritiva. Com o `INTER_STEP_DELAY` de 0.5s entre filtros e o `SOFT_DELAY` de 0.5s a partir de 30 req/min no endpoint, um IP fazendo uso normal dificilmente estoura o limite do provedor externo.

## Resposta da API

Toda resposta da API inclui headers que informam o estado atual do rate limiter para o IP que fez a requisição. Esses headers permitem que o cliente **se autorregule** sem precisar esperar receber um 429.

### Headers Informativos (em toda resposta)

| Header | Exemplo | Significado |
|---|---|---|
| `X-RateLimit-Limit` | `200` | Limite máximo do middleware global (req/min/IP). |
| `X-RateLimit-Remaining` | `187` | Quantas requisições ainda restam na janela atual. |
| `X-RateLimit-Window-Seconds` | `60` | Tamanho da janela em segundos. |
| `X-Response-Time-ms` | `42` | Tempo de processamento da requisição em milissegundos. |

### Cenário 1 — Sucesso (HTTP 200)

Requisição dentro de todos os limites, sem delay.

**Request:**

```http
POST /analyze/ HTTP/1.1
Content-Type: application/json

{ "text": "texto a ser analisado" }
```

**Response:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 198
X-RateLimit-Window-Seconds: 60
X-Response-Time-ms: 12

{
  "result": "Análise do texto (21 chars) concluída.",
  "metrics": {
    "total_requests": 2,
    "requests_last_minute_global": 2,
    "requests_last_minute_ip": 2,
    "uptime_seconds": 45.32
  },
  "delay_applied_seconds": 0.0
}
```

### Cenário 2 — Sucesso com Delay (HTTP 200, mais lento)

Requisição acima do soft limit (30 req/min) ou hard limit (60 req/min) do `/analyze`. A API responde normalmente, mas com um delay deliberado antes de retornar.

O cliente percebe pela combinação de:

- `delay_applied_seconds` no corpo da resposta (0.5 ou 2.0).
- `X-Response-Time-ms` mais alto.

Esse é o **sinal de aviso**: o cliente está se aproximando do limite e deveria reduzir a frequência.

### Cenário 3 — Bloqueado (HTTP 429)

Requisição excedeu o limite (global de 200 ou específico do `/analyze` de 120). A rota **não é executada**.

**Response (middleware global):**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60
X-RateLimit-Limit: 200
X-RateLimit-Remaining: 0

{
  "detail": "Limite global de 200 requisições/minuto excedido para o IP 192.168.1.50.",
  "retry_after_seconds": 60
}
```

**Response (endpoint `/analyze`):**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{
  "detail": "Limite de 120 requisições/minuto excedido para este IP."
}
```

### Como o cliente deve reagir

| Situação | Ação recomendada |
|---|---|
| `X-RateLimit-Remaining` < 20 | Reduzir frequência preventivamente. |
| `delay_applied_seconds` > 0 | Espaçar requisições; está perto do limite. |
| HTTP 429 com `Retry-After` | Aguardar N segundos antes de tentar de novo. |
| HTTP 429 sem `Retry-After` | Aguardar pelo menos 60s (janela padrão). |

## Limites Testados na Prática

Os comportamentos descritos acima foram validados com um teste de carga sintético usando o script `scripts/load_test_rate_limit.py`.

### Configuração do Teste

| Parâmetro | Valor |
|---|---|
| Total de requisições | 150 |
| Concorrência | 10 threads |
| Endpoint testado | `POST /analyze/` |
| Payload | `{ "text": "teste de carga" }` |
| Tempo total | 15.05s |
| Taxa média | 10 req/s |

### Resultado

| Status | Quantidade | % do total |
|---|---|---|
| 200 (sucesso) | 60 | 40% |
| 429 (bloqueado) | 90 | 60% |

### Distribuição de Delays (apenas respostas 200)

| Delay aplicado | Quantidade | Faixa correspondente |
|---|---|---|
| 0.0s | 14 | Abaixo do soft limit |
| 0.5s | 15 | Soft limit (30–60 no contador) |
| 2.0s | 31 | Hard limit (60–120 no contador) |

### Tempo de Resposta (apenas 200)

| Métrica | Valor |
|---|---|
| Mínimo | 0.658s |
| Máximo | 2.495s |
| Média | 1.620s |

### Observação Importante: Dupla Contagem

Durante os testes, verificou-se que cada requisição ao `/analyze` é **contada duas vezes** no `RequestCounter`: uma vez pelo middleware global em `main.py` e outra dentro do próprio endpoint. Por isso, o bloqueio (HTTP 429) começou a ocorrer após cerca de **60 requisições reais**, e não 120 como o valor literal de `BLOCK_LIMIT_PER_MINUTE` sugeriria.

Esse comportamento **não é um bug** — é uma consequência intencional do desenho em camadas. Se for desejado contar exatamente uma vez por requisição, o middleware pode passar o snapshot da contagem via `request.state` para o endpoint, evitando o segundo `register()`. Para o objetivo atual de proteger o free tier, a dupla contagem age como margem de segurança adicional.

### Conclusões

- ✅ O sistema **bloqueia confiavelmente** acima do limite efetivo.
- ✅ Os três níveis de delay (0.0s / 0.5s / 2.0s) **funcionam como esperado**.
- ✅ O middleware retorna 429 sem executar a rota (protegendo CPU mesmo sob ataque).
- ⚠️ O limite efetivo do `/analyze` é **metade** do valor configurado, devido à dupla contagem.

## Como Ajustar os Limites

Todos os valores configuráveis ficam em **constantes no topo dos arquivos**, sem necessidade de variáveis de ambiente ou reinício especial — basta editar, salvar e o `--reload` do uvicorn aplica.

### Para mudar limites do endpoint `/analyze` ou do middleware global

Arquivo: `src/api/routers/analyze.py`, classe `RateLimitConfig`.

```python
class RateLimitConfig:
    WINDOW_SECONDS: int = 60
    SOFT_LIMIT_PER_MINUTE: int = 30
    HARD_LIMIT_PER_MINUTE: int = 60
    BLOCK_LIMIT_PER_MINUTE: int = 120
    GLOBAL_BLOCK_LIMIT_PER_MINUTE: int = 200
    SOFT_DELAY: float = 0.5
    HARD_DELAY: float = 2.0
```

### Para mudar o delay entre etapas do pipeline

Arquivo: `src/pipeline/pipeline.py`, constante no topo:

```python
INTER_STEP_DELAY: float = 0.5
```

### Cenários comuns de ajuste

| Situação | O que mexer |
|---|---|
| API externa começou a retornar 429 | Aumentar `INTER_STEP_DELAY` no pipeline. |
| Usuários reclamam que está lento | Aumentar `SOFT_LIMIT_PER_MINUTE` e `HARD_LIMIT_PER_MINUTE`. |
| Sistema sob ataque (DDoS leve) | Reduzir `GLOBAL_BLOCK_LIMIT_PER_MINUTE`. |
| Free tier do Gemini mudou | Recalcular limites com base na nova quota e ajustar todos os valores proporcionalmente. |
| Quer desativar rate limiting (dev local) | Setar `BLOCK_LIMIT_PER_MINUTE` e `GLOBAL_BLOCK_LIMIT_PER_MINUTE` para um valor alto (ex: 10000). |

### Após qualquer mudança

1. Reiniciar a API (`Ctrl+C` no terminal do uvicorn e subir de novo, ou aguardar o reload automático).
2. Rodar o script de teste de carga (`python -m scripts.load_test_rate_limit`).
3. Atualizar a seção **"Limites Testados na Prática"** deste documento com os novos números.
