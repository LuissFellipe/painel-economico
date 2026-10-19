import os
from datetime import date, datetime, timedelta

import psycopg
import requests

SERIES = {
    432: "selic_meta",
    433: "ipca_mensal",
    1: "dolar_venda",
}
DATA_INICIAL = date(2015, 1, 1)
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
JANELA = timedelta(days=365 * 5)

DDL = """
create schema if not exists raw;
create table if not exists raw.sgs_series (
    codigo_serie int not null,
    nome_serie text not null,
    data date not null,
    valor numeric not null,
    carregado_em timestamptz not null default now(),
    primary key (codigo_serie, data)
);
"""


def conectar():
    return psycopg.connect(
        host=os.getenv("PGHOST", "postgres"),
        port=os.getenv("PGPORT", "5432"),
        user=os.getenv("PGUSER", "bcb"),
        password=os.getenv("PGPASSWORD", "bcb"),
        dbname=os.getenv("PGDATABASE", "bcb"),
    )


def buscar(codigo, inicio, fim):
    registros = []
    while inicio <= fim:
        fim_janela = min(inicio + JANELA, fim)
        resp = requests.get(
            URL.format(codigo=codigo),
            params={
                "formato": "json",
                "dataInicial": inicio.strftime("%d/%m/%Y"),
                "dataFinal": fim_janela.strftime("%d/%m/%Y"),
            },
            timeout=60,
        )
        if resp.status_code != 404:
            resp.raise_for_status()
            registros += resp.json()
        inicio = fim_janela + timedelta(days=1)
    return [
        (datetime.strptime(r["data"], "%d/%m/%Y").date(), r["valor"])
        for r in registros
    ]


def main():
    hoje = date.today()
    with conectar() as conn:
        conn.execute(DDL)
        for codigo, nome in SERIES.items():
            ultima = conn.execute(
                "select max(data) from raw.sgs_series where codigo_serie = %s",
                (codigo,),
            ).fetchone()[0]
            inicio = ultima + timedelta(days=1) if ultima else DATA_INICIAL
            if inicio > hoje:
                print(f"{nome}: já atualizado")
                continue
            linhas = buscar(codigo, inicio, hoje)
            with conn.cursor() as cur:
                cur.executemany(
                    """insert into raw.sgs_series (codigo_serie, nome_serie, data, valor)
                       values (%s, %s, %s, %s)
                       on conflict (codigo_serie, data) do update set valor = excluded.valor""",
                    [(codigo, nome, d, v) for d, v in linhas],
                )
            print(f"{nome}: {len(linhas)} registros a partir de {inicio}")


if __name__ == "__main__":
    main()
