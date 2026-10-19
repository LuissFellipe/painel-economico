import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text

engine = create_engine(os.getenv("DATABASE_URL", "postgresql+psycopg://bcb:bcb@localhost:5434/bcb"))

st.set_page_config(page_title="Painel econômico", layout="wide")


@st.cache_data(ttl=600)
def consultar(sql):
    with engine.connect() as con:
        return pd.read_sql(text(sql), con)


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
c1.metric("Selic (média do mês)", f"{ultimo.selic_media_aa:.2f}% a.a.")
c2.metric("IPCA 12 meses", f"{ultimo.ipca_12m:.2f}%")
c3.metric("Juro real", f"{ultimo.juro_real_aa:.2f}% a.a.")
c4.metric("Dólar médio", f"R$ {ultimo.dolar_medio:.2f}")
st.caption(f"Referência: {ultimo.mes:%m/%Y}")

st.subheader("Juros e inflação")
st.plotly_chart(
    px.line(df, x="mes", y=["selic_media_aa", "ipca_12m", "juro_real_aa"],
            labels={"mes": "", "value": "% ao ano", "variable": ""}),
    use_container_width=True,
)

st.subheader("Selic e dólar")
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df.mes, y=df.selic_media_aa, name="Selic % a.a."), secondary_y=False)
fig.add_trace(go.Scatter(x=df.mes, y=df.dolar_medio, name="Dólar R$"), secondary_y=True)
st.plotly_chart(fig, use_container_width=True)

if tabela_existe("raw.execucoes"):
    st.subheader("Execuções do pipeline")
    st.dataframe(
        consultar("select inicio, fim, sucesso, etapa_com_falha from raw.execucoes order by id desc limit 10"),
        hide_index=True, use_container_width=True,
    )
