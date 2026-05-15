# Exportação de Relatório

## O que é

Recurso que permite baixar o resultado de uma análise como arquivo
**Markdown** (`.md`) com todo o diagnóstico estruturado: título do
edital, órgão, percentual de fit, classificação, justificativa,
critérios atendidos, gaps, top 3 ações, recomendações e parceiros
sugeridos.

Markdown foi a escolha pelo equilíbrio entre simplicidade (texto puro,
versionável, lê em qualquer editor) e formatação (cabeçalhos, listas,
ênfase). PDF é roadmap futuro.

## Como usar

### A partir do painel de Resultado

Após concluir uma análise:

1. Vá em **📊 Resultado**
2. Role até o rodapé
3. Clique em **📥 Exportar Relatorio** (botão central, ao lado dos
   botões "Voltar ao Upload" e "Nova Analise")
4. O navegador faz download do arquivo `analise_<slug>_<timestamp>.md`

### A partir do Histórico

Para baixar análises antigas:

1. Vá em **📚 Histórico**
2. Em cada card de análise, clique em **📥 Exportar**
3. Download imediato do relatório daquela análise específica

## Formato do arquivo

```markdown
# Analise de Edital — {edital_titulo}

**Orgao:** {orgao}
**Data da analise:** DD/MM/AAAA HH:MM
**Classificacao:** {Alto|Medio|Baixo|Inviavel}
**Percentual de Fit:** {0-100}%
**Valor estimado:** {valor}
**Prazo de entrega:** {prazo}

---

## Justificativa do percentual
...

## Criterios Atendidos (N)
- ✅ ...

## Gaps Identificados (N)
- ❌ ...

## Top 3 Acoes Prioritarias
1. **Titulo** — descricao + prazo + esforco + responsavel
2. ...

## Recomendacoes de Adequacao
- ...

## Parceiros Sugeridos
- **Nome** (Tipo) — Match X%: motivo
```

## Nome do arquivo

Formato: `analise_<slug>_<AAAAMMDD_HHMM>.md`

- `slug`: título do edital normalizado (minúsculas, sem acentos, sem
  caracteres especiais, máx 60 chars)
- timestamp: data/hora local do clique

Exemplo: `analise_edital_de_inovacao_001_2026_20260515_1843.md`

## Robustez

O exportador é defensivo:

- **Listas vazias** → renderiza "_Nenhum item registrado._" em vez
  de seção em branco
- **Itens em formato dict OU string** → ambos suportados (mesmo padrão
  das funções `render_*` do painel de Resultado)
- **Campos opcionais** → se `justificativa_percentual` não existe,
  cai pra `resumo_executivo`; se também não existir, mostra mensagem
  padrão
- **Resultado inválido** (`None`, lista, etc.) → retorna "Relatório
  indisponível" em vez de quebrar

## Limitações atuais

- Apenas Markdown — PDF/DOCX são roadmap futuro
- Não permite escolher seções (exporta tudo)
- Não tem template customizável

## Roadmap futuro

- Exportar PDF via `reportlab` ou `weasyprint`
- Exportar DOCX via `python-docx`
- Modal de seleção (escolher quais seções exportar)
- Template branding i9+ com logo e cabeçalho institucional
- Exportar histórico inteiro em ZIP
