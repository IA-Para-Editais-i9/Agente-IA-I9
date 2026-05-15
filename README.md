# Guia de Contribuição — Agente de IA para Editais

> **Leitura obrigatória antes de fazer o primeiro commit.**  
> Este documento explica como o repositório está organizado, como os branches funcionam, quais são as regras de Pull Request e como cada squad deve trabalhar. Se você tiver dúvidas após a leitura, mande uma mensagem para o representante do projeto.

## Sumário

- [Guia de Contribuição — Agente de IA para Editais](#guia-de-contribuição--agente-de-ia-para-editais)
  - [Sumário](#sumário)
  - [1. Por que temos essas regras?](#1-por-que-temos-essas-regras)
  - [2. O padrão de arquitetura: Pipe \& Filter](#2-o-padrão-de-arquitetura-pipe--filter)
    - [O contrato central: `PipelineContext`](#o-contrato-central-pipelinecontext)
  - [3. Estrutura de pastas (Filetree)](#3-estrutura-de-pastas-filetree)
    - [Responsabilidade por pasta](#responsabilidade-por-pasta)
  - [4. Arquivos que nunca vão para o git](#4-arquivos-que-nunca-vão-para-o-git)
  - [5. Estratégia de branches](#5-estratégia-de-branches)
    - [Os 4 níveis explicados](#os-4-níveis-explicados)
    - [Convenção de nomes para branches de feature](#convenção-de-nomes-para-branches-de-feature)
  - [6. Regras de proteção por branch](#6-regras-de-proteção-por-branch)
    - [`main` — protegida, nível máximo](#main--protegida-nível-máximo)
    - [`develop` — protegida, nível médio](#develop--protegida-nível-médio)
    - [`squad/*` — semi-protegida](#squad--semi-protegida)
    - [`feat/*`, `fix/*`, `chore/*` — livre](#feat-fix-chore--livre)
    - [Como configurar no GitHub](#como-configurar-no-github)
  - [7. Como abrir um Pull Request](#7-como-abrir-um-pull-request)
    - [O fluxo padrão de uma tarefa](#o-fluxo-padrão-de-uma-tarefa)
    - [Template obrigatório de PR](#template-obrigatório-de-pr)
  - [8. Convenção de commits](#8-convenção-de-commits)
  - [9. CODEOWNERS — quem revisa o quê](#9-codeowners--quem-revisa-o-quê)
    - [Por que `base.py` e `context.py` têm revisão de todos?](#por-que-basepy-e-contextpy-têm-revisão-de-todos)
    - [Como criar os times no GitHub](#como-criar-os-times-no-github)
  - [10. CI — o que roda automaticamente](#10-ci--o-que-roda-automaticamente)
  - [11. Fluxo completo de uma tarefa](#11-fluxo-completo-de-uma-tarefa)
  - [12. Dúvidas frequentes](#12-dúvidas-frequentes)


---

## 1. Por que temos essas regras?

O projeto envolve 5 squads trabalhando em camadas de um pipeline encadeado. Isso significa que uma mudança mal feita no Squad A pode quebrar o trabalho do Squad C sem que ninguém perceba imediatamente.

As regras deste documento existem para três coisas:

- **Isolar o trabalho de cada squad** — você pode desenvolver sem medo de sobrescrever o trabalho de outra pessoa.
- **Garantir que o pipeline nunca quebre em `develop`** — a branch de integração sempre tem código que funciona.
- **Proteger os contratos entre squads** — os arquivos `base.py`, `context.py` e os schemas Pydantic são a "cola" do sistema. Qualquer mudança neles precisa de consenso.

---

## 2. O padrão de arquitetura: Pipe & Filter

O pipeline segue o padrão **Pipe & Filter**. A ideia é simples:

- Cada etapa do processamento é um **filtro** (um arquivo em `src/pipeline/filters/`).
- O **pipe** é o `PipelineContext` — um objeto de dados que é criado uma vez e passado de filtro em filtro.
- Cada filtro recebe o contexto, faz seu trabalho, popula seu campo e devolve o contexto para o próximo.

**Nota:** A conversão inicial PDF → Markdown é feita usando **PyMuPDF + Tesseract** (substituindo o Docling, que não usamos mais).

```
PDF input
   ↓
f01_ingestion.py    → popula: ctx.markdown_text               (PyMuPDF + Tesseract)  (Squad A)
   ↓
f02_indexing.py     → popula: ctx.edital_collection_id        (Squad A)
                      popula: ctx.empresa_collection_id       (Squad A)
   ↓
f03_extraction.py   → popula: ctx.criterios_edital            (Squad B)
   ↓
f04_retrieval.py    → popula: ctx.company_chunks              (Squad C)
   ↓
f05_inference.py    → popula: ctx.resultado_fit               (Squad C)
   ↓
JSON ResultadoFit
```

### O contrato central: `PipelineContext`

O arquivo `src/pipeline/context.py` define todos os campos que existem no pipeline. **Este arquivo é o contrato entre todos os squads.** Se você precisar adicionar um campo novo, isso afeta todos — veja a seção de CODEOWNERS antes de fazer qualquer mudança.

```python
# src/pipeline/context.py
@dataclass
class PipelineContext:
    pdf_path: str = ""              # entrada inicial

    markdown_text: str = ""         # saída do f01
    edital_collection_id: str = ""  # saída do f02 (id da coleção do edital)
    empresa_collection_id: str = "" # saída do f02 (id da coleção empresa/i9+)
    criterios_edital: Optional[dict] = None   # saída do f03
    company_chunks: list[str] = field(default_factory=list)  # saída do f04
    resultado_fit: Optional[dict] = None      # saída do f05
```

PDF input
   ↓
f01_ingestion.py    → popula: ctx.markdown_text          (Squad A)
   ↓
f02_indexing.py     → popula: ctx.chroma_collection_id   (Squad A)
   ↓
f03_extraction.py   → popula: ctx.criterios_edital        (Squad B)
   ↓
f04_retrieval.py    → popula: ctx.company_chunks          (Squad C)
   ↓
f05_inference.py    → popula: ctx.resultado_fit           (Squad C)
   ↓
JSON ResultadoFit
```

### O contrato central: `PipelineContext`

O arquivo `src/pipeline/context.py` define todos os campos que existem no pipeline. **Este arquivo é o contrato entre todos os squads.** Se você precisar adicionar um campo novo, isso afeta todos — veja a seção de CODEOWNERS antes de fazer qualquer mudança.

```python
# src/pipeline/context.py
@dataclass
class PipelineContext:
    pdf_path: str = ""              # entrada inicial

     markdown_text: str = ""         # saída do f01
     edital_collection_id: str = ""  # saída do f02
     empresa_collection_id: str = "" # saída do f02 (docs i9)
     criterios_edital: Optional[dict] = None   # saída do f03
     company_chunks: list[str] = field(default_factory=list)  # saída do f04
     resultado_fit: Optional[dict] = None      # saída do f05
```

---

## 3. Estrutura de pastas (Filetree)

```
Agente-IA-i9/
│
├── .github/
│   ├── CODEOWNERS                        ← define quem revisa cada arquivo
│   ├── pull_request_template.md          ← template obrigatório de PR
│   └── workflows/
│       ├── ci.yml                        ← lint + testes a cada PR
│       └── lint.yml
│
├── chroma_db/                            ← GITIGNORED — gerado automaticamente
│   └── (gerado pelo ChromaDB em disco)
│
├── src/
│   ├── pipeline/
│   │   ├── base.py                       ← interface abstrata Filter  [CORE]
│   │   ├── context.py                    ← PipelineContext, o "pipe"  [CORE]
│   │   ├── pipeline.py                   ← orquestrador (Squad D)
│   │   └── filters/
│   │       ├── f01_ingestion.py          ← Squad A · PDF → Markdown (PyMuPDF)
│   │       ├── f02_indexing.py           ← Squad A · Markdown → ChromaDB
│   │       ├── f03_extraction.py         ← Squad B · Markdown → CriteriosEdital
│   │       ├── f04_retrieval.py          ← Squad C · Query → Company chunks (RAG)
│   │       └── f05_inference.py          ← Squad C · Chunks → ResultadoFit
│   │
│   ├── schemas/                          ← Squad B (contrato B↔C↔D↔E)
│   │   ├── criterios_edital.py           ← Pydantic CriteriosEdital
│   │   └── resultado_fit.py              ← Pydantic ResultadoFit
│   │
│   ├── api/                              ← Squad D
│   │   ├── main.py                       ← FastAPI app
│   │   └── routers/
│   │       ├── analyze.py                ← POST /analisar-edital
│   │       └── index.py                  ← POST /indexar-documento
│   │
│   └── frontend/                         ← Squad E
│       ├── .streamlit/
│       │   ├── config.toml               ← tema, porta, layout (versionado)
│       │   └── secrets.toml              ← GITIGNORED — chaves de API
│       ├── app.py                        ← ponto de entrada do Streamlit (Home)
│       └── pages/
│           ├── 1_📄_Upload.py            ← tela de upload do edital
│           └── 2_📊_Resultado.py         ← painel de fit, gaps, recomendações
│
├── data/
│   ├── empresa/                          ← GITIGNORED — documentos sensíveis da i9+
│   │   ├── portfolio/
│   │   ├── certificacoes/
│   │   └── contratos/
│   └── editais/
│       └── samples/                      ← 5 PDFs reais de teste (não sensíveis)
│
├── tests/
│   ├── unit/
│   │   ├── test_f01_ingestion.py
│   │   ├── test_f02_indexing.py
│   │   ├── test_f03_extraction.py
│   │   ├── test_f04_retrieval.py
│   │   └── test_f05_inference.py
│   └── integration/
│       └── test_pipeline_e2e.py
│
├── docs/
│   ├── planejamento_equipes_i9_v2.md           ← planejamento por squads/cronograma
│
├── .env.example                          ← template das variáveis (sem valores reais)
├── .gitignore
├── docker-compose.yml                    ← Langfuse self-hosted
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Responsabilidade por pasta

| Pasta / Arquivo | Squad responsável | Observação |
|---|---|---|
| `src/pipeline/filters/f01_*`, `f02_*` | A | Ingestão & Memória |
| `src/pipeline/filters/f03_*` | B | Agente Extrator |
| `src/pipeline/filters/f04_*`, `f05_*` | C | Inferência & Fit |
| `src/schemas/` | B | Contrato compartilhado com C, D, E |
| `src/pipeline/pipeline.py`, `src/api/` | D | Orquestração & Backend |
| `src/frontend/`, `src/monitoring/` | E | Frontend & Monitoramento |
| `src/pipeline/base.py`, `src/pipeline/context.py` | **Todos** | Arquivos de contrato central |

---

## 4. Arquivos que nunca vão para o git

O `.gitignore` do projeto bloqueia os itens abaixo. **Nunca tente fazer commit deles.**

Se o git reclamar que um arquivo "não está sendo rastreado", é de propósito — não tente forçar com `git add -f`.

```gitignore
# Segredos — NUNCA no histórico do git
.env
*.env
**/secrets.toml

# ChromaDB (banco local — pode ter gigabytes)
chroma_db/

# Documentos internos da i9+ (sensíveis)
data/empresa/

# Editais reais (PDFs pesados)
data/editais/*.pdf

# Python padrão
__pycache__/
*.pyc
.venv/
dist/
```

> **Atenção redobrada — repositório público:** Como o repo é público, um segredo commitado fica imediatamente visível para qualquer pessoa na internet. Se uma chave de API vazar no histórico, ela precisa ser **revogada imediatamente** no painel do serviço (Groq, Gemini, Langfuse) e o histórico do git precisa ser reescrito com `git filter-branch` ou `BFG Repo-Cleaner`. Isso é trabalhoso, constrangedor e evitável. Use `.env` e `secrets.toml` para todas as credenciais, sempre, sem exceção.

---

## 5. Estratégia de branches

O repositório usa **4 níveis de branch**. Cada nível tem um propósito diferente e regras diferentes.

```
main
└── develop
      ├── squad/A
      │     ├── feat/A-A1-pymupdf-setup
      │     ├── feat/A-A2-ingestion-module
      │     └── fix/A-A1-scanned-pdf-edge-case
      ├── squad/B
      │     ├── feat/B-B1-criterios-schema
      │     └── feat/B-B2-instructor-groq
      ├── squad/C
      ├── squad/D
      └── squad/E
```

### Os 4 níveis explicados

**`main`** — Produção. Código que chegou aqui foi testado, aprovado e funciona. Nunca recebe push direto. Só é atualizado via PR de `develop` ao final de cada sprint.

**`develop`** — Integração contínua. É aqui que o trabalho de todos os squads se une. Deve sempre estar em estado funcional — se `develop` está quebrado, é problema de todos. Só recebe PR dos branches `squad/*`.

**`squad/A`, `squad/B`, `squad/C`, `squad/D`, `squad/E`** — Integração interna de cada squad. Os membros do squad fazem PR das suas features aqui. É o ambiente de "QA interno" do squad antes de subir para `develop`.

**`feat/*`, `fix/*`, `chore/*`** — Branches pessoais de desenvolvimento. Criados a partir do `squad/*` correspondente. O desenvolvedor tem controle total aqui.

### Convenção de nomes para branches de feature

```
feat/<squad>-<id-da-tarefa>-<descricao-curta>

Exemplos:
  feat/A-A1-pymupdf-setup
  feat/A-A3-chromadb-collections
  feat/B-B1-criterios-schema
  feat/C-C3-rag-chromadb
  feat/D-D3-endpoint-analisar
  feat/E-E1-upload-screen
  fix/B-B3-scanned-pdf-edge-case
  chore/S1-github-initial-setup
  docs/C2-documentar-logica-pesos
```

O `<squad>` no nome da branch deixa claro de imediato qual squad é dono daquele trabalho, o que facilita na hora de revisar PRs e resolver conflitos.

---

## 6. Regras de proteção por branch

As proteções abaixo são configuradas diretamente no GitHub (Settings → Branches) e são **aplicadas automaticamente** — o GitHub bloqueia qualquer operação que viole essas regras, independente de quem tente.

### `main` — protegida, nível máximo

| Regra | Valor |
|---|---|
| Push direto | ❌ Bloqueado |
| Force push | ❌ Bloqueado |
| Delete da branch | ❌ Bloqueado |
| Aprovações necessárias para PR | 2 (tech leads de squads diferentes) |
| CI deve passar | ✅ Obrigatório |
| Linear history | ✅ Obrigatório (squash merge) |
| Origem aceita | Somente PRs vindos de `develop` |

### `develop` — protegida, nível médio

| Regra | Valor |
|---|---|
| Push direto | ❌ Bloqueado |
| Force push | ❌ Bloqueado |
| Aprovações necessárias para PR | 1 (qualquer membro, exceto o autor do PR) |
| CI deve passar | ✅ Obrigatório |
| Origem aceita | Somente PRs vindos de `squad/*` |

### `squad/*` — semi-protegida

| Regra | Valor |
|---|---|
| Push direto | ❌ Bloqueado |
| Aprovações necessárias para PR | 1 (qualquer integrante do squad) |
| CI | Recomendado, não obrigatório |
| Origem aceita | PRs vindos de `feat/*`, `fix/*`, `chore/*` do squad |

### `feat/*`, `fix/*`, `chore/*` — livre

| Regra | Valor |
|---|---|
| Push direto | ✅ Liberado |
| Restrições | Nenhuma — branch pessoal |

### Como configurar no GitHub

Para aplicar as proteções acima:

1. Acesse `Settings → Branches` no repositório
2. Clique em **Add branch ruleset**
3. Crie uma regra para o padrão `main`, uma para `develop` e uma para `squad/*`
4. Configure os campos conforme as tabelas acima

---

## 7. Como abrir um Pull Request

### O fluxo padrão de uma tarefa

```
1. Cria seu branch a partir do squad/*
   git checkout squad/B
   git pull
   git checkout -b feat/B-B2-instructor-groq

2. Desenvolve e faz commits no seu branch
   git add .
   git commit -m "feat(B2): integrar Instructor com cliente Groq"

3. Abre PR: feat/B-B2-instructor-groq → squad/B
   (1 aprovação de integrante do squad)

4. Quando o squad/B tiver as entregas do sprint prontas:
   squad/B → develop
   (1 aprovação de qualquer membro fora do squad)

5. Ao final do sprint, após validação completa:
   develop → main
   (2 aprovações + CI verde)
```

### Template obrigatório de PR

Ao abrir um PR, o GitHub preencherá automaticamente o template abaixo (definido em `.github/pull_request_template.md`). Preencha todos os campos.

```markdown
## O que esse PR faz?
Descrição breve do que foi implementado.

## Tarefa relacionada
Closes # (ex: A1, B3 — referencie a tarefa do backlog)

## Checklist
- [ ] Código roda sem erros localmente
- [ ] Testes unitários passando
- [ ] Sem chaves de API ou senhas no código
- [ ] .env.example atualizado se necessário
- [ ] Documentação atualizada (se aplicável)

## Como testar
Descreva como o revisor pode validar as mudanças.

## Screenshots / Outputs (se aplicável)
```

> Um PR com o checklist incompleto **não deve ser aprovado**. Se você está revisando e perceber que o autor não testou localmente, peça que ele complete antes de aprovar.

---

## 8. Convenção de commits

Use o padrão **Conventional Commits**. O formato é:

```
<tipo>(<escopo>): <descrição curta em minúsculas>
```

| Tipo | Quando usar |
|---|---|
| `feat` | Adicionou uma funcionalidade nova |
| `fix` | Corrigiu um bug |
| `chore` | Configuração, dependências, setup |
| `docs` | Apenas documentação |
| `test` | Adicionou ou corrigiu testes |
| `refactor` | Refatoração sem mudança de comportamento |

O `<escopo>` é o ID da tarefa do backlog (`A1`, `B3`, `D6`, `S1`, etc.).

```
feat(A1): configurar PyMuPDF e testar com editais reais
feat(B2): integrar Instructor com Groq API usando llama-3.1-8b
fix(B3): corrigir extração de tabelas em PDFs escaneados
chore(S1): criar estrutura de pastas e branches do repositório
docs(C2): documentar lógica de pesos do percentual de fit
test(D6): adicionar teste e2e do pipeline completo
refactor(A2): separar chunking de indexação em funções distintas
```

Commits com mensagem genérica como `"fix stuff"`, `"update"` ou `"wip"` **não serão aceitos em PRs para `squad/*` ou acima**.

---

## 9. CODEOWNERS — quem revisa o quê

O arquivo `.github/CODEOWNERS` instrui o GitHub a adicionar automaticamente os revisores corretos quando um PR toca determinados arquivos. Você não precisa lembrar quem chamar — o GitHub faz isso.

```
# ── Squad A — Ingestão & Memória
src/pipeline/filters/f01_*    @squad-A
src/pipeline/filters/f02_*    @squad-A
data/empresa/                 @squad-A

# ── Squad B — Schemas & Extração
src/pipeline/filters/f03_*    @squad-B
src/schemas/                  @squad-B

# ── Squad C — Inferência & Fit
src/pipeline/filters/f04_*    @squad-C
src/pipeline/filters/f05_*    @squad-C

# ── Squad D — Orquestração & Backend
src/api/                      @squad-D
src/pipeline/pipeline.py      @squad-D

# ── Squad E — Frontend & Monitoramento
src/frontend/                 @squad-E
src/monitoring/               @squad-E

# ── Arquivos de contrato central (TODOS revisam)
src/pipeline/base.py          @squad-A @squad-B @squad-C @squad-D
src/pipeline/context.py       @squad-A @squad-B @squad-C @squad-D

# ── Schemas são contrato entre múltiplos squads
src/schemas/criterios_edital.py    @squad-B @squad-C
src/schemas/resultado_fit.py       @squad-B @squad-C @squad-D @squad-E

# ── CI e configuração de repo
.github/                      @squad-A @squad-B @squad-C @squad-D @squad-E
```

### Por que `base.py` e `context.py` têm revisão de todos?

Esses dois arquivos definem a **interface do pipeline inteiro**. Se você muda a assinatura de `Filter.run()` em `base.py`, todos os filtros de todos os squads precisam ser atualizados. Se você renomeia um campo em `PipelineContext`, quem lê aquele campo vai quebrar silenciosamente.

Antes de propor uma mudança nesses arquivos, abra uma Issue no GitHub explicando o que precisa mudar e por quê. Nenhum PR que altere esses arquivos será aprovado sem alinhamento prévio.

### Como criar os times no GitHub

Para o CODEOWNERS funcionar, os times precisam existir no GitHub:

1. Acesse `github.com/org/Agente-IA-i9 → Settings → Collaborators & teams`
2. Clique em **New team** e crie: `squad-A`, `squad-B`, `squad-C`, `squad-D`, `squad-E`
3. Adicione os integrantes de cada squad ao time correspondente
4. Dê permissão **Write** a todos os times no repositório
5. Faça commit do arquivo `CODEOWNERS` — os times passarão a ser requisitados automaticamente nos PRs

---

## 10. CI — o que roda automaticamente

A cada Pull Request aberto para `squad/*`, `develop` ou `main`, o GitHub Actions executa o pipeline de CI definido em `.github/workflows/ci.yml`.

```yaml
name: CI
on: [pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: python -m pytest tests/unit/ -v
      - run: python -m ruff check src/    # lint
```

O CI verifica duas coisas: os **testes unitários** passam, e o **código não tem erros de estilo** (linting com ruff). Se qualquer um dos dois falhar, o PR não pode ser mergeado em `develop` ou `main`.

> **Dica:** rode `python -m ruff check src/` e `python -m pytest tests/unit/` localmente antes de abrir o PR. Economiza tempo.

---

## 11. Fluxo completo de uma tarefa

Para fixar tudo, aqui está o fluxo de ponta a ponta de uma tarefa hipotética — o membro do Squad B implementando a tarefa B2 (configurar Instructor com Groq API):

```bash
# 1. Garantir que o squad/B está atualizado
git checkout squad/B
git pull origin squad/B

# 2. Criar o branch de feature a partir do squad/B
git checkout -b feat/B-B2-instructor-groq

# 3. Desenvolver normalmente, fazendo commits claros
git add src/pipeline/filters/f03_extraction.py
git commit -m "feat(B2): integrar Instructor com Groq usando llama-3.1-8b"

git add tests/unit/test_f03_extraction.py
git commit -m "test(B2): adicionar teste de extração com JSON válido"

# 4. Rodar lint e testes antes de abrir PR
python -m ruff check src/
python -m pytest tests/unit/test_f03_extraction.py -v

# 5. Push e abertura do PR no GitHub
git push origin feat/B-B2-instructor-groq
# Abre PR: feat/B-B2-instructor-groq → squad/B
# Preenche o template e marca tarefa B2 no backlog

# 6. Após aprovação e merge em squad/B:
# Quando o squad/B tiver todas as entregas do sprint, um integrante abre PR:
# squad/B → develop
# 1 aprovação de membro fora do Squad B + CI verde

# 7. Ao final do sprint, após validação:
# develop → main
# 2 aprovações + CI verde
```

---

## 12. Dúvidas frequentes

**"Posso fazer push direto em `develop`?"**  
Não. `develop` está protegida pelo GitHub. A operação será bloqueada automaticamente.

**"Posso fazer push direto em `squad/B`?"**  
Não. Branches `squad/*` também estão protegidas. Crie um `feat/` e abra PR.

**"Posso fazer push direto no meu `feat/`?"**  
Sim. Branches `feat/*` são seus. Faça como quiser.

**"Preciso criar testes unitários para tudo?"**  
Para código que vai para `develop`, sim. O CI vai bloquear o merge se os testes falharem. Para rascunhos no seu `feat/`, pode deixar para o final da tarefa.

**"Quero mudar um campo no `PipelineContext`. O que faço?"**  
Abra uma Issue no GitHub explicando a mudança e os squads afetados. Não abra o PR antes de ter consenso — o CODEOWNERS vai requisitar aprovação de quatro squads de qualquer forma, mas é melhor alinhar antes para não perder tempo.

**"Meu `chroma_db/` está vazio. Como populo?"**  
Rode o script de inicialização do Squad A que processa os documentos em `data/empresa/`. Você precisará ter os documentos da i9+ na pasta local (não estão no git — peça ao Squad A ou ao parceiro).

**"Onde coloco as minhas chaves de API?"**  
- No backend: arquivo `.env` na raiz (nunca commitado — copie de `.env.example`)
- No frontend Streamlit: `src/frontend/.streamlit/secrets.toml` (nunca commitado)
- No Streamlit Community Cloud: configurar pela interface web do deploy

**"Como vejo quais branches existem no remoto?"**

```bash
git fetch --all
git branch -r
```

---

> Última atualização: Sprint 0 — Setup Inicial  
> Mantenedor deste documento: Arthur Soares Padia  
> Dúvidas? Manda msg no grupo.
