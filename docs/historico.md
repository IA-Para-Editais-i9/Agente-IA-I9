# Histórico de Análises

## O que é

Recurso que armazena as análises de editais concluídas na sessão atual e
permite revisitar resultados anteriores sem precisar re-rodar o upload e
a análise. Pensado para quando o usuário compara vários editais em
sequência (ex: triagem semanal).

## Como funciona

- Cada vez que o usuário clica em **"Iniciar Análise IA"** na página de
  Upload e o processamento conclui (real ou mock), a análise é
  **inserida no início** de `st.session_state["historico"]`.
- O histórico é uma lista de dicts com as chaves: `timestamp`,
  `edital_nome`, `edital_titulo`, `orgao`, `percentual`,
  `classificacao` e `resultado_completo` (o `resultado_fit` inteiro,
  para permitir reabrir o painel).
- Limite de **50 itens** — itens mais antigos são descartados
  automaticamente para não inchar o `session_state`.

## Como acessar

Menu lateral do Streamlit → **📚 Histórico**.

A página exibe:

- Contador de análises na sessão
- Lista de cards (mais recente primeiro), cada um com:
  - Título do edital
  - Badge colorido com o percentual (cor varia conforme faixa)
  - Órgão, classificação e timestamp
  - Botão **"🔍 Ver Detalhes"** que reabre o painel de Resultado com
    aqueles dados
- Empty state amigável quando ainda não há análises
- Botão **"🗑️ Limpar Histórico"** no rodapé (com checkbox de
  confirmação obrigatório, para evitar clique acidental)

## Cores do badge de percentual

| Faixa de % | Cor       |
|------------|-----------|
| 80–100     | Verde     |
| 60–79      | Amarelo   |
| 40–59      | Laranja   |
| 0–39       | Vermelho  |

## Limitações atuais

- **Não persiste entre sessões.** Quando o usuário fecha o navegador ou
  o Streamlit reinicia, o histórico é perdido (é apenas
  `st.session_state`).
- **Não exporta** — para arquivo permanente, ver o recurso de
  Exportação de Relatório ([exportar-relatorio.md](exportar-relatorio.md)).

## Roadmap futuro

- Persistir em SQLite local (`data/historico.db`) ou JSON
  (`data/historico.json`) para sobreviver entre sessões.
- Adicionar busca/filtro por órgão, percentual ou data.
- Permitir comparar duas análises lado a lado.
