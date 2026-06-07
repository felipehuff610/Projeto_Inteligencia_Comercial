# %% [markdown]
# # 03 · Métricas de Clientes — RFM, Inativos e Potencial de Crescimento
# **Projeto:** Inteligência Comercial — Varejo E-commerce Brasil  
# **Objetivo:** Segmentar a base de clientes e identificar oportunidades de receita.
#
# Perguntas que vamos responder aqui:
# - Quais clientes estão inativos (sem compra há mais de 90 dias)?
# - Qual o ticket médio por cliente e por segmento?
# - Quem tem potencial de crescimento mas ainda compra pouco?
# - RFM — quem são os clientes mais valiosos?

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
DIR_GRAFICOS    = os.path.join(BASE, "dashboard", "graficos_clientes")
os.makedirs(DIR_GRAFICOS, exist_ok=True)

PALETA = {
    "primaria":   "#2563EB",
    "secundaria": "#7C3AED",
    "sucesso":    "#059669",
    "alerta":     "#D97706",
    "perigo":     "#DC2626",
    "neutro":     "#64748B",
}
CORES_CAT = list(PALETA.values())

sns.set_theme(style="whitegrid", palette=CORES_CAT, font="sans-serif")
plt.rcParams.update({
    "figure.dpi":        150,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    13,
    "axes.labelsize":    11,
})

# %%
df_ped  = pd.read_csv(os.path.join(DIR_PROCESSADOS, "pedidos_analitico.csv"), encoding="utf-8-sig")
df_cli  = pd.read_csv(os.path.join(DIR_PROCESSADOS, "clientes_limpos.csv"),   encoding="utf-8-sig")

df_ped["data_pedido"] = pd.to_datetime(df_ped["data_pedido"])

# data de referência — usamos o último dia do dataset pra calcular recência
DATA_REF = df_ped["data_pedido"].max()
print(f"Data de referência (último pedido): {DATA_REF.strftime('%d/%m/%Y')}")

# %% [markdown]
# ## 2. Clientes inativos — sem compra há mais de 90 dias

# %%
ultima_compra = (
    df_ped.groupby("id_cliente")["data_pedido"]
    .max()
    .reset_index()
    .rename(columns={"data_pedido": "ultima_compra"})
)

ultima_compra["dias_sem_compra"] = (DATA_REF - ultima_compra["ultima_compra"]).dt.days

# definição: inativo = sem compra há mais de 90 dias
# poderia usar 60 ou 120 dependendo da frequência natural da categoria
LIMIAR_INATIVO = 90

clientes_inativos = ultima_compra[ultima_compra["dias_sem_compra"] > LIMIAR_INATIVO].copy()
clientes_inativos = clientes_inativos.merge(
    df_cli[["id_cliente", "nome_cliente" if "nome_cliente" in df_cli.columns else "nome",
            "segmento", "regiao", "email"]].rename(columns={"nome": "nome_cliente"}),
    on="id_cliente",
    how="left",
)

n_total    = df_cli["id_cliente"].nunique()
n_inativos = len(clientes_inativos)
print(f"\nClientes inativos (+{LIMIAR_INATIVO} dias): {n_inativos:,} de {n_total:,} ({n_inativos/n_total:.1%})")

# quais segmentos têm mais inativos?
inativos_por_segmento = (
    clientes_inativos.groupby("segmento").size()
    .reset_index(name="qtd_inativos")
    .sort_values("qtd_inativos", ascending=False)
)
print("\nInativos por segmento:")
print(inativos_por_segmento.to_string(index=False))

# %% [markdown]
# ## 3. Ticket médio por cliente e por segmento

# %%
receita_cliente = (
    df_ped.groupby("id_cliente")
    .agg(
        receita_total=("valor_total", "sum"),
        n_pedidos=("id_pedido", "count"),
        primeira_compra=("data_pedido", "min"),
        ultima_compra=("data_pedido", "max"),
    )
    .reset_index()
)
receita_cliente["ticket_medio"] = (receita_cliente["receita_total"] / receita_cliente["n_pedidos"]).round(2)

# juntar com segmento
receita_cliente = receita_cliente.merge(
    df_cli[["id_cliente", "segmento", "regiao"]],
    on="id_cliente",
    how="left",
)

print("\nTicket médio por segmento:")
ticket_segmento = (
    receita_cliente.groupby("segmento")["ticket_medio"]
    .agg(["mean", "median", "count"])
    .round(2)
    .rename(columns={"mean": "ticket_médio", "median": "mediana", "count": "clientes"})
    .sort_values("ticket_médio", ascending=False)
)
print(ticket_segmento.to_string())

# %% [markdown]
# ## 4. Análise RFM — Recência, Frequência, Valor Monetário

# %%
rfm = (
    df_ped.groupby("id_cliente")
    .agg(
        recencia=("data_pedido", lambda x: (DATA_REF - x.max()).days),
        frequencia=("id_pedido", "count"),
        monetario=("valor_total", "sum"),
    )
    .reset_index()
)

# scores de 1 a 5 usando quintis
# recência: quanto menor o número de dias, melhor → score invertido
rfm["score_r"] = pd.qcut(rfm["recencia"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
rfm["score_f"] = pd.qcut(rfm["frequencia"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
rfm["score_m"] = pd.qcut(rfm["monetario"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)

rfm["rfm_score"] = rfm["score_r"] * 100 + rfm["score_f"] * 10 + rfm["score_m"]
rfm["rfm_total"] = rfm["score_r"] + rfm["score_f"] + rfm["score_m"]


def classificar_rfm(row) -> str:
    r, f, m = row["score_r"], row["score_f"], row["score_m"]
    total = r + f + m

    if r >= 4 and f >= 4 and m >= 4:
        return "Campeões"
    elif r >= 4 and (f >= 3 or m >= 3):
        return "Clientes Fiéis"
    elif r >= 3 and f <= 2:
        return "Potencial de Crescimento"
    elif r <= 2 and f >= 4:
        return "Em Risco"
    elif r <= 2 and f <= 2 and m >= 3:
        return "Hibernando"
    elif total <= 5:
        return "Perdidos"
    else:
        return "Regulares"


rfm["segmento_rfm"] = rfm.apply(classificar_rfm, axis=1)

print("\nDistribuição de segmentos RFM:")
dist_rfm = rfm["segmento_rfm"].value_counts().reset_index()
dist_rfm.columns = ["segmento", "clientes"]
dist_rfm["pct"] = (dist_rfm["clientes"] / dist_rfm["clientes"].sum() * 100).round(1)
print(dist_rfm.to_string(index=False))

# %% [markdown]
# ## 5. Clientes com potencial de crescimento

# %%
# potencial = compra pouco (frequência baixa) mas tem bom ticket médio
# e a recência não é tão ruim (comprou nos últimos 180 dias)
potencial = rfm[
    (rfm["segmento_rfm"] == "Potencial de Crescimento") |
    (rfm["score_f"] <= 2) & (rfm["score_m"] >= 3) & (rfm["recencia"] <= 180)
].copy()

potencial = potencial.merge(
    df_cli[["id_cliente", "nome", "segmento", "email", "regiao"]],
    on="id_cliente",
    how="left",
)

print(f"\nClientes com potencial de crescimento: {len(potencial):,}")
print(f"Receita atual desse grupo: R$ {potencial['monetario'].sum():,.2f}")
print(f"Frequência média: {potencial['frequencia'].mean():.1f} pedidos")
print("\nTop 10 por valor monetário:")
print(
    potencial.nlargest(10, "monetario")[
        ["nome", "segmento", "regiao", "recencia", "frequencia", "monetario"]
    ].to_string(index=False)
)

# %% [markdown]
# ## 6. Visualizações RFM

# %%
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# distribuição dos segmentos RFM
cores_rfm = {
    "Campeões":               PALETA["primaria"],
    "Clientes Fiéis":         PALETA["secundaria"],
    "Potencial de Crescimento": PALETA["sucesso"],
    "Regulares":              PALETA["neutro"],
    "Em Risco":               PALETA["alerta"],
    "Hibernando":             "#F59E0B",
    "Perdidos":               PALETA["perigo"],
}

dist_rfm_sorted = rfm["segmento_rfm"].value_counts()
axes[0].barh(
    dist_rfm_sorted.index,
    dist_rfm_sorted.values,
    color=[cores_rfm.get(s, PALETA["neutro"]) for s in dist_rfm_sorted.index],
    height=0.6,
    edgecolor="white",
)
axes[0].set_title("Segmentação RFM — Base de Clientes", fontweight="bold")
axes[0].set_xlabel("Número de Clientes")

# scatter: recência × frequência, tamanho = valor monetário
scatter = axes[1].scatter(
    rfm["recencia"],
    rfm["frequencia"],
    c=rfm["rfm_total"],
    s=rfm["monetario"] / 80,
    cmap="RdYlGn_r",
    alpha=0.6,
    edgecolors="none",
)
axes[1].set_xlabel("Recência (dias desde última compra)")
axes[1].set_ylabel("Frequência (nº de pedidos)")
axes[1].set_title("RFM — Recência × Frequência\n(tamanho = valor monetário)", fontweight="bold")
plt.colorbar(scatter, ax=axes[1], label="Score RFM Total")

fig.tight_layout()
plt.savefig(os.path.join(DIR_GRAFICOS, "01_rfm_segmentacao.png"), bbox_inches="tight")
plt.show()

# %% [markdown]
# ## 7. Meta × Realizado por vendedor

# %%
df_metas = pd.read_csv(os.path.join(os.path.dirname(DIR_PROCESSADOS), "brutos", "metas.csv"), encoding="utf-8-sig")

# realizado por vendedor por mês
realizado = (
    df_ped.groupby(["id_vendedor", "ano", "mes"])["valor_total"]
    .sum()
    .reset_index()
    .rename(columns={"valor_total": "realizado"})
)

meta_real = df_metas.merge(realizado, on=["id_vendedor", "ano", "mes"], how="left").fillna(0)

# juntar nome do vendedor
vendedores = pd.read_csv(
    os.path.join(os.path.dirname(DIR_PROCESSADOS), "brutos", "vendedores.csv"),
    encoding="utf-8-sig"
)
meta_real = meta_real.merge(vendedores[["id_vendedor", "nome"]], on="id_vendedor")

# resumo anual
resumo_anual = (
    meta_real.groupby(["nome", "ano"])
    .agg(meta=("meta_valor", "sum"), realizado=("realizado", "sum"))
    .reset_index()
)
resumo_anual["atingimento"] = (resumo_anual["realizado"] / resumo_anual["meta"] * 100).round(1)
resumo_anual["gap"] = resumo_anual["realizado"] - resumo_anual["meta"]

print("\nMeta × Realizado por vendedor (2024):")
print(
    resumo_anual[resumo_anual["ano"] == 2024]
    .sort_values("atingimento", ascending=False)
    [["nome", "meta", "realizado", "atingimento", "gap"]]
    .to_string(index=False)
)

# %% [markdown]
# ## 8. Salvar tabelas finais

# %%
rfm.to_csv(os.path.join(DIR_PROCESSADOS, "rfm_clientes.csv"), index=False, encoding="utf-8-sig")
clientes_inativos.to_csv(os.path.join(DIR_PROCESSADOS, "clientes_inativos.csv"), index=False, encoding="utf-8-sig")
potencial.to_csv(os.path.join(DIR_PROCESSADOS, "clientes_potencial.csv"), index=False, encoding="utf-8-sig")
meta_real.to_csv(os.path.join(DIR_PROCESSADOS, "meta_realizado.csv"), index=False, encoding="utf-8-sig")

print("\nTabelas salvas:")
print(f"  ✓ rfm_clientes.csv          — {len(rfm):,} registros")
print(f"  ✓ clientes_inativos.csv     — {len(clientes_inativos):,} registros")
print(f"  ✓ clientes_potencial.csv    — {len(potencial):,} registros")
print(f"  ✓ meta_realizado.csv        — {len(meta_real):,} registros")
print(f"\nGráficos em: {DIR_GRAFICOS}")
print("\n✅ Análise de clientes concluída!")
