from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def convert_string_to_quarter(quarter):
    quarter = quarter.replace("trimestre", "Q").replace("º", "")
    quarter, q, year = quarter.split(" ")
    return f"{year}{q}{quarter}"


def convert_to_datetime(month_year):
    get_month = {
        "janeiro": 1,
        "fevereiro": 2,
        "março": 3,
        "abril": 4,
        "maio": 5,
        "junho": 6,
        "julho": 7,
        "agosto": 8,
        "setembro": 9,
        "outubro": 10,
        "novembro": 11,
        "dezembro": 12,
    }
    month, year = month_year.split(" ")
    return datetime.strptime(f"01-{get_month[month]}-{year}", "%d-%m-%Y")


# Configura a pagina
st.set_page_config(layout="wide")

# https://sidra.ibge.gov.br/tabela/2296
custo_medio_m2 = pd.read_csv("./static/custo-medio-m2-em-moeda-corrente.csv")
# https://sidra.ibge.gov.br/tabela/1737
ipca = pd.read_csv("./static/IPCA-serie-histórica.csv")
# https://sidra.ibge.gov.br/tabela/5438
rendimento_mensal = pd.read_csv(
    "./static/rendimento-medio-mensal-real-trabalhadores.csv"
)
rendimento_mensal["Trimestre"] = rendimento_mensal["Trimestre"].apply(lambda quarter: convert_string_to_quarter(quarter))
rendimento_mensal = rendimento_mensal[rendimento_mensal["Nível de instrução"] != "Total"]
rendimento_mensal["Valor"] = rendimento_mensal["Valor"].replace("-", "0")
rendimento_mensal["Valor"] = pd.to_numeric(rendimento_mensal["Valor"]).fillna(0).astype(int)

custo_medio_m2 = custo_medio_m2.rename(
    columns={
        "Unnamed: 1": "Unidade Territorial",
        "Unnamed: 3": "Valor",
        "Variável": "Variável",
    }
)
ipca = ipca.rename(
    columns={
        "Unnamed: 1": "Unidade Territorial",
        "Unnamed: 3": "Valor",
        "Variável": "Variável",
    }
)

df = pd.concat([custo_medio_m2, ipca])

df["Data"] = pd.to_datetime(df["Mês"].apply(convert_to_datetime)).dt.date
df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

df["Trimestre"] = df["Data"].dt.to_period("Q").astype(str)

quarter = st.sidebar.multiselect(
    "Selecione um ou mais trimestres", ["Q1", "Q2", "Q3", "Q4"], #index=None
)
year = st.sidebar.multiselect("Selecione o ano que deseja filtrar", list(range(1980, 2025)))

quarter_list = [f"{_year}{_quarter}" for _year in year for _quarter in quarter]

start_date = st.sidebar.date_input("Seleciona a data inicial", value=None)
end_date = st.sidebar.date_input("Seleciona a data final", value=None)
if quarter_list:
    df = pd.concat([df[df["Trimestre"] == _quarter] for _quarter in quarter_list])
    # df.drop_duplicates()
    rendimento_mensal = [rendimento_mensal[rendimento_mensal["Trimestre"] == _quarter ] for _quarter in quarter_list]
if start_date and end_date:
    df = df[(df["Data"].dt.date >= start_date) & (df["Data"].dt.date <= end_date)]
if start_date and not end_date:
    df = df[df["Data"].dt.date >= start_date]
if not start_date and end_date:
    df = df[df["Data"].dt.date <= end_date]

col1, col2 = st.columns(2)

ipca_indice = df[
    df["Variável"]
    == "IPCA - Número-índice (base: dezembro de 1993 = 100) (Número-índice)"
]
ipca_indice["Valor Indice"] = ipca_indice["Valor"].apply(
    lambda value: float(value) / 1000
)
ipca_variacao = df[df["Variável"] == "IPCA - Variação mensal (%)"]
ipca_graph = px.bar(
    ipca_indice,
    x="Data",
    y="Valor Indice",
    color="Valor Indice",
    title="Indice e variação do IPCA (Economia)",
)
ipca_graph.add_trace(
    go.Scatter(
        x=ipca_variacao["Data"],
        y=ipca_variacao["Valor"],
        name="Variação do IPCA",
        marker=dict(color="red"),
    )
)
col1.plotly_chart(ipca_graph)

preco_m2 = df[df["Variável"] == "Custo médio m² - moeda corrente (Reais)"]
preco_m2_graph = px.line(
    preco_m2,
    x="Data",
    y="Valor",
    # color="Variável",
    title="Valor do metro quadrado por mês e ano (Economia)",
    markers=True,
)
col2.plotly_chart(preco_m2_graph)

col3, col4 = st.columns(2)

instruction_level = st.sidebar.selectbox(
    "Selecione o nivel de instrução",
    rendimento_mensal[rendimento_mensal["Nível de instrução"] != "Total"][
        "Nível de instrução"
    ].unique(),
    index=None,
)
if instruction_level:
    rendimento_mensal = rendimento_mensal[rendimento_mensal["Nível de instrução"] == instruction_level]
trace = rendimento_mensal["Nível de instrução"].value_counts()

instruction_graph = px.line(
    rendimento_mensal,
    x="Nível de instrução",
    y="Valor",
    # color="Valor",
    title="Rendimento médio por nivel de instrução (Economia)",
)
# instruction_graph.add_trace(
#     go.Scatter(
#         x=trace.index,
#         y=trace.values,
#         name="Quantidade por nivel de instrução",
#         marker=dict(color="red"),
#     )
# )
col3.plotly_chart(instruction_graph)