import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL", "postgresql+psycopg://bcb:bcb@localhost:5437/bcb"))

st.set_page_config(page_title="Painel econômico", layout="wide")


@st.cache_data(ttl=600)
def consultar(sql):
    with engine.connect() as con:
        return pd.read_sql(text(sql), con)


def br(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def tabela_existe(nome):
    return consultar(f"select to_regclass('{nome}') is not null as existe").existe[0]


st.title("Painel econômico: Selic, IPCA e dólar")
st.caption("Fonte: SGS do Banco Central. Atualizado automaticamente todo dia pelo pipeline.")

if not tabela_existe("marts.fct_indicadores_mensais"):
    st.info("O pipeline ainda está carregando os dados. Recarregue a página em alguns segundos.")
    st.stop()

df = consultar("select * from marts.fct_indicadores_mensais order by mes")
df["mes"] = pd.to_datetime(df["mes"])
anos = st.slider("Período", int(df.mes.dt.year.min()), int(df.mes.dt.year.max()),
                 (int(df.mes.dt.year.min()), int(df.mes.dt.year.max())))
df = df[df.mes.dt.year.between(*anos)]

ultimo = df.dropna(subset=["ipca_12m"]).iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Selic (média do mês)", f"{br(ultimo.selic_media_aa)}% a.a.")
c2.metric("IPCA 12 meses", f"{br(ultimo.ipca_12m)}%")
c3.metric("Juro real", f"{br(ultimo.juro_real_aa)}% a.a.")
c4.metric("Dólar médio", f"R$ {br(ultimo.dolar_medio)}")
st.caption(f"Referência: {ultimo.mes:%m/%Y}")

CORES = {"Selic": "#2a78d6", "IPCA 12 meses": "#eb6834", "Juro real": "#1baf7a"}
NOMES = {"selic_media_aa": "Selic", "ipca_12m": "IPCA 12 meses", "juro_real_aa": "Juro real"}

st.subheader("Juros e inflação")
juros = df.melt(id_vars="mes", value_vars=list(NOMES), var_name="serie", value_name="valor")
juros["serie"] = juros.serie.map(NOMES)
fig = px.line(juros, x="mes", y="valor", color="serie", color_discrete_map=CORES,
              labels={"mes": "", "valor": "% ao ano", "serie": ""})
fig.update_layout(separators=",.", legend=dict(orientation="h", y=1.08), hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# Dólar em gráfico próprio: Selic (%) e dólar (R$) num eixo duplo sugeririam
# uma relação que depende só de como as duas escalas foram alinhadas.
st.subheader("Dólar")
fig = px.line(df, x="mes", y="dolar_medio", labels={"mes": "", "dolar_medio": "R$ (média do mês)"},
              color_discrete_sequence=["#2a78d6"])
fig.update_layout(separators=",.", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

if tabela_existe("raw.execucoes"):
    st.subheader("Execuções do pipeline")
    st.dataframe(
        consultar("select inicio, fim, sucesso, etapa_com_falha from raw.execucoes order by id desc limit 10"),
        hide_index=True, use_container_width=True,
    )
