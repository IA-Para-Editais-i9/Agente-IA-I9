# Monitoramento com Langfuse

## O que é

[Langfuse](https://langfuse.com/) é uma plataforma de observabilidade
para aplicações LLM. Cada chamada feita pelos agentes 1 (extração) e 2
(inferência) deve ser registrada lá, com:

- Prompt enviado
- Resposta recebida
- Modelo usado (ex: `llama-3.1-8b-instant`)
- Tokens consumidos (input/output)
- Latência da chamada
- Metadados (squad, edital, sessão, etc.)

O Squad E é dono do cliente em `src/monitoring/`. Os Squads B e C
**chamam** os helpers desse módulo a partir dos filtros do pipeline.

## Setup rápido (cloud — recomendado para dev)

1. Crie uma conta gratuita em <https://cloud.langfuse.com>
2. Crie um projeto (ex: `agente-editais-dev`)
3. Em "Settings → API Keys", copie `PUBLIC_KEY` e `SECRET_KEY`
4. No `.env` do projeto, preencha:

   ```env
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

5. `pip install -r requirements.txt` e pronto

## Setup self-hosted (Docker Compose)

Quando precisar rodar sem expor dados pra serviço externo (ex: editais
sigilosos), suba o Langfuse localmente:

```powershell
docker compose --profile monitoring up -d
```

Esse comando sobe dois serviços:

- `langfuse-db` (Postgres 15 com volume persistente)
- `langfuse` (UI + API na porta `3000`)

Acesse <http://localhost:3000>, crie a conta inicial, depois um projeto,
gere as chaves e cole no `.env`:

```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000
```

Para parar: `docker compose --profile monitoring down`
Para apagar dados: `docker compose --profile monitoring down -v`

> Sem o flag `--profile monitoring`, esses containers **não sobem**.
> O `docker-compose.yml` foi pensado para que o ambiente de monitoramento
> seja opcional.

## Como usar no código

### Decorator (caso simples)

```python
from src.monitoring import trace_llm_call

@trace_llm_call(name="agente_extracao", model="llama-3.1-8b-instant")
def extrair_criterios(prompt: str):
    response = groq_client.chat.completions.create(...)
    return response
```

O decorator captura prompt (primeiro argumento ou kwarg `prompt`),
response (valor de retorno), latência (medida com `time.perf_counter`)
e tenta extrair tokens automaticamente de objetos com `.usage`
(formato OpenAI-compatible).

### Helper manual (controle total)

```python
from src.monitoring import log_llm_call

log_llm_call(
    name="agente_inferencia",
    prompt=prompt_final,
    response=resposta_modelo,
    model="llama-3.1-8b-instant",
    tokens_input=320,
    tokens_output=180,
    latency_ms=842.5,
    metadata={"edital_id": "FINEP-2026-001"},
)
```

### Flush ao final da sessão

```python
from src.monitoring import flush_langfuse

# No fim do pipeline (ou em finally do FastAPI):
flush_langfuse()
```

## Variáveis de ambiente

| Variável               | Obrigatória | Descrição                                |
|------------------------|-------------|------------------------------------------|
| `LANGFUSE_PUBLIC_KEY`  | Sim*        | Public key do projeto Langfuse           |
| `LANGFUSE_SECRET_KEY`  | Sim*        | Secret key do projeto Langfuse           |
| `LANGFUSE_HOST`        | Sim*        | URL do servidor (cloud ou self-hosted)   |

\* Se qualquer uma estiver faltando ou vazia, o cliente cai num
`NoOpLangfuseClient` automaticamente — o pipeline continua funcionando
sem monitoramento, sem nenhum erro.

## Comportamento sem configuração (NoOp fallback)

Se você rodar o pipeline sem `LANGFUSE_*` no `.env`:

- O `get_langfuse_client()` retorna um `NoOpLangfuseClient`
- Todas as chamadas (`trace`, `generation`, `score`, `flush`) viram no-op
- Aparece **um único log INFO** no início indicando que o monitoramento
  está desligado
- O `@trace_llm_call` e `log_llm_call` continuam sendo chamados, mas não
  enviam nada — útil pra rodar testes/CI sem precisar de keys

## Troubleshooting

| Sintoma                                          | Causa provável                              | Solução |
|--------------------------------------------------|---------------------------------------------|---------|
| Vejo `Langfuse desligado: variaveis...`          | `.env` não tem as 3 chaves preenchidas      | Preencher `LANGFUSE_*` ou aceitar o NoOp |
| Vejo `Pacote langfuse nao instalado`             | `pip install` não foi rodado                | `pip install -r requirements.txt` |
| Vejo `Falha ao inicializar Langfuse (...)`       | Host inacessível ou chaves inválidas        | Conferir `LANGFUSE_HOST`, testar `curl <host>/api/public/health` |
| Container `langfuse` não sobe                    | Porta 3000 ocupada                          | Mudar mapeamento em `docker-compose.yml` (`"3001:3000"`) |
| Traces não aparecem na UI                        | Falta `flush_langfuse()` antes do exit      | Chamar `flush_langfuse()` em `finally` ou ao fim do pipeline |
