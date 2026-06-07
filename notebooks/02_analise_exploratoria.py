# %% [markdown]
# # 02 · Análise Exploratória de Dados (EDA)
# **Projeto:** Inteligência Comercial — Varejo E-commerce Brasil  
# **Objetivo:** Entender o comportamento das vendas antes de ir pras métricas específicas.  
# Aqui quero responder: *o que está acontecendo?* — antes de perguntar *por quê*.

# %% [markdown]
# ## 1. Setup

# %%
import os
import warnings


import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

def _achar_raiz(inicio, marcador="requirements.txt"):
    """Sobe pastas ate encontrar o marcador - funciona de qualquer subpasta."""
    atual = os.path.abspath(inicio)
    for _ in range(8):
        if os.path.isfile(os.path.join(atual, marcador)):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:
            break
        atual = pai
    raise FileNotFoundError(
        "Raiz do projeto nao encontrada. "
        "Certifique-se de que requirements.txt existe na pasta raiz."
    )

BASE = _achar_raiz(os.path.dirname(os.path.abspath(__file__)))
DIR_PROCESSADOS = os.path.join(BASE, "dados", "processados")
DIR_GRAFICOS    = os.path.join(BASE, "dashboard", "graficos_eda")
os.makedirs(DIR_GRAFICOS, exist_ok=True)

# paleta personalizada — me cansei do azul default do matplotlib
PALETA = {
    "primaria":   "#2563EB",   # azul
    "secundaria": "#7C3AED",   # roxo
    "sucesso":    "#059669",   # verde
    "alerta":     "#D97706",   # âmbar
    "perigo":     "#DC2626",   # vermelho
    "neutro":     "#64748B",   # cinza
}
COR_SEQ   = "#2563EB"
CORES_CAT = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626"]

sns.set_theme(style="whitegrid", palette=CORES_CAT, font="sans-serif")
plt.rcParams.update({
    "figure.dpi":      150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
})

# %%
df = pd.read_csv(os.path.join(DIR_PROCESSADOS, "pedidos_analitico.csv"), encoding="utf-8-sig")
df["data_pedido"] = pd.to_datetime(df["data_pedido"])
df["ano_mes"]     = pd.to_datetime(df["ano_mes"])

print(f"Dataset: {df.shape[0]:,} pedidos válidos | {df['id_cliente'].nunique():,} clientes únicos")
print(f"Período: {df['data_pedido'].min().strftime('%d/%m/%Y')} → {df['data_pedido'].max().strftime('%d/%m/%Y')}")

# %% [markdown]
# ## 2. Receita mensal — evolução e sazonalidade

# %%
receita_mensal = (
    df.groupby("ano_mes")["valor_total"]
    .sum()
    .reset_index()
    .rename(columns={"valor_total": "receita"})
    .sort_values("ano_mes")
)

fig, ax = plt.subplots(figsize=(14, 5))

ax.fill_between(
    receita_mensal["ano_mes"],
    receita_mensal["receita"],
    alpha=0.15,
    color=COR_SEQ,
)
ax.plot(
    receita_mensal["ano_mes"],
    receita_mensal["receita"],
    color=COR_SEQ,
    linewidth=2.5,
    marker="o",
    markersize=5,
)

# destacar Black Friday (novembro)
for _, row in receita_mensal[receita_mensal["ano_mes"].dt.month == 11].iterrows():
    ax.annotate(
        "Black Friday",
        xy=(row["ano_mes"], row["receita"]),
        xytext=(0, 14),
        textcoords="offset points",
        ha="center",
        fontsize=8,
        color=PALETA["perigo"],
        fontweight="bold",
    )

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax.set_title("Receita Mensal — Jan 2023 a Dez 2024", fontweight="bold", pad=14)
ax.set_xlabel("")
ax.set_ylabel("Receita (R$)")
fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "01_receita_mensal.png"), bbox_inches="tight")
plt.show()
print("Gráfico salvo ✓")

# %% [markdown]
# ## 3. Receita por categoria de produto

# %%
receita_cat = (
    df.groupby("categoria")["valor_total"]
    .sum()
    .sort_values(ascending=True)
    .reset_index()
)
receita_cat["pct"] = (receita_cat["valor_total"] / receita_cat["valor_total"].sum() * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 4))

bars = ax.barh(
    receita_cat["categoria"],
    receita_cat["valor_total"],
    color=CORES_CAT[:len(receita_cat)],
    height=0.55,
    edgecolor="white",
)

for bar, (_, row) in zip(bars, receita_cat.iterrows()):
    ax.text(
        bar.get_width() + 5_000,
        bar.get_y() + bar.get_height() / 2,
        f"R$ {row['valor_total']/1000:.0f}k  ({row['pct']}%)",
        va="center",
        fontsize=9,
    )

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax.set_title("Receita Total por Categoria de Produto", fontweight="bold", pad=12)
ax.set_xlabel("Receita (R$)")
fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "02_receita_categoria.png"), bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 4. Performance por região

# %%
receita_regiao = (
    df.groupby("regiao")
    .agg(
        receita=("valor_total", "sum"),
        pedidos=("id_pedido", "count"),
        clientes_unicos=("id_cliente", "nunique"),
    )
    .reset_index()
    .sort_values("receita", ascending=False)
)
receita_regiao["ticket_medio"] = (receita_regiao["receita"] / receita_regiao["clientes_unicos"]).round(2)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# receita por região
axes[0].bar(
    receita_regiao["regiao"],
    receita_regiao["receita"],
    color=CORES_CAT,
    width=0.55,
    edgecolor="white",
)
axes[0].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
axes[0].set_title("Receita por Região", fontweight="bold")
axes[0].set_xlabel("")

# ticket médio por região
axes[1].bar(
    receita_regiao["regiao"],
    receita_regiao["ticket_medio"],
    color=CORES_CAT,
    width=0.55,
    edgecolor="white",
)
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
axes[1].set_title("Ticket Médio por Cliente × Região", fontweight="bold")

for ax in axes:
    ax.tick_params(axis="x", labelsize=9)

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "03_performance_regiao.png"), bbox_inches="tight")
plt.show()

print("\nReceita por região:")
print(receita_regiao.to_string(index=False))

# %% [markdown]
# ## 5. Top 10 produtos mais vendidos

# %%
top_produtos = (
    df.groupby("nome_produto")
    .agg(
        receita=("valor_total", "sum"),
        unidades=("quantidade", "sum"),
        pedidos=("id_pedido", "count"),
    )
    .sort_values("receita", ascending=False)
    .head(10)
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 6))

cores_top = [PALETA["primaria"] if i < 3 else PALETA["neutro"] for i in range(len(top_produtos))]
bars = ax.barh(
    top_produtos["nome_produto"][::-1],
    top_produtos["receita"][::-1],
    color=cores_top[::-1],
    height=0.6,
    edgecolor="white",
)

for bar, val in zip(bars, top_produtos["receita"][::-1]):
    ax.text(
        bar.get_width() + 800,
        bar.get_y() + bar.get_height() / 2,
        f"R$ {val/1000:.0f}k",
        va="center",
        fontsize=9,
    )

ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax.set_title("Top 10 Produtos por Receita", fontweight="bold", pad=12)
ax.set_xlabel("Receita Total (R$)")

# legenda manual pra indicar o top 3
from matplotlib.patches import Patch
legenda = [
    Patch(color=PALETA["primaria"], label="Top 3"),
    Patch(color=PALETA["neutro"],   label="Demais"),
]
ax.legend(handles=legenda, loc="lower right", fontsize=9)

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "04_top_produtos.png"), bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 6. Distribuição por canal de venda

# %%
canal_agg = (
    df.groupby("canal")
    .agg(receita=("valor_total", "sum"), pedidos=("id_pedido", "count"))
    .reset_index()
    .sort_values("receita", ascending=False)
)

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# pizza — share de receita por canal
wedges, texts, autotexts = axes[0].pie(
    canal_agg["receita"],
    labels=canal_agg["canal"],
    autopct="%1.1f%%",
    colors=CORES_CAT,
    startangle=90,
    wedgeprops={"edgecolor": "white", "linewidth": 1.5},
)
for at in autotexts:
    at.set_fontsize(9)
axes[0].set_title("Share de Receita por Canal", fontweight="bold")

# barras — volume de pedidos por canal
axes[1].barh(
    canal_agg["canal"],
    canal_agg["pedidos"],
    color=CORES_CAT,
    height=0.5,
    edgecolor="white",
)
axes[1].set_title("Volume de Pedidos por Canal", fontweight="bold")

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "05_canais_venda.png"), bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 7. Heatmap — vendas por dia da semana × mês

# %%
pivot = (
    df.assign(
        dia_semana=df["data_pedido"].dt.dayofweek,
        mes_num=df["data_pedido"].dt.month,
    )
    .groupby(["dia_semana", "mes_num"])["valor_total"]
    .sum()
    .unstack(fill_value=0)
)

dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

pivot.index = dias[:len(pivot)]
pivot.columns = [meses[c - 1] for c in pivot.columns]

fig, ax = plt.subplots(figsize=(13, 4))
sns.heatmap(
    pivot,
    ax=ax,
    cmap="Blues",
    linewidths=0.4,
    cbar_kws={"label": "Receita (R$)"},
    annot=pivot.map(lambda x: f"{x/1000:.0f}k"),
    fmt="",
    annot_kws={"size": 8},
)
ax.set_title("Receita por Dia da Semana × Mês (2023–2024)", fontweight="bold", pad=12)
ax.set_xlabel("")
ax.set_ylabel("")
fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "06_heatmap_dia_mes.png"), bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 8. Resumo executivo dos insights

# %%
receita_total  = df["valor_total"].sum()
ticket_geral   = df.groupby("id_cliente")["valor_total"].sum().mean()
pedidos_total  = len(df)
clientes_ativos = df["id_cliente"].nunique()

print("=" * 55)
print("  RESUMO EXECUTIVO — INTELIGÊNCIA COMERCIAL")
print("=" * 55)
print(f"  Receita total (2023–2024):  R$ {receita_total:>12,.2f}")
print(f"  Total de pedidos válidos:   {pedidos_total:>12,}")
print(f"  Clientes únicos com compra: {clientes_ativos:>12,}")
print(f"  Ticket médio por cliente:   R$ {ticket_geral:>11,.2f}")
print(f"  Região líder:               {receita_regiao.iloc[0]['regiao']}")
print(f"  Canal principal:            {canal_agg.iloc[0]['canal']}")
print("=" * 55)
print(f"\nGráficos salvos em: {DIR_GRAFICOS}")
