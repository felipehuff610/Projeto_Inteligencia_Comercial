# %% [markdown]
# # 04 · Análise de Cohort — Retenção de Clientes
# **Projeto:** Inteligência Comercial — Varejo E-commerce Brasil
# **Autor:** Felipe Huff | github.com/felipehuff610
#
# ---
#
# ## O que é análise de cohort?
#
# Cohort é um grupo de clientes que tiveram sua **primeira compra no mesmo mês**.
# A análise mede quantos desses clientes **voltaram a comprar** nos meses seguintes.
#
# Exemplo de leitura:
# > *"Dos clientes que compraram pela primeira vez em Janeiro/2023,
# > 28% voltaram a comprar no mês seguinte (mês 1), e 14% ainda compravam
# > 6 meses depois (mês 6)."*
#
# Isso responde perguntas que o RFM não consegue:
# - A retenção está melhorando ao longo do tempo?
# - Clientes adquiridos no Black Friday são piores do que os de períodos normais?
# - Qual mês de aquisição gerou os clientes mais fiéis?

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
DIR_GRAFICOS    = os.path.join(BASE, "dashboard", "graficos_cohort")
os.makedirs(DIR_GRAFICOS, exist_ok=True)

# paleta consistente com os outros notebooks
PALETA = {
    "primaria":   "#2563EB",
    "secundaria": "#7C3AED",
    "sucesso":    "#059669",
    "alerta":     "#D97706",
    "perigo":     "#DC2626",
    "neutro":     "#64748B",
}

sns.set_theme(style="white", font="sans-serif")
plt.rcParams.update({
    "figure.dpi":        150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
})

print("Setup concluído ✓")

# %% [markdown]
# ## 2. Carregamento e preparação

# %%
df = pd.read_csv(
    os.path.join(DIR_PROCESSADOS, "pedidos_analitico.csv"),
    encoding="utf-8-sig",
)
df["data_pedido"] = pd.to_datetime(df["data_pedido"])

# período do mês — vou trabalhar com mês/ano, não dia exato
# isso é crucial: agrupar por período, não por data exata
df["periodo_pedido"] = df["data_pedido"].dt.to_period("M")

print(f"Pedidos carregados: {len(df):,}")
print(f"Clientes únicos: {df['id_cliente'].nunique():,}")
print(f"Período: {df['periodo_pedido'].min()} → {df['periodo_pedido'].max()}")

# %% [markdown]
# ## 3. Construção da matriz de cohort
#
# A lógica em 3 passos:
# 1. Identificar o **mês de aquisição** de cada cliente (primeira compra)
# 2. Para cada pedido, calcular quantos meses se passaram desde a aquisição
# 3. Contar clientes únicos por (cohort, mês_relativo) e calcular taxa de retenção

# %%
# passo 1 — mês de aquisição por cliente
aquisicao = (
    df.groupby("id_cliente")["periodo_pedido"]
    .min()
    .reset_index()
    .rename(columns={"periodo_pedido": "cohort"})
)

# passo 2 — juntar com todos os pedidos e calcular mês relativo
df_cohort = df.merge(aquisicao, on="id_cliente", how="left")

# diferença em meses entre o pedido e a primeira compra
# .n retorna o número inteiro do intervalo de períodos
df_cohort["mes_relativo"] = (
    df_cohort["periodo_pedido"] - df_cohort["cohort"]
).apply(lambda x: x.n)

print(f"\nMês relativo — distribuição:")
print(df_cohort["mes_relativo"].value_counts().sort_index().head(10))

# passo 3 — contar clientes únicos por cohort e mês relativo
cohort_data = (
    df_cohort.groupby(["cohort", "mes_relativo"])["id_cliente"]
    .nunique()
    .reset_index()
    .rename(columns={"id_cliente": "n_clientes"})
)

# pivotar: linhas = cohort, colunas = mês relativo
cohort_pivot = cohort_data.pivot_table(
    index="cohort",
    columns="mes_relativo",
    values="n_clientes",
    fill_value=0,
)

# tamanho de cada cohort (coluna 0 = mês de aquisição)
cohort_size = cohort_pivot[0]

# taxa de retenção = clientes no mês N / clientes no mês 0
retention = cohort_pivot.divide(cohort_size, axis=0).round(4)

print(f"\nMatrix de retenção: {retention.shape[0]} cohorts × {retention.shape[1]} meses")
print(f"\nPrimeiras linhas da matrix de retenção:")
print((retention.iloc[:4, :7] * 100).round(1).to_string())

# %% [markdown]
# ## 4. Heatmap de Retenção — visual principal

# %%
# formatar o índice pra ficar legível no gráfico
retention.index = retention.index.strftime("%b/%y")
cohort_size.index = cohort_size.index.strftime("%b/%y")

# limitar a 13 meses (mês 0 ao 12) pra caber bem no gráfico
# cohorts mais recentes vão ter NaN nos meses que ainda não existem — normal
max_meses = min(13, retention.shape[1])
retention_plot = retention.iloc[:, :max_meses].copy()

# substituir 0.0 por NaN nos meses futuros (cohorts recentes)
# isso evita mostrar 0% pra períodos que simplesmente não aconteceram ainda
for i, cohort_label in enumerate(retention_plot.index):
    n_meses_possiveis = max_meses - i  # cohorts mais novos têm menos meses disponíveis
    if n_meses_possiveis < max_meses:
        retention_plot.iloc[i, n_meses_possiveis:] = np.nan

# anotações: mostrar % formatado, NaN como vazio
annot = retention_plot.map(
    lambda x: f"{x:.0%}" if pd.notna(x) and x > 0 else ""
)

fig, ax = plt.subplots(figsize=(16, 8))

sns.heatmap(
    retention_plot,
    ax=ax,
    annot=annot,
    fmt="",
    cmap="Blues",
    vmin=0,
    vmax=0.6,
    linewidths=0.5,
    linecolor="#E2E8F0",
    cbar_kws={"label": "Taxa de Retenção", "shrink": 0.6},
    annot_kws={"size": 8, "weight": "normal"},
    mask=retention_plot.isna(),
)

# adicionar o tamanho do cohort no eixo Y
labels_y = [
    f"{label}  (n={int(cohort_size.iloc[i])})"
    for i, label in enumerate(retention_plot.index)
]
ax.set_yticklabels(labels_y, rotation=0, fontsize=9)

# eixo X — renomear pra ficar mais claro
meses_label = ["Mês 0\n(aquisição)"] + [f"Mês {m}" for m in range(1, max_meses)]
ax.set_xticklabels(meses_label[:max_meses], rotation=45, ha="right", fontsize=9)

ax.set_title(
    "Retenção de Clientes por Cohort de Aquisição\n"
    "E-commerce Brasil — Jan/23 a Dez/24",
    fontweight="bold",
    pad=16,
    fontsize=14,
)
ax.set_xlabel("Meses após a primeira compra", labelpad=10)
ax.set_ylabel("Cohort (mês da 1ª compra)", labelpad=10)

# linha separando meses com sazonalidade forte (Nov = Black Friday)
for i, label in enumerate(retention_plot.index):
    if "Nov" in label:
        ax.axhline(y=i, color=PALETA["perigo"], linewidth=1.5, linestyle="--", alpha=0.6)
        ax.text(
            max_meses + 0.1, i + 0.5,
            "Black Friday",
            fontsize=7.5, color=PALETA["perigo"], va="center",
        )

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "01_heatmap_retencao.png"), bbox_inches="tight", dpi=150)
plt.show()
print("Heatmap salvo ✓")

# %% [markdown]
# ## 5. Curva de Retenção — evolução mês a mês
#
# O heatmap mostra o detalhe por cohort.
# A curva de retenção agrega tudo e mostra a **retenção média** da base —
# e compara 2023 vs 2024 pra ver se melhorou.

# %%
# recarregar sem o índice formatado (precisamos do período pra filtrar por ano)
df_cohort2 = df.merge(aquisicao, on="id_cliente", how="left")
df_cohort2["mes_relativo"] = (
    df_cohort2["periodo_pedido"] - df_cohort2["cohort"]
).apply(lambda x: x.n)

cohort_data2 = (
    df_cohort2.groupby(["cohort", "mes_relativo"])["id_cliente"]
    .nunique()
    .reset_index()
    .rename(columns={"id_cliente": "n_clientes"})
)

cohort_pivot2 = cohort_data2.pivot_table(
    index="cohort",
    columns="mes_relativo",
    values="n_clientes",
    fill_value=0,
)
cohort_size2 = cohort_pivot2[0]
retention2   = cohort_pivot2.divide(cohort_size2, axis=0)

# separar por ano de aquisição
cohorts_2023 = [c for c in retention2.index if c.year == 2023]
cohorts_2024 = [c for c in retention2.index if c.year == 2024]

retencao_media_2023 = retention2.loc[cohorts_2023].mean()
retencao_media_2024 = retention2.loc[cohorts_2024].mean()

fig, ax = plt.subplots(figsize=(12, 5))

meses = range(0, min(13, len(retencao_media_2023)))

ax.plot(
    list(meses),
    [retencao_media_2023.get(m, np.nan) for m in meses],
    color=PALETA["neutro"],
    linewidth=2.5,
    marker="o",
    markersize=6,
    label="Cohorts 2023",
)
ax.plot(
    list(meses),
    [retencao_media_2024.get(m, np.nan) for m in meses],
    color=PALETA["primaria"],
    linewidth=2.5,
    marker="o",
    markersize=6,
    label="Cohorts 2024",
)

# faixa de confiança — desvio padrão
for cohorts, cor, alpha in [
    (cohorts_2023, PALETA["neutro"], 0.08),
    (cohorts_2024, PALETA["primaria"], 0.10),
]:
    media = retention2.loc[cohorts].mean()
    std   = retention2.loc[cohorts].std()
    vals  = list(meses)
    ax.fill_between(
        vals,
        [(media.get(m, 0) - std.get(m, 0)) for m in vals],
        [(media.get(m, 0) + std.get(m, 0)) for m in vals],
        color=cor,
        alpha=alpha,
    )

ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
ax.set_xticks(list(meses))
ax.set_xticklabels([f"Mês {m}" for m in meses], fontsize=9)
ax.set_title(
    "Curva de Retenção Média — 2023 vs 2024",
    fontweight="bold",
    pad=12,
)
ax.set_xlabel("Meses após a primeira compra")
ax.set_ylabel("Taxa de retenção (%)")
ax.legend(frameon=False)
ax.set_ylim(0, 1.05)

# anotação da retenção no mês 1
for cohorts, cor, label, offset in [
    (cohorts_2023, PALETA["neutro"], "2023", -0.06),
    (cohorts_2024, PALETA["primaria"], "2024", +0.04),
]:
    val_m1 = retention2.loc[cohorts].mean().get(1, np.nan)
    if not np.isnan(val_m1):
        ax.annotate(
            f"{val_m1:.0%}",
            xy=(1, val_m1),
            xytext=(1, val_m1 + offset),
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=cor,
        )

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "02_curva_retencao_yoy.png"), bbox_inches="tight", dpi=150)
plt.show()

# %% [markdown]
# ## 6. Retenção por segmento de cliente
#
# Diamante e Ouro retêm mais? Ou a diferença é menor do que se imagina?

# %%
# juntar segmento ao dataframe de cohort
segmento_cliente = df[["id_cliente", "segmento"]].drop_duplicates("id_cliente")
df_seg = df_cohort2.merge(segmento_cliente, on="id_cliente", how="left", suffixes=("", "_drop")).rename(columns={"segmento_drop": "_drop_seg"}).pipe(lambda d: d.drop(columns=[c for c in d.columns if c.endswith("_drop")])) 
# already merged, use df with segmento
df_seg = df.merge(aquisicao, on="id_cliente", how="left")
df_seg["mes_relativo"] = (df_seg["data_pedido"].dt.to_period("M") - df_seg["cohort"]).apply(lambda x: x.n)
# df_seg = df_cohort2.merge(segmento_cliente, on="id_cliente", how="left")

cohort_seg = (
    df_seg.groupby(["segmento", "mes_relativo"])["id_cliente"]
    .nunique()
    .reset_index()
    .rename(columns={"id_cliente": "n_clientes"})
)

# tamanho de cada segmento no mês 0
size_seg = (
    cohort_seg[cohort_seg["mes_relativo"] == 0]
    .set_index("segmento")["n_clientes"]
)

fig, ax = plt.subplots(figsize=(12, 5))

cores_seg = {
    "Bronze":   PALETA["neutro"],
    "Prata":    PALETA["alerta"],
    "Ouro":     PALETA["sucesso"],
    "Diamante": PALETA["primaria"],
}

for segmento, grupo in cohort_seg.groupby("segmento"):
    grupo = grupo.sort_values("mes_relativo")
    meses_disp = grupo["mes_relativo"].tolist()
    retencao   = (grupo["n_clientes"] / size_seg[segmento]).tolist()

    ax.plot(
        meses_disp[:13],
        retencao[:13],
        color=cores_seg.get(segmento, "#888"),
        linewidth=2.2,
        marker="o",
        markersize=5,
        label=f"{segmento} (n={int(size_seg[segmento])})",
    )

ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
ax.set_xticks(range(0, 13))
ax.set_xticklabels([f"Mês {m}" for m in range(0, 13)], fontsize=9)
ax.set_title(
    "Retenção por Segmento de Cliente — Mês 0 ao Mês 12",
    fontweight="bold",
    pad=12,
)
ax.set_xlabel("Meses após a primeira compra")
ax.set_ylabel("Taxa de retenção (%)")
ax.legend(frameon=False, fontsize=9)
ax.set_ylim(0, 1.05)

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "03_retencao_por_segmento.png"), bbox_inches="tight", dpi=150)
plt.show()

# %% [markdown]
# ## 7. Receita por cohort — LTV acumulado
#
# Retenção conta cabeças. Mas o que realmente importa é:
# **quanto cada cohort gerou de receita ao longo do tempo?**
#
# Esse gráfico mostra o LTV (Lifetime Value) acumulado médio por cohort.

# %%
ltv_data = (
    df_cohort2.groupby(["cohort", "mes_relativo"])["valor_total"]
    .sum()
    .reset_index()
)

# LTV acumulado por cohort ao longo dos meses
ltv_pivot = ltv_data.pivot_table(
    index="cohort",
    columns="mes_relativo",
    values="valor_total",
    fill_value=0,
)

# acumular mes a mes
ltv_acum = ltv_pivot.cumsum(axis=1)

# normalizar por tamanho do cohort → LTV médio por cliente
ltv_medio = ltv_acum.divide(cohort_size2, axis=0)

# agrupar por trimestre de aquisição pra não poluir o gráfico
ltv_medio.index = pd.PeriodIndex(ltv_medio.index)
ltv_medio["trimestre"] = ltv_medio.index.to_timestamp().to_period("Q").astype(str)

ltv_trimestre = ltv_medio.groupby("trimestre").mean()

fig, ax = plt.subplots(figsize=(12, 5))

cores_trim = [PALETA["neutro"], PALETA["alerta"], PALETA["sucesso"],
              PALETA["primaria"], PALETA["secundaria"], "#0EA5E9", "#F43F5E", "#8B5CF6"]

for i, (trimestre, row) in enumerate(ltv_trimestre.iterrows()):
    vals_mes  = [m for m in range(13) if m in row.index and not np.isnan(row.get(m, np.nan))]
    vals_ltv  = [row.get(m, np.nan) for m in vals_mes]

    ax.plot(
        vals_mes,
        vals_ltv,
        color=cores_trim[i % len(cores_trim)],
        linewidth=2,
        marker="o",
        markersize=4,
        label=trimestre,
    )

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
ax.set_xticks(range(0, 13))
ax.set_xticklabels([f"Mês {m}" for m in range(0, 13)], fontsize=9)
ax.set_title(
    "LTV Médio Acumulado por Trimestre de Aquisição",
    fontweight="bold",
    pad=12,
)
ax.set_xlabel("Meses após a primeira compra")
ax.set_ylabel("LTV médio acumulado (R$)")
ax.legend(title="Trimestre", frameon=False, fontsize=9, ncol=2)

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "04_ltv_acumulado_cohort.png"), bbox_inches="tight", dpi=150)
plt.show()

# %% [markdown]
# ## 8. Resumo dos insights

# %%
# retenção geral no mês 1, 3 e 6
ret_m1 = float(retention2.mean().get(1, 0))
ret_m3 = float(retention2.mean().get(3, 0))
ret_m6 = float(retention2.mean().get(6, 0))

# melhor e pior cohort no mês 3
ret_m3_cohort = retention2[3].dropna().sort_values(ascending=False)
melhor_cohort = ret_m3_cohort.index[0].strftime("%b/%Y")
pior_cohort   = ret_m3_cohort.index[-1].strftime("%b/%Y")

# LTV médio no mês 12 pelo último trimestre com dados completos
try:
    ltv_m12 = ltv_medio[12].dropna().mean()
except KeyError:
    ltv_m12 = ltv_medio.iloc[:, -1].dropna().mean()

print("=" * 58)
print("  INSIGHTS — ANÁLISE DE COHORT")
print("=" * 58)
print(f"  Retenção mês 1  (30 dias):   {ret_m1:.1%}")
print(f"  Retenção mês 3  (90 dias):   {ret_m3:.1%}")
print(f"  Retenção mês 6 (180 dias):   {ret_m6:.1%}")
print(f"  Melhor cohort (mês 3):        {melhor_cohort}  ({ret_m3_cohort.iloc[0]:.1%})")
print(f"  Pior cohort   (mês 3):        {pior_cohort}  ({ret_m3_cohort.iloc[-1]:.1%})")
print(f"  LTV médio acum. (12 meses):  R$ {ltv_m12:,.2f}")
print("=" * 58)

# %% [markdown]
# ## 9. Salvar tabelas para o Power BI

# %%
# tabela de retenção em formato longo — ideal pra Power BI
retention_long = (
    cohort_data2
    .copy()
    .assign(
        cohort_str=lambda df: df["cohort"].dt.strftime("%Y-%m"),
        taxa_retencao=lambda df: df.apply(
            lambda row: row["n_clientes"] / cohort_size2.get(row["cohort"], 1),
            axis=1,
        ).round(4),
    )
    .rename(columns={"mes_relativo": "mes_apos_aquisicao"})
)

# LTV longo
ltv_long = (
    df_cohort2.groupby(["cohort", "mes_relativo"])["valor_total"]
    .sum()
    .reset_index()
    .assign(cohort_str=lambda df: df["cohort"].dt.strftime("%Y-%m"))
    .rename(columns={"mes_relativo": "mes_apos_aquisicao", "valor_total": "receita"})
)

retention_long.to_csv(
    os.path.join(DIR_PROCESSADOS, "cohort_retencao.csv"),
    index=False, encoding="utf-8-sig",
)
ltv_long.to_csv(
    os.path.join(DIR_PROCESSADOS, "cohort_ltv.csv"),
    index=False, encoding="utf-8-sig",
)

print("\nArquivos salvos:")
print(f"  ✓ cohort_retencao.csv  — {len(retention_long):,} registros")
print(f"  ✓ cohort_ltv.csv       — {len(ltv_long):,} registros")
print(f"\nGráficos em: {DIR_GRAFICOS}")
print("\n✅ Análise de cohort concluída!")
