"""
Dashboard Central — Inteligência Comercial:
Gera um único PNG (20×28") com todos os gráficos do projeto
organizados em seções: EDA → Produtos → RFM → Cohort
"""
import os
import warnings

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch
warnings.filterwarnings("ignore")
# ── paths ──────────────────────────────────────────────────────────────────────
def _achar_raiz(inicio: str, marcador: str = "requirements.txt") -> str:
    """
    Sobe a árvore de pastas até encontrar o arquivo marcador.
    Funciona independentemente de onde o script estiver.
    """
    atual = os.path.abspath(inicio)
    for _ in range(8):
        if os.path.isfile(os.path.join(atual, marcador)):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:   # chegou na raiz do sistema
            break
        atual = pai
    raise FileNotFoundError(
        f"Raiz do projeto não encontrada a partir de '{inicio}'.\n"
        f"Certifique-se de que '{marcador}' existe na pasta raiz do projeto."
    )

BASE = _achar_raiz(os.path.dirname(os.path.abspath(__file__)))
DIR_PROC = os.path.join(BASE, "dados", "processados")
DIR_OUT  = os.path.join(BASE, "dashboard")
os.makedirs(DIR_OUT, exist_ok=True)

# ── paleta ─────────────────────────────────────────────────────────────────────
P = {
    "bg":         "#0F172A",   # fundo escuro do header
    "card":       "#1E293B",   # cards do header
    "primary":    "#2563EB",
    "secondary":  "#7C3AED",
    "success":    "#059669",
    "warning":    "#D97706",
    "danger":     "#DC2626",
    "neutral":    "#64748B",
    "text_light": "#F1F5F9",
    "text_muted": "#94A3B8",
    "surface":    "#F8FAFC",
    "border":     "#E2E8F0",
    "section_bg": "#EFF6FF",
}
CATS = [P["primary"], P["secondary"], P["success"], P["warning"], P["danger"]]

sns.set_theme(style="white")
plt.rcParams.update({
    "font.family":       "sans-serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.titlesize":    11,
    "axes.labelsize":    9,
    "xtick.labelsize":   8,
    "ytick.labelsize":   8,
    "axes.titlepad":     10,
})

# ── carregar dados ─────────────────────────────────────────────────────────────
df       = pd.read_csv(os.path.join(DIR_PROC, "pedidos_analitico.csv"), encoding="utf-8-sig")
df_cli   = pd.read_csv(os.path.join(DIR_PROC, "clientes_limpos.csv"),   encoding="utf-8-sig")
df_rfm   = pd.read_csv(os.path.join(DIR_PROC, "rfm_clientes.csv"),      encoding="utf-8-sig")
df_cret  = pd.read_csv(os.path.join(DIR_PROC, "cohort_retencao.csv"),   encoding="utf-8-sig")
df_ltv   = pd.read_csv(os.path.join(DIR_PROC, "cohort_ltv.csv"),        encoding="utf-8-sig")
df_meta  = pd.read_csv(os.path.join(DIR_PROC, "meta_realizado.csv"),    encoding="utf-8-sig")

df["data_pedido"] = pd.to_datetime(df["data_pedido"])
df["ano_mes_dt"]  = df["data_pedido"].dt.to_period("M").dt.to_timestamp()

print("Dados carregados ✓")

# ── KPIs globais ───────────────────────────────────────────────────────────────
receita_total  = df["valor_total"].sum()
total_pedidos  = len(df)
ticket_medio   = df.groupby("id_cliente")["valor_total"].sum().mean()
margem_media   = df["margem_bruta"].mean()
clientes_uniq  = df["id_cliente"].nunique()
data_ref       = df["data_pedido"].max()
inativos       = df.groupby("id_cliente")["data_pedido"].max()
pct_inativos   = (inativos < data_ref - pd.Timedelta(days=90)).mean()
atingimento    = df_meta["realizado"].sum() / df_meta["meta_valor"].sum()

# ── figura principal ───────────────────────────────────────────────────────────
FIG_W, FIG_H = 20, 28
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=P["surface"])

# GridSpec: 12 linhas × 2 colunas
# alturas calibradas pra preencher bem os 28"
gs = gridspec.GridSpec(
    nrows=12, ncols=2,
    figure=fig,
    hspace=0.55,
    wspace=0.30,
    top=0.97, bottom=0.02,
    left=0.06, right=0.97,
    height_ratios=[2.2, 1.6, 0.25, 3.2, 3.0, 0.25, 3.4, 0.25, 3.2, 0.25, 4.8, 3.0],
)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER — fundo escuro, título + subtítulo
# ═══════════════════════════════════════════════════════════════════════════════
ax_header = fig.add_subplot(gs[0, :])
ax_header.set_facecolor(P["bg"])
ax_header.set_xlim(0, 1)
ax_header.set_ylim(0, 1)
ax_header.axis("off")

ax_header.text(0.5, 0.75, "🛒  Inteligência Comercial",
               ha="center", va="center", fontsize=26, fontweight="bold",
               color=P["text_light"], transform=ax_header.transAxes)
ax_header.text(0.5, 0.38, "Análise de Vendas & Clientes — Varejo E-commerce Brasil  |  Jan 2023 – Dez 2024",
               ha="center", va="center", fontsize=11,
               color=P["text_muted"], transform=ax_header.transAxes)
ax_header.text(0.5, 0.10, "Felipe Huff  ·  github.com/felipehuff610  ·  linkedin.com/in/felipe-huff-1b411327b",
               ha="center", va="center", fontsize=9,
               color="#475569", transform=ax_header.transAxes)

# borda inferior do header
ax_header.axhline(0, color=P["primary"], linewidth=3)

# ═══════════════════════════════════════════════════════════════════════════════
# KPI CARDS — 5 cartões na segunda linha
# ═══════════════════════════════════════════════════════════════════════════════
ax_kpi = fig.add_subplot(gs[1, :])
ax_kpi.set_facecolor(P["bg"])
ax_kpi.set_xlim(0, 1)
ax_kpi.set_ylim(0, 1)
ax_kpi.axis("off")

kpis = [
    ("Receita Total",    f"R$ {receita_total/1e6:.2f}M",  "2 anos",             P["primary"]),
    ("Pedidos Válidos",  f"{total_pedidos:,}",             "Entregues + trânsito", P["secondary"]),
    ("Ticket Médio",     f"R$ {ticket_medio:,.0f}",        "por cliente",        P["success"]),
    ("Margem Bruta",     f"{margem_media:.1%}",            "média geral",        P["warning"]),
    ("Atingimento Meta", f"{atingimento:.1%}",             "meta × realizado",   P["danger"] if atingimento < 0.8 else P["success"]),
]

card_w  = 0.175
card_gap = 0.01
x_start = (1 - (len(kpis) * card_w + (len(kpis)-1) * card_gap)) / 2

for i, (label, valor, sub, cor) in enumerate(kpis):
    x = x_start + i * (card_w + card_gap)
    # fundo do card
    rect = FancyBboxPatch((x, 0.08), card_w, 0.84,
                          boxstyle="round,pad=0.01",
                          facecolor=P["card"], edgecolor=cor,
                          linewidth=1.5, transform=ax_kpi.transAxes,
                          clip_on=False)
    ax_kpi.add_patch(rect)
    # barra colorida no topo do card
    top_bar = FancyBboxPatch((x, 0.87), card_w, 0.06,
                             boxstyle="round,pad=0.005",
                             facecolor=cor, edgecolor="none",
                             transform=ax_kpi.transAxes, clip_on=False)
    ax_kpi.add_patch(top_bar)

    cx = x + card_w / 2
    ax_kpi.text(cx, 0.62, valor, ha="center", va="center",
                fontsize=16, fontweight="bold", color=P["text_light"],
                transform=ax_kpi.transAxes)
    ax_kpi.text(cx, 0.35, label, ha="center", va="center",
                fontsize=8.5, color=P["text_muted"],
                transform=ax_kpi.transAxes)
    ax_kpi.text(cx, 0.16, sub, ha="center", va="center",
                fontsize=7.5, color="#475569",
                transform=ax_kpi.transAxes)


def section_label(ax, texto, cor=P["primary"]):
    """Rótulo de seção entre blocos."""
    ax.set_facecolor(P["section_bg"])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.0, 0.05), 1.0, 0.9,
                                boxstyle="round,pad=0.005",
                                facecolor=P["section_bg"], edgecolor=cor,
                                linewidth=1, transform=ax.transAxes))
    ax.text(0.02, 0.5, f"▌  {texto}", va="center", fontsize=10,
            fontweight="bold", color=cor, transform=ax.transAxes)


# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 1 — EDA
# ═══════════════════════════════════════════════════════════════════════════════
ax_s1 = fig.add_subplot(gs[2, :])
section_label(ax_s1, "ANÁLISE EXPLORATÓRIA DE DADOS", P["primary"])

# ── Receita mensal (largura total) ────────────────────────────────────────────
ax_rm = fig.add_subplot(gs[3, :])
rec_mensal = (df.groupby("ano_mes_dt")["valor_total"].sum()
              .reset_index().sort_values("ano_mes_dt"))
rec_mensal["ano"] = rec_mensal["ano_mes_dt"].dt.year

for ano, cor, lw in [(2023, P["neutral"], 1.8), (2024, P["primary"], 2.5)]:
    sub = rec_mensal[rec_mensal["ano"] == ano]
    ax_rm.fill_between(sub["ano_mes_dt"], sub["valor_total"], alpha=0.08, color=cor)
    ax_rm.plot(sub["ano_mes_dt"], sub["valor_total"],
               color=cor, linewidth=lw, marker="o", markersize=4,
               label=str(ano))

# destacar Black Friday
for _, row in rec_mensal[rec_mensal["ano_mes_dt"].dt.month == 11].iterrows():
    ax_rm.annotate("Black\nFriday", xy=(row["ano_mes_dt"], row["valor_total"]),
                   xytext=(0, 10), textcoords="offset points",
                   ha="center", fontsize=7, color=P["danger"], fontweight="bold")

ax_rm.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax_rm.set_title("Receita Mensal — Evolução 2023 vs 2024", fontweight="bold")
ax_rm.legend(title="Ano", frameon=False, fontsize=8)
ax_rm.set_xlabel("")
ax_rm.grid(axis="y", alpha=0.3, linewidth=0.5)

# ── Região (esquerda) + Canal (direita) ───────────────────────────────────────
ax_reg = fig.add_subplot(gs[4, 0])
rec_reg = (df.groupby("regiao")["valor_total"].sum()
           .sort_values(ascending=True).reset_index())
bars = ax_reg.barh(rec_reg["regiao"], rec_reg["valor_total"],
                   color=P["primary"], height=0.55, edgecolor="white")
for bar in bars:
    ax_reg.text(bar.get_width() + 1500, bar.get_y() + bar.get_height()/2,
                f"R$ {bar.get_width()/1000:.0f}k", va="center", fontsize=7.5)
ax_reg.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax_reg.set_title("Receita por Região", fontweight="bold")
ax_reg.set_xlabel("")

ax_can = fig.add_subplot(gs[4, 1])
rec_can = df.groupby("canal")["valor_total"].sum().reset_index().sort_values("valor_total", ascending=False)
ax_can.bar(rec_can["canal"], rec_can["valor_total"],
           color=CATS, width=0.55, edgecolor="white")
for i, (_, row) in enumerate(rec_can.iterrows()):
    ax_can.text(i, row["valor_total"] + 1500,
                f"R$ {row['valor_total']/1000:.0f}k",
                ha="center", fontsize=7.5)
ax_can.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax_can.set_title("Receita por Canal de Venda", fontweight="bold")
ax_can.tick_params(axis="x", labelsize=8)

# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 2 — PRODUTOS
# ═══════════════════════════════════════════════════════════════════════════════
ax_s2 = fig.add_subplot(gs[5, :])
section_label(ax_s2, "ANÁLISE DE PRODUTOS — CURVA ABC", P["secondary"])

ax_prod = fig.add_subplot(gs[6, 0])
top10 = (df.groupby("nome_produto")["valor_total"].sum()
         .nlargest(10).sort_values(ascending=True).reset_index())
cores_top = [P["primary"] if i >= 7 else P["neutral"] for i in range(len(top10))]
ax_prod.barh(top10["nome_produto"], top10["valor_total"],
             color=cores_top, height=0.6, edgecolor="white")
for i, (_, row) in enumerate(top10.iterrows()):
    ax_prod.text(row["valor_total"] + 200, i,
                 f"R$ {row['valor_total']/1000:.0f}k", va="center", fontsize=7)
ax_prod.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x/1000:.0f}k"))
ax_prod.set_title("Top 10 Produtos por Receita", fontweight="bold")
leg = [mpatches.Patch(color=P["primary"], label="Top 3"),
       mpatches.Patch(color=P["neutral"], label="Demais")]
ax_prod.legend(handles=leg, frameon=False, fontsize=8, loc="lower right")

ax_cat = fig.add_subplot(gs[6, 1])
rec_cat = (df.groupby("categoria")["valor_total"].sum()
           .sort_values(ascending=False).reset_index())
rec_cat["pct"] = rec_cat["valor_total"] / rec_cat["valor_total"].sum()
wedges, _, autotexts = ax_cat.pie(
    rec_cat["valor_total"], labels=rec_cat["categoria"],
    autopct="%1.1f%%", colors=CATS[:len(rec_cat)],
    startangle=90, wedgeprops={"edgecolor": "white", "linewidth": 1.5},
)
for at in autotexts:
    at.set_fontsize(8)
ax_cat.set_title("Share de Receita por Categoria", fontweight="bold")

# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 3 — RFM
# ═══════════════════════════════════════════════════════════════════════════════
ax_s3 = fig.add_subplot(gs[7, :])
section_label(ax_s3, "SEGMENTAÇÃO DE CLIENTES — RFM", P["success"])

ax_rfm_bar = fig.add_subplot(gs[8, 0])
dist_rfm = df_rfm["segmento_rfm"].value_counts().sort_values()
cores_rfm = {
    "Campeões":                P["primary"],
    "Clientes Fiéis":          P["secondary"],
    "Potencial de Crescimento":P["success"],
    "Regulares":               P["neutral"],
    "Em Risco":                P["warning"],
    "Hibernando":              "#F59E0B",
    "Perdidos":                P["danger"],
}
ax_rfm_bar.barh(
    dist_rfm.index, dist_rfm.values,
    color=[cores_rfm.get(s, P["neutral"]) for s in dist_rfm.index],
    height=0.6, edgecolor="white",
)
for i, (seg, val) in enumerate(dist_rfm.items()):
    ax_rfm_bar.text(val + 1, i, f"{val} clientes", va="center", fontsize=7.5)
ax_rfm_bar.set_title("Clientes por Segmento RFM", fontweight="bold")
ax_rfm_bar.set_xlabel("Número de clientes")

ax_scatter = fig.add_subplot(gs[8, 1])
sc = ax_scatter.scatter(
    df_rfm["recencia"], df_rfm["frequencia"],
    c=df_rfm["rfm_total"],
    s=df_rfm["monetario"] / 100,
    cmap="RdYlGn_r", alpha=0.55, edgecolors="none",
)
plt.colorbar(sc, ax=ax_scatter, label="Score RFM", shrink=0.8)
ax_scatter.set_xlabel("Recência (dias)")
ax_scatter.set_ylabel("Frequência (pedidos)")
ax_scatter.set_title("Recência × Frequência\n(tamanho = valor monetário)", fontweight="bold")

# ═══════════════════════════════════════════════════════════════════════════════
# SEÇÃO 4 — COHORT
# ═══════════════════════════════════════════════════════════════════════════════
ax_s4 = fig.add_subplot(gs[9, :])
section_label(ax_s4, "ANÁLISE DE COHORT — RETENÇÃO DE CLIENTES", P["warning"])

# ── Heatmap de retenção ───────────────────────────────────────────────────────
ax_heat = fig.add_subplot(gs[10, :])

pivot = df_cret.pivot_table(
    index="cohort_str", columns="mes_apos_aquisicao",
    values="taxa_retencao", fill_value=np.nan,
)
pivot.index = pd.to_datetime(pivot.index).strftime("%b/%y")

# máscara: esconder células além do possível para cada cohort
mask = pd.DataFrame(False, index=pivot.index, columns=pivot.columns)
max_mes = pivot.shape[1]
for i in range(len(pivot)):
    n_possiveis = max_mes - i
    if n_possiveis < max_mes:
        mask.iloc[i, n_possiveis:] = True

annot = pivot.map(lambda x: f"{x:.0%}" if pd.notna(x) and x > 0 else "")

sns.heatmap(
    pivot, ax=ax_heat,
    annot=annot, fmt="",
    cmap="Blues", vmin=0, vmax=0.6,
    linewidths=0.4, linecolor="#E2E8F0",
    cbar_kws={"label": "Taxa de Retenção", "shrink": 0.5},
    annot_kws={"size": 7.5},
    mask=mask,
)
meses_label = ["Mês 0\n(aquisição)"] + [f"Mês {m}" for m in range(1, max_mes)]
ax_heat.set_xticklabels(meses_label[:max_mes], rotation=45, ha="right", fontsize=8)
ax_heat.set_yticklabels(ax_heat.get_yticklabels(), rotation=0, fontsize=8)
ax_heat.set_title("Heatmap de Retenção por Cohort de Aquisição", fontweight="bold")
ax_heat.set_xlabel("Meses após a primeira compra")
ax_heat.set_ylabel("")

# ── Curva YoY + LTV ──────────────────────────────────────────────────────────
ax_curva = fig.add_subplot(gs[11, 0])
df_cret["ano"] = pd.to_datetime(df_cret["cohort_str"]).dt.year

for ano, cor, lbl in [(2023, P["neutral"], "2023"), (2024, P["primary"], "2024")]:
    grupo = (df_cret[df_cret["ano"] == ano]
             .groupby("mes_apos_aquisicao")["taxa_retencao"]
             .mean().reset_index())
    ax_curva.plot(grupo["mes_apos_aquisicao"], grupo["taxa_retencao"],
                  color=cor, linewidth=2.2, marker="o", markersize=4, label=lbl)
    std = (df_cret[df_cret["ano"] == ano]
           .groupby("mes_apos_aquisicao")["taxa_retencao"].std().reset_index())
    ax_curva.fill_between(
        grupo["mes_apos_aquisicao"],
        (grupo["taxa_retencao"] - std["taxa_retencao"]).clip(0),
        grupo["taxa_retencao"] + std["taxa_retencao"],
        color=cor, alpha=0.08,
    )

ax_curva.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
ax_curva.set_title("Curva de Retenção — 2023 vs 2024", fontweight="bold")
ax_curva.set_xlabel("Meses após aquisição")
ax_curva.set_ylabel("Retenção (%)")
ax_curva.legend(frameon=False, fontsize=8)
ax_curva.set_ylim(0, 1)

ax_ltv = fig.add_subplot(gs[11, 1])
df_ltv["ano"] = pd.to_datetime(df_ltv["cohort_str"]).dt.year
df_ltv["trimestre"] = pd.to_datetime(df_ltv["cohort_str"]).dt.to_period("Q").astype(str)

cohort_sizes = (df_cret[df_cret["mes_apos_aquisicao"] == 0]
                .set_index("cohort_str")["n_clientes"].to_dict())

cores_trim = [P["neutral"], P["warning"], P["success"],
              P["primary"], P["secondary"], "#0EA5E9", "#F43F5E", "#8B5CF6"]

for i, (trim, grupo) in enumerate(df_ltv.groupby("trimestre")):
    grupo = grupo.sort_values("mes_apos_aquisicao")
    # LTV acumulado médio por cliente do trimestre
    size = np.mean([cohort_sizes.get(c, 1) for c in grupo["cohort_str"].unique()])
    ltv_acum = grupo.groupby("mes_apos_aquisicao")["receita"].sum().cumsum() / size
    ax_ltv.plot(ltv_acum.index, ltv_acum.values,
                color=cores_trim[i % len(cores_trim)],
                linewidth=1.8, marker="o", markersize=3, label=trim)

ax_ltv.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
ax_ltv.set_title("LTV Médio Acumulado por Trimestre", fontweight="bold")
ax_ltv.set_xlabel("Meses após aquisição")
ax_ltv.set_ylabel("LTV médio (R$)")
ax_ltv.legend(title="Trimestre", frameon=False, fontsize=7, ncol=2)

# ── fundo geral dos eixos de análise ──────────────────────────────────────────
for ax in fig.get_axes():
    if ax not in [ax_header, ax_kpi, ax_s1, ax_s2, ax_s3, ax_s4]:
        ax.set_facecolor("white")

# ── salvar ────────────────────────────────────────────────────────────────────
output = os.path.join(DIR_OUT, "dashboard_central.png")
plt.savefig(output, dpi=150, bbox_inches="tight",
            facecolor=P["surface"], edgecolor="none")
print(f"\n✅ Dashboard salvo em: {output}")
print(f"   Resolução: {FIG_W*150:.0f} × {FIG_H*150:.0f} px")
