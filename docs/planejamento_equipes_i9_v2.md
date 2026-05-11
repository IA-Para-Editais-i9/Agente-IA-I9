# Planejamento de Produção — Pipeline de Análise de Editais (i9+)
## Versão Cloud · Free Tier

---

## 1. Divisão em Squads

O projeto é dividido em **5 squads**, cada squad responsável por uma camada do pipeline.

| Squad | Camada do Pipeline | Integrantes |
|---|---|---|
| **A — Ingestão & Memória** | Docling + ChromaDB | — |
| **B — Schemas & Extração** | Pydantic/Instructor + Agente 1 | — |
| **C — Inferência & Fit** | Agente 2 + RAG + % fit | — |
| **D — Orquestração & Backend** | CrewAI + FastAPI | — |
| **E — Frontend & Monitoramento** | Streamlit + Langfuse | — |

---

## 2. Backlog de Tarefas de Produção

### Setup Inicial (todos os squads — Sprint 0)

| # | Tarefa | Descrição |
|---|---|---|
| S1 | Criar repositório GitHub com estrutura de pastas e README inicial | Repositório com estrutura base do projeto, branches definidas e README explicando o propósito de cada módulo |
| S2 | Configurar contas gratuitas: Groq API + Google Gemini API + Streamlit Community Cloud | Criar e validar as chaves de API necessárias, documentar limites do free tier e configurar variáveis de ambiente no projeto |
| S3 | Definir e documentar a estrutura de pastas do projeto | Especificar onde cada squad entrega seu módulo, padrões de nomenclatura e convenções de commit |

---

### Squad A — Ingestão & Memória

> **Responsabilidade:** garantir que o edital e os documentos da empresa cheguem ao pipeline em formato limpo e consultável.

| # | Tarefa | Descrição |
|---|---|---|
| A1 | Configurar Docling e testar com editais reais | Instalar Docling, rodar em 3 editais reais da i9+ (PDFs de 60-80 pág) e verificar se tabelas e seções são preservadas corretamente. Registrar edge cases (PDFs escaneados, colunas duplas, etc.) |
| A2 | Criar módulo de ingestão: PDF → Markdown | Implementar função que recebe qualquer PDF e retorna o Markdown estruturado. Deve funcionar tanto para editais quanto para documentos internos da empresa |
| A3 | Configurar ChromaDB e estrutura de coleções | Criar duas coleções separadas: `editais` e `perfil_empresa`. Definir metadados de cada documento (tipo, data, fonte) |
| A4 | Criar pipeline de indexação dos documentos internos da i9+ | Usar o módulo A2 para converter todos os documentos da empresa (portfólio, contratos, certificações) em chunks e indexar no ChromaDB. Executado uma única vez na inicialização |
| A5 | Levantar e organizar todos os documentos internos da i9+ | Junto ao parceiro: identificar e coletar portfólio de projetos, CNPJ/contrato social, certificações ESG, histórico de editais anteriores. Montar pasta `data/empresa/` organizada |
| A6 | Testar qualidade da busca semântica no ChromaDB | Executar 10 consultas semânticas de teste ("projetos de economia circular", "porte da empresa", "certificações ambientais") e verificar se os trechos retornados são relevantes. Ajustar tamanho dos chunks se necessário |

---

### Squad B — Schemas & Agente Extrator

> **Responsabilidade:** definir a estrutura de dados e implementar o Agente 1, que lê o edital e extrai critérios objetivos em JSON.

| # | Tarefa | Descrição |
|---|---|---|
| B1 | Definir schema Pydantic `CriteriosEdital` | Mapear todos os campos que o Agente 1 deve extrair: título, órgão financiador, valor máximo, prazo, setores elegíveis, porte de empresa, requisitos técnicos, documentos exigidos, critérios de exclusão, necessidade de parceria ICT, palavras-chave temáticas. Validar com o Squad C se os campos são suficientes para a análise de fit |
| B2 | Configurar Instructor com Groq API | Integrar a biblioteca Instructor com o cliente da Groq usando o modelo `llama-3.1-8b-instant`. Testar que a saída é sempre um JSON válido conforme o schema Pydantic, mesmo para editais mal formatados |
| B3 | Escrever e iterar o prompt de extração (Agente 1) | Criar o prompt que instrui a IA a apenas extrair dados factuais, sem interpretação. Testar com 5 editais diferentes e refinar até a precisão ser consistente. O prompt deve enfatizar: "NÃO interprete, apenas copie e organize" |
| B4 | Testar extração com editais reais e documentar resultados | Rodar o Agente 1 em pelo menos 5 editais reais (FINEP, EMBRAPII, BNDES, editais estaduais). Criar uma planilha comparando o JSON extraído com a leitura manual do edital. Identificar campos onde o modelo erra com frequência |
| B5 | Criar fallback Groq → Gemini para o Agente Extrator | Implementar lógica de fallback: se Groq retornar erro (limite de rate ou falha), retentar automaticamente com Google Gemini Flash. Testar o comportamento quando o free tier da Groq está esgotado |
| B6 | Documentar o schema final e apresentar ao parceiro | Criar documento simples explicando cada campo extraído e por que ele importa para a análise. Apresentar ao parceiro (Sandro) para confirmar que nenhum critério relevante está faltando |

---

### Squad C — Inferência & Fit

> **Responsabilidade:** implementar o Agente 2, que recebe o JSON estruturado + perfil da empresa e produz o % de fit e as recomendações.

| # | Tarefa | Descrição |
|---|---|---|
| C1 | Definir schema Pydantic `ResultadoFit` | Mapear todos os campos da saída do Agente 2: percentual_fit (float 0-100), classificação ("Alto"/"Médio"/"Baixo"/"Inviável"), critérios_atendidos (lista), gaps_identificados (lista), recomendações_adequação (lista), necessidade_parceria_ICT (bool), sugestão_parceiros (lista), justificativa_percentual (texto), ações_prioritárias (top 3) |
| C2 | Implementar a lógica de pesos do % de fit | O % final é composto por: 40% elegibilidade técnica (CNAE, porte, setor) + 30% alinhamento temático (economia circular, baterias, sustentabilidade) + 20% capacidade documental e financeira + 10% experiência prévia com editais similares. Implementar essa lógica de forma que o prompt instrua o modelo a calcular cada sub-score separadamente antes de compor o total |
| C3 | Implementar a busca RAG no ChromaDB | Dado o resumo_objetivo do edital (campo extraído pelo Agente 1), buscar no ChromaDB os 10 trechos mais relevantes do perfil da empresa. Esses trechos são o "contexto da empresa" que o Agente 2 recebe |
| C4 | Escrever e iterar o prompt de inferência (Agente 2) | Criar o prompt que instrui o modelo a: (a) analisar fit com base nos pesos definidos, (b) ser honesto sobre gaps, (c) sugerir "pivotagens" reais e específicas para a i9+, (d) identificar parceiros concretos (ex: UTFPR, SENAI-PR) quando necessário. Testar com pelo menos 5 editais |
| C5 | Integrar RAG + Agente 2 e testar qualidade | Conectar a saída do ChromaDB (Squad A) como contexto de entrada para o prompt do Agente 2. Verificar se o modelo usa as informações da empresa corretamente ou ignora o contexto RAG. Ajustar o prompt conforme necessário |
| C6 | Calibrar % de fit com editais já avaliados manualmente | Pegar 3 editais que o parceiro já analisou manualmente (e sabe se tinha fit ou não). Rodar o Agente 2 e comparar o % gerado com a avaliação humana. Ajustar prompts e pesos até os resultados convergirem |

---

### Squad D — Orquestração & Backend

> **Responsabilidade:** conectar todos os módulos em sequência e expor a funcionalidade via API.

| # | Tarefa | Descrição |
|---|---|---|
| D1 | Implementar orquestração com CrewAI | Criar o pipeline principal: Agente 1 (extração) → RAG (ChromaDB) → Agente 2 (inferência). Usar CrewAI para definir os dois agentes com seus papéis, objetivos e ferramentas. Garantir que a saída de um é a entrada do próximo |
| D2 | Implementar tratamento de erros e logs do pipeline | Adicionar try/except em cada etapa com mensagens de erro claras. Implementar logging que registra: qual edital foi processado, tempo de cada etapa, quantos tokens foram usados, qual agente rodou |
| D3 | Criar endpoint FastAPI: `POST /analisar-edital` | Endpoint que recebe o PDF do edital como upload, roda o pipeline completo e retorna o JSON com o `ResultadoFit`. Incluir validação do arquivo (só aceita PDF, máx 100MB) |
| D4 | Criar endpoint FastAPI: `POST /indexar-documento` | Endpoint que recebe documentos da empresa (PDF/DOCX) e os adiciona ao ChromaDB. Retorna confirmação e número de chunks indexados |
| D5 | Implementar controle de uso do free tier | Criar um contador de requisições por sessão que alerta quando o limite do Groq (30 req/min) está próximo. Implementar delay automático entre requisições para evitar rate limit errors. Documentar limites reais testados |
| D6 | Teste de ponta a ponta do pipeline | Rodar o pipeline completo (Docling → ChromaDB → Agente 1 → Agente 2 → JSON final) com um edital real, medir tempo total de execução, verificar que todas as etapas funcionam em sequência e que o JSON final é válido |

---

### Squad E — Frontend & Monitoramento

> **Responsabilidade:** construir a interface visual para o usuário e o painel de monitoramento do sistema.

| # | Tarefa | Descrição |
|---|---|---|
| E1 | Criar tela de upload no Streamlit | Tela inicial com: campo de upload do PDF do edital, campo de upload de documentos adicionais da empresa (opcional, para complementar a base), botão "Analisar" que chama o backend FastAPI |
| E2 | Criar painel de resultado no Streamlit | Tela de resultado com: indicador visual do % de fit (gauge ou barra de progresso colorida), classificação em destaque ("Alto / Médio / Baixo"), e justificativa do percentual em texto |
| E3 | Criar visualização de critérios atendidos vs. gaps | No painel de resultado: duas colunas lado a lado — ✅ Critérios Atendidos e ❌ Gaps Identificados — exibindo as listas retornadas pelo Agente 2 |
| E4 | Criar visualização de recomendações e top 3 ações | Seção no painel de resultado com: lista de recomendações de adequação, destaque das "Top 3 Ações Prioritárias" para aumentar o fit, seção de parceiros sugeridos quando necessário |
| E5 | Configurar Langfuse para monitoramento | Integrar Langfuse (self-hosted via Docker Compose ou conta gratuita) para registrar todas as chamadas LLM: prompt enviado, resposta recebida, tokens consumidos, latência, modelo usado |
| E6 | Criar dashboard de monitoramento no Langfuse | Configurar traces para as duas chamadas do pipeline (Agente 1 e Agente 2) com as etiquetas corretas. Criar visualização que mostre: tempo médio por análise, taxa de erro, consumo de tokens por sessão |

---

## 3. Critérios de Validação por Sprint

> Checklist interno da equipe para saber se o sprint está pronto antes de avançar. Nenhum desses critérios depende de reunião — são verificações que a própria equipe executa.

### ✅ Sprint 1 — Ingestão & Memória
- Qualquer PDF de edital (incluindo escaneados e com tabelas) é convertido em Markdown sem perda de estrutura
- As coleções `editais` e `perfil_empresa` existem no ChromaDB com os documentos da i9+ indexados
- Uma busca semântica por tema relevante retorna trechos pertinentes da empresa

### ✅ Sprint 2 — Agente Extrator
- O Agente 1 retorna um JSON válido (sem erro Pydantic) para qualquer edital testado
- Os campos extraídos batem com a leitura manual do edital em pelo menos 85% dos casos
- O fallback Groq → Gemini funciona automaticamente quando o rate limit é atingido

### ✅ Sprint 3 — Agente Inferidor
- O Agente 2 retorna um `ResultadoFit` válido com % de fit entre 0 e 100
- As recomendações são específicas para a i9+ (mencionam a empresa, não são genéricas)
- O % de fit diverge no máximo 15 pontos da avaliação manual da equipe em 3 editais de teste

### ✅ Sprint 4 — Backend & Frontend
- O endpoint `POST /analisar-edital` recebe um PDF e devolve o JSON final sem erros
- A interface Streamlit exibe o resultado completo (% fit, gaps, recomendações) sem necessidade de explicação verbal
- Langfuse está registrando 100% das chamadas LLM com latência e tokens

### ✅ Sprint 5 — Entrega
- O pipeline completo roda em menos de 3 minutos para um edital de 80 páginas
- Um integrante que não desenvolveu a feature consegue operar o sistema apenas lendo a documentação
- O parceiro confirma que o sistema está aprovado para uso

---

## 4. Cronograma por Sprints

O projeto tem **5 sprints de produção** + 1 sprint de setup. Os sprints são definidos por entrega, não por tempo fixo — um sprint pode ser concluído em menos de uma semana ou levar mais, dependendo do ritmo da equipe.

```
SPRINT 0        SPRINT 1        SPRINT 2        SPRINT 3        SPRINT 4        SPRINT 5
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Setup   │    │ Ingestão │    │  Agente  │    │  Agente  │    │ Backend  │    │ Testes & │
│          │    │ +Memória │    │ Extrator │    │ Inferidor│    │+Frontend │    │ Entrega  │
│ S1,S2,S3 │    │ A1 a A6  │    │ B1 a B6  │    │ C1 a C6  │    │ D1 a D6  │    │          │
│          │    │          │    │          │    │ +D1,D2   │    │ E1 a E6  │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                   ▼ checklist      ▼ checklist     ▼ checklist     ▼ checklist     ▼ checklist
               Sprint 1         Sprint 2        Sprint 3        Sprint 4        Sprint 5
```

### Dependências Críticas entre Squads

O pipeline tem dependências em cascata. A ordem de entrega importa:

```
Squad A (Docling + ChromaDB) → Squad B pode começar B3/B4 em paralelo
Squad B (Agente Extrator)    → Squad C pode começar só depois de B1/B2 prontos
Squad C (Agente Inferidor)   → Squad D pode orquestrar só depois de C1/C2 prontos
Squads D + E (Backend/Front) → Podem ser desenvolvidos em paralelo entre si
```

**Regra prática:** Squads A e B trabalham em paralelo no Sprint 1-2. Squad C começa no Sprint 2 enquanto B termina. Squad D e E constroem "em cima" do que A, B, C entregam.

### O que pode ser antecipado por squad

Mesmo respeitando as dependências acima, cada squad tem tarefas que **não bloqueiam** os demais e podem ser adiantadas a qualquer momento:

| Squad | Pode adiantar sem depender de ninguém |
|---|---|
| **A** | A5 (levantar documentos internos) — não depende de código |
| **B** | B1 (definir schema) e B3 (rascunho do prompt) — podem ser feitos em paralelo com o Sprint 1 |
| **C** | C1 (definir schema ResultadoFit) e C2 (lógica de pesos) — design puro, sem dependência de código |
| **D** | D3/D4 (endpoints FastAPI com mock) — estrutura da API pode ser montada antes dos agentes ficarem prontos |
| **E** | E1/E2 (telas Streamlit com dados mockados) — layout da interface não depende do backend real |

---

## 5. Limites do Free Tier e Como Contornar

| Recurso | Limite | Impacto Real | Mitigação |
|---|---|---|---|
| **Groq** | 30 req/min · 14.400 req/dia | Cada análise usa 2 chamadas (1 por agente). Limite real: ~7.200 editais/dia | Mais que suficiente para uso da i9+. Tarefa D5 implementa delay automático |
| **Groq (tokens)** | 6.000 tokens/min (llama 8B) | Editais longos podem precisar de chunking extra | Docling divide o edital em seções; cada seção é processada separadamente se necessário |
| **Google Gemini** | 15 req/min · 1.500 req/dia | Fallback apenas. Se Groq cair, suporta até 750 análises/dia | Tarefa B5 implementa fallback automático |
| **Streamlit Community Cloud** | 1 app gratuito · sempre ligado | Sem limite de usuários simultâneos | Suficiente para uso interno da i9+ |
| **ChromaDB** | Sem limite (roda local) | Apenas limite de disco da máquina | Docs da empresa são poucos KB; sem problema |
| **GitHub** | Repositório público ou privado gratuito | Nenhum | Usar repositório privado da equipe |

---

## 6. Carga por Integrante

> Preencha os integrantes de cada squad conforme sua decisão. Cada pessoa fica responsável por 2 tarefas de produção do seu squad.

| Squad | Integrante | Tarefas |
|---|---|---|
| **A** | _________________ | A1, A2 |
| **A** | _________________ | A3, A4 |
| **A** | _________________ | A5, A6 |
| **B** | _________________ | B1, B2 |
| **B** | _________________ | B3, B4 |
| **B** | _________________ | B5, B6 |
| **C** | _________________ | C1, C2 |
| **C** | _________________ | C3, C4 |
| **C** | _________________ | C5, C6 |
| **D** | _________________ | D1, D2 |
| **D** | _________________ | D3, D4 |
| **D** | _________________ | D5, D6 |
| **E** | _________________ | E1, E2 |
| **E** | _________________ | E3, E4 |
| **E** | _________________ | E5, E6 |

---

> **Próximo passo:** após definição dos squads e atribuição de membros, todos os squads iniciam o Sprint 0 (setup) simultaneamente. A primeira entrega concreta de todos os squads acontece ao final do Sprint 1.
