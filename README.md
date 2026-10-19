# Painel econômico: pipeline agendado + dashboard

Projeto integrador. O [pipeline ELT do Banco Central](../pipeline-bcb) roda sozinho todo dia, e um dashboard lê as tabelas finais. Tudo sobe com um comando.

**Pergunta:** como juros, inflação e câmbio se comportaram desde 2015, e qual é o juro real hoje?

## Arquitetura

```
              ┌──────────────────── docker compose ─────────────────────┐
API SGS/BCB ──┼─► pipeline (agendador.py, todo dia às 08h)              │
              │     1. ingestão incremental ─► raw.sgs_series           │
              │     2. dbt build ─► staging ─► marts.fct_indicadores    │
              │     3. registra a execução ─► raw.execucoes             │
              │                     │                                   │
              │               postgres:16                               │
              │                     │                                   │
              │   dashboard (Streamlit) ◄─┘   http://localhost:8501     │
              └─────────────────────────────────────────────────────────┘
```

## Decisões técnicas

- **Agendador em Python em vez de Airflow**: para um único DAG de duas etapas, o Airflow adicionaria scheduler, webserver e um banco de metadados. O `agendador.py` faz o essencial: roda as etapas em ordem, para na primeira falha e grava cada execução em `raw.execucoes`, que o dashboard exibe.
- **Ingestão incremental**: cada execução pede ao BCB só os dias depois da última data gravada, e o `on conflict` torna a carga idempotente.
- **Testes de dados no dbt** (`unique`, `not_null`, `accepted_values`): o `dbt build` falha antes de publicar uma tabela com dados quebrados.
- **Dashboard tolerante à primeira carga**: enquanto os marts não existem, o dashboard mostra um aviso em vez de quebrar.

## Como rodar

```bash
docker compose up -d --build
```

O dashboard fica em http://localhost:8501. Para acompanhar o pipeline, use `docker compose logs -f pipeline`. O horário da execução diária é definido por `HORA_EXECUCAO` no `docker-compose.yml`.
