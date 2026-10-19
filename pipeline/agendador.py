import os
import subprocess
import time
from datetime import datetime, timedelta

import psycopg

from ingest.ingest_bcb import conectar

HORA = int(os.getenv("HORA_EXECUCAO", "8"))

DDL = """
create schema if not exists raw;
create table if not exists raw.execucoes (
    id serial primary key,
    inicio timestamptz not null,
    fim timestamptz not null,
    sucesso boolean not null,
    etapa_com_falha text,
    saida text
);
"""

ETAPAS = [
    ("ingestao", ["python", "-m", "ingest.ingest_bcb"]),
    ("dbt", ["dbt", "build", "--profiles-dir", "dbt_bcb", "--project-dir", "dbt_bcb"]),
]


def aguardar_banco():
    for _ in range(30):
        try:
            with conectar():
                return
        except psycopg.OperationalError:
            time.sleep(2)
    raise RuntimeError("Postgres indisponível")


def executar():
    inicio = datetime.now().astimezone()
    saida, falha = [], None
    for nome, comando in ETAPAS:
        resultado = subprocess.run(comando, capture_output=True, text=True)
        saida.append(f"== {nome} ==\n{resultado.stdout}{resultado.stderr}")
        print(saida[-1], flush=True)
        if resultado.returncode != 0:
            falha = nome
            break
    with conectar() as conn:
        conn.execute(DDL)
        conn.execute(
            "insert into raw.execucoes (inicio, fim, sucesso, etapa_com_falha, saida) values (%s, now(), %s, %s, %s)",
            (inicio, falha is None, falha, "\n".join(saida)[-20000:]),
        )
    print(f"execução {'concluída' if falha is None else f'falhou em {falha}'}", flush=True)


def proxima_execucao(agora):
    alvo = agora.replace(hour=HORA, minute=0, second=0, microsecond=0)
    return alvo if alvo > agora else alvo + timedelta(days=1)


def main():
    aguardar_banco()
    executar()
    while True:
        alvo = proxima_execucao(datetime.now())
        print(f"próxima execução em {alvo:%d/%m/%Y %H:%M}", flush=True)
        time.sleep((alvo - datetime.now()).total_seconds())
        executar()


if __name__ == "__main__":
    main()
