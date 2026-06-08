"""
Dashboard Interativo — Inteligência Comercial
=============================================
Interface navegável  |  Dark Neumorfismo  |  PyQt6 + Matplotlib

Dependências:
    pip install PyQt6 pandas matplotlib seaborn numpy

Como executar:
    python dashboard/app_dashboard.py

Autor: Felipe Huff | github.com/felipehuff610
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

# backend ANTES de qualquer import do pyplot
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QStackedWidget, QScrollArea, QMessageBox, QSplashScreen,
)
from PyQt6.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QFont, QLinearGradient, QPixmap,
)


# ══════════════════════════════════════════════════════════════════
#  PALETA — DARK NEUMORFISMO
# ══════════════════════════════════════════════════════════════════
BG       = "#1E2235"   # fundo base
CARD_BG  = "#252B42"   # superfície dos cards
SD_DARK  = "#141828"   # sombra escura
SD_LIGHT = "#2E3655"   # sombra clara / brilho
TEXT     = "#E2E8F0"   # texto principal
SUB      = "#8892B0"   # texto secundário
PRIM     = "#3B82F6"   # azul neon
SEC      = "#8B5CF6"   # roxo neon
SUCC     = "#10B981"   # verde neon
WARN     = "#F59E0B"   # âmbar
DANG     = "#EF4444"   # vermelho
ACCENT   = [PRIM, SEC, SUCC, WARN, DANG]

# matplotlib dark theme
plt.rcParams.update({
    "figure.facecolor":   BG,
    "axes.facecolor":     BG,
    "text.color":         TEXT,
    "axes.labelcolor":    SUB,
    "xtick.color":        SUB,
    "ytick.color":        SUB,
    "axes.edgecolor":     SD_LIGHT,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.color":         SD_LIGHT,
    "grid.alpha":         0.35,
    "grid.linewidth":     0.5,
    "axes.titlesize":     11,
    "axes.titlecolor":    TEXT,
    "axes.labelsize":     9,
    "xtick.labelsize":    8,
    "ytick.labelsize":    8,
    "legend.facecolor":   CARD_BG,
    "legend.edgecolor":   SD_LIGHT,
    "legend.labelcolor":  TEXT,
    "font.family":        "sans-serif",
})


# ══════════════════════════════════════════════════════════════════
#  HELPER — RAIZ DO PROJETO
# ══════════════════════════════════════════════════════════════════
def find_root(start, marker="requirements.txt"):
    atual = os.path.abspath(start)
    for _ in range(8):
        if os.path.isfile(os.path.join(atual, marker)):
            return atual
        pai = os.path.dirname(atual)
        if pai == atual:
            break
        atual = pai
    return os.path.abspath(start)

ROOT     = find_root(os.path.dirname(os.path.abspath(__file__)))
DIR_PROC = os.path.join(ROOT, "dados", "processados")


# ══════════════════════════════════════════════════════════════════
#  HELPERS MATPLOTLIB
# ══════════════════════════════════════════════════════════════════
def make_fig(figsize=(10, 4)):
    fig = Figure(figsize=figsize, facecolor=BG)
    fig.tight_layout()
    canvas = FigureCanvas(fig)
    canvas.setStyleSheet(f"background-color: {BG};")
    return fig, canvas

def fmt_r(x, _):
    if x >= 1_000_000:
        return f"R$ {x/1e6:.1f}M"
    if x >= 1_000:
        return f"R$ {x/1000:.0f}k"
    return f"R$ {x:.0f}"


# ══════════════════════════════════════════════════════════════════
#  DADOS
# ══════════════════════════════════════════════════════════════════
class DataStore:
    df = rfm = cret = ltv = meta = None
    loaded = False

    @classmethod
    def load(cls):
        if cls.loaded:
            return True
        try:
            cls.df   = pd.read_csv(os.path.join(DIR_PROC, "pedidos_analitico.csv"), encoding="utf-8-sig")
            cls.rfm  = pd.read_csv(os.path.join(DIR_PROC, "rfm_clientes.csv"),      encoding="utf-8-sig")
            cls.cret = pd.read_csv(os.path.join(DIR_PROC, "cohort_retencao.csv"),   encoding="utf-8-sig")
            cls.ltv  = pd.read_csv(os.path.join(DIR_PROC, "cohort_ltv.csv"),        encoding="utf-8-sig")
            cls.meta = pd.read_csv(os.path.join(DIR_PROC, "meta_realizado.csv"),    encoding="utf-8-sig")
            cls.df["data_pedido"] = pd.to_datetime(cls.df["data_pedido"])
            cls.df["ano_mes_dt"]  = cls.df["data_pedido"].dt.to_period("M").dt.to_timestamp()
            cls.loaded = True
            return True
        except FileNotFoundError:
            return False


# ══════════════════════════════════════════════════════════════════
#  WIDGETS DARK NEUMÓRFICOS
# ══════════════════════════════════════════════════════════════════

class NeuCard(QWidget):
    """Card dark neumórfico — dupla sombra via QPainter."""
    SH = 9

    def __init__(self, parent=None, radius=16):
        super().__init__(parent)
        self.radius = radius
        m = self.SH + 6
        self.setContentsMargins(m, m, m, m)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.SH
        r = QRectF(s, s, self.width() - 2 * s, self.height() - 2 * s)
        d = s * 0.8

        # sombra escura — baixo direita
        p.setBrush(QColor(SD_DARK))
        p.setPen(Qt.PenStyle.NoPen)
        p.setOpacity(0.95)
        p.drawRoundedRect(r.adjusted(d, d, d, d), self.radius, self.radius)

        # sombra clara (brilho) — cima esquerda
        p.setBrush(QColor(SD_LIGHT))
        p.setOpacity(0.50)
        p.drawRoundedRect(r.adjusted(-d, -d, -d, -d), self.radius, self.radius)

        # superfície principal
        p.setOpacity(1.0)
        p.setBrush(QColor(CARD_BG))
        p.drawRoundedRect(r, self.radius, self.radius)
        p.end()


class KPICard(NeuCard):
    """Card de KPI com barra neon e glow."""

    def __init__(self, label, value, sub="", color=PRIM, parent=None):
        super().__init__(parent, radius=18)
        self.lbl   = label
        self.val   = value
        self.sub   = sub
        self.color = color
        self.setMinimumSize(170, 120)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.SH
        r = QRectF(s, s, self.width() - 2 * s, self.height() - 2 * s)
        x0 = r.x() + 18

        # glow blob atrás da barra
        glow = QColor(self.color); glow.setAlpha(40)
        p.setBrush(glow); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(x0 - 4, r.y() + 9, 56, 10), 5, 5)

        # barra neon
        p.setBrush(QColor(self.color))
        p.drawRoundedRect(QRectF(x0, r.y() + 12, 48, 4), 2, 2)

        # label
        p.setPen(QColor(SUB))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(x0, r.y() + 26, r.width() - 36, 18),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self.lbl)

        # valor
        p.setPen(QColor(TEXT))
        p.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        p.drawText(QRectF(x0, r.y() + 46, r.width() - 36, 36),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                   self.val)

        # sub
        if self.sub:
            p.setPen(QColor(self.color))
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(QRectF(x0, r.y() + 84, r.width() - 36, 16),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       self.sub)
        p.end()


class NavButton(QWidget):
    """Botão de navegação — sem ícone, tipografia limpa, animação de hover."""
    clicked = pyqtSignal()

    # cores de texto: SUB → TEXT (interpolação no hover)
    _SUB_RGB  = (136, 146, 176)
    _TEXT_RGB = (226, 232, 240)

    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label_str    = label
        self._selected    = False
        self._hover_t     = 0.0          # 0.0 = frio, 1.0 = hover pleno
        self._target_t    = 0.0
        self._press_t     = 0.0          # 0→1 ao clicar, anima de volta

        self._timer = QTimer(self)
        self._timer.setInterval(10)      # ~100fps — animação suave
        self._timer.timeout.connect(self._tick)

        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_selected(self, v):
        self._selected = v
        self.update()

    def enterEvent(self, e):
        self._target_t = 1.0
        self._timer.start()

    def leaveEvent(self, e):
        self._target_t = 0.0
        self._timer.start()

    def mousePressEvent(self, e):
        self._press_t = 1.0
        self._timer.start()
        self.clicked.emit()

    def _tick(self):
        changed = False
        # hover fade
        diff = self._target_t - self._hover_t
        if abs(diff) > 0.01:
            self._hover_t += diff * 0.18
            changed = True
        else:
            self._hover_t = self._target_t

        # click flash decay
        if self._press_t > 0.01:
            self._press_t *= 0.75
            changed = True
        else:
            self._press_t = 0.0

        if not changed:
            self._timer.stop()
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = QRectF(10, 5, w - 20, h - 10)

        if self._selected:
            # fundo neumórfico escuro
            grad = QLinearGradient(r.topLeft(), r.bottomRight())
            grad.setColorAt(0.0, QColor("#191E36"))
            grad.setColorAt(1.0, QColor("#232B47"))
            p.setBrush(grad)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(r, 11, 11)

            # barra neon lateral
            p.setBrush(QColor(PRIM))
            p.drawRoundedRect(QRectF(10, 13, 3, h - 26), 2, 2)

            # halo azul suave
            halo = QColor(PRIM); halo.setAlpha(16)
            p.setBrush(halo)
            p.drawRoundedRect(r, 11, 11)

        else:
            # hover background animado
            if self._hover_t > 0.005:
                bg = QColor(255, 255, 255)
                bg.setAlpha(int(14 * self._hover_t))
                p.setBrush(bg)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(r, 11, 11)

            # flash de clique
            if self._press_t > 0.005:
                flash = QColor(PRIM)
                flash.setAlpha(int(30 * self._press_t))
                p.setBrush(flash)
                p.setPen(Qt.PenStyle.NoPen)
                p.drawRoundedRect(r, 11, 11)

        # texto com cor interpolada
        if self._selected:
            tc = QColor(TEXT)
        else:
            sr, sg, sb = self._SUB_RGB
            tr, tg, tb = self._TEXT_RGB
            t = self._hover_t
            tc = QColor(int(sr + (tr-sr)*t), int(sg + (tg-sg)*t), int(sb + (tb-sb)*t))

        wt = QFont.Weight.DemiBold if self._selected else QFont.Weight.Normal
        p.setFont(QFont("Segoe UI", 10, wt))
        p.setPen(tc)
        p.drawText(QRectF(24, 0, w - 36, h), Qt.AlignmentFlag.AlignVCenter, self.label_str)
        p.end()


class SectionTitle(QLabel):
    def __init__(self, text, color=PRIM, parent=None):
        super().__init__(text, parent)
        self.setFont(QFont("Segoe UI", 13, QFont.Weight.DemiBold))
        self.setStyleSheet(f"color: {color}; background: transparent; padding: 2px 0 8px 0;")


def chart_card(canvas, title="", height=300):
    """NeuCard embrulhando um FigureCanvas."""
    card = NeuCard(radius=14)
    lay  = QVBoxLayout(card)
    lay.setContentsMargins(4, 4, 4, 4)
    lay.setSpacing(6)
    if title:
        lbl = QLabel(title)
        lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        lbl.setStyleSheet(f"color: {SUB}; background: transparent;")
        lay.addWidget(lbl)
    canvas.setMinimumHeight(height)
    lay.addWidget(canvas)
    return card


def scroll_page(widget):
    sa = QScrollArea()
    sa.setWidget(widget)
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.Shape.NoFrame)
    sa.setStyleSheet(f"background-color: {BG}; border: none;")
    sa.verticalScrollBar().setStyleSheet(f"""
        QScrollBar:vertical {{ background: {BG}; width: 6px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {SD_LIGHT}; border-radius: 3px; min-height: 30px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """)
    return sa


# ══════════════════════════════════════════════════════════════════
#  PÁGINAS DE CONTEÚDO
# ══════════════════════════════════════════════════════════════════

class PageOverview(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(18)

        df   = DataStore.df
        meta = DataStore.meta

        data_ref   = df["data_pedido"].max()
        inativos   = (df.groupby("id_cliente")["data_pedido"].max() < data_ref - pd.Timedelta(days=90)).mean()
        atingimento = meta["realizado"].sum() / meta["meta_valor"].sum()

        # ── KPIs ──────────────────────────────────────────────────
        kpis = [
            ("Receita Total",     f"R$ {df['valor_total'].sum()/1e6:.2f}M",   "Jan 2023 – Dez 2024",  PRIM),
            ("Pedidos Válidos",   f"{len(df):,}",                             "Entregues + trânsito", SEC),
            ("Ticket Médio",      f"R$ {df.groupby('id_cliente')['valor_total'].sum().mean():,.0f}",
                                                                               "por cliente",          SUCC),
            ("Margem Bruta",      f"{df['margem_bruta'].mean():.1%}",         "média geral",          WARN),
            ("Inativos (+90d)",   f"{inativos:.1%}",                          "da base de clientes",  DANG),
        ]
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(14)
        for lbl, val, sub, cor in kpis:
            kpi_row.addWidget(KPICard(lbl, val, sub, cor))
        lay.addLayout(kpi_row)

        # ── Receita mensal (full width) ───────────────────────────
        fig1, cv1 = make_fig((13, 3.4))
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.12)
        for ano, cor, lw in [(2023, SUB, 1.6), (2024, PRIM, 2.4)]:
            sub_df = df[df["data_pedido"].dt.year == ano] \
                     .groupby("ano_mes_dt")["valor_total"].sum().reset_index()
            ax1.fill_between(sub_df["ano_mes_dt"], sub_df["valor_total"], alpha=0.08, color=cor)
            ax1.plot(sub_df["ano_mes_dt"], sub_df["valor_total"],
                     color=cor, lw=lw, marker="o", markersize=4, label=str(ano))
        bf_data = df[df["data_pedido"].dt.month == 11].groupby("ano_mes_dt")["valor_total"].sum()
        for dt_val, v in bf_data.items():
            ax1.annotate("▲ BF", xy=(dt_val, v), xytext=(0, 10),
                         textcoords="offset points", ha="center",
                         fontsize=7, color=DANG, fontweight="bold")
        ax1.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_r))
        ax1.set_title("Receita Mensal — 2023 vs 2024  (▲ BF = Black Friday)",
                      color=TEXT, fontweight="bold")
        ax1.legend(frameon=False, fontsize=9)
        for sp in ax1.spines.values(): sp.set_color(SD_LIGHT)
        lay.addWidget(chart_card(cv1, height=270))

        # ── Linha inferior: região + atingimento de meta ──────────
        row2 = QHBoxLayout(); row2.setSpacing(14)

        fig2, cv2 = make_fig((6, 3.2))
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.30, right=0.96, top=0.88, bottom=0.10)
        reg = df.groupby("regiao")["valor_total"].sum().sort_values(ascending=True)
        bar_colors = [PRIM if i == len(reg) - 1 else SUB for i in range(len(reg))]
        ax2.barh(reg.index, reg.values, color=bar_colors, height=0.55, edgecolor="none")
        for i, v in enumerate(reg.values):
            ax2.text(v * 1.01, i, f"R$ {v/1000:.0f}k", va="center", fontsize=8, color=TEXT)
        ax2.set_title("Receita por Região", color=TEXT, fontweight="bold")
        ax2.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_r))
        for sp in ax2.spines.values(): sp.set_color(SD_LIGHT)
        row2.addWidget(chart_card(cv2, height=255))

        fig3, cv3 = make_fig((7.5, 3.2))
        ax3 = fig3.add_subplot(111)
        fig3.subplots_adjust(left=0.28, right=0.96, top=0.88, bottom=0.12)
        by_v = meta.groupby("nome").agg(
            meta_t=("meta_valor", "sum"), real_t=("realizado", "sum")
        ).reset_index()
        by_v["pct"] = (by_v["real_t"] / by_v["meta_t"] * 100).round(1)
        by_v = by_v.sort_values("pct", ascending=True)
        bar_c = [SUCC if x >= 100 else (WARN if x >= 80 else DANG) for x in by_v["pct"]]
        ax3.barh(by_v["nome"], by_v["pct"], color=bar_c, height=0.55, edgecolor="none")
        ax3.axvline(100, color=SUB, linestyle="--", lw=1, alpha=0.7)
        for i, v in enumerate(by_v["pct"]):
            ax3.text(v + 0.5, i, f"{v:.0f}%", va="center", fontsize=8, color=TEXT)
        ax3.set_title("Atingimento de Meta por Vendedor (%)", color=TEXT, fontweight="bold")
        for sp in ax3.spines.values(): sp.set_color(SD_LIGHT)
        row2.addWidget(chart_card(cv3, height=255))

        lay.addLayout(row2)
        lay.addStretch()


class PageEDA(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(18)

        df = DataStore.df
        lay.addWidget(SectionTitle("Análise Exploratória de Vendas"))

        # heatmap dia × mês
        fig1, cv1 = make_fig((13, 4))
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.07, right=0.98, top=0.88, bottom=0.15)
        pivot = df.assign(
            ds=df["data_pedido"].dt.dayofweek,
            ms=df["data_pedido"].dt.month,
        ).groupby(["ds", "ms"])["valor_total"].sum().unstack(fill_value=0)
        pivot.index = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][:len(pivot)]
        pivot.columns = ["Jan","Fev","Mar","Abr","Mai","Jun",
                         "Jul","Ago","Set","Out","Nov","Dez"][:len(pivot.columns)]
        sns.heatmap(pivot, ax=ax1, cmap="Blues", linewidths=0.3, linecolor=BG,
                    annot=pivot.map(lambda x: f"{x/1000:.0f}k"), fmt="",
                    annot_kws={"size": 8, "color": "#0F172A"},
                    cbar_kws={"label": "Receita (R$)", "shrink": 0.7})
        ax1.set_title("Receita por Dia da Semana × Mês", color=TEXT, fontweight="bold")
        ax1.tick_params(colors=SUB)
        lay.addWidget(chart_card(cv1, height=290))

        # canal + categoria
        row2 = QHBoxLayout(); row2.setSpacing(14)

        fig2, cv2 = make_fig((6, 3.8))
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.05, right=0.95, top=0.88, bottom=0.05)
        can = df.groupby("canal")["valor_total"].sum().sort_values(ascending=False)
        wedges, _, autotexts = ax2.pie(
            can.values, labels=can.index, autopct="%1.1f%%",
            colors=ACCENT[:len(can)], startangle=90,
            wedgeprops={"edgecolor": BG, "linewidth": 2},
        )
        for at in autotexts: at.set_fontsize(8); at.set_color(TEXT)
        ax2.set_title("Share por Canal de Venda", color=TEXT, fontweight="bold")
        row2.addWidget(chart_card(cv2, height=300))

        fig3, cv3 = make_fig((7.5, 3.8))
        ax3 = fig3.add_subplot(111)
        fig3.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.14)
        cat = df.groupby("categoria").agg(
            receita=("valor_total", "sum"),
            margem=("margem_bruta", "mean"),
        ).reset_index().sort_values("receita", ascending=True)
        bars = ax3.barh(cat["categoria"], cat["receita"],
                        color=ACCENT[:len(cat)], height=0.55, edgecolor="none")
        ax3.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_r))
        ax3.set_title("Receita por Categoria  (margem % no rótulo)", color=TEXT, fontweight="bold")
        for bar, (_, row) in zip(bars, cat.iterrows()):
            ax3.text(bar.get_width() * 1.01, bar.get_y() + bar.get_height() / 2,
                     f"{row['margem']:.0%} mg", va="center", fontsize=8, color=TEXT)
        for sp in ax3.spines.values(): sp.set_color(SD_LIGHT)
        row2.addWidget(chart_card(cv3, height=300))

        lay.addLayout(row2)
        lay.addStretch()


class PageProdutos(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(18)

        df = DataStore.df
        lay.addWidget(SectionTitle("Análise de Produtos — Curva ABC"))

        row1 = QHBoxLayout(); row1.setSpacing(14)

        # top 10
        fig1, cv1 = make_fig((8, 5))
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.34, right=0.96, top=0.90, bottom=0.10)
        t10 = df.groupby("nome_produto")["valor_total"].sum().nlargest(10).sort_values(ascending=True)
        cores = [PRIM if i >= 7 else SUB for i in range(len(t10))]
        ax1.barh(t10.index, t10.values, color=cores, height=0.6, edgecolor="none")
        for i, v in enumerate(t10.values):
            ax1.text(v * 1.01, i, f"R$ {v/1000:.0f}k", va="center", fontsize=7.5, color=TEXT)
        ax1.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_r))
        ax1.set_title("Top 10 Produtos por Receita", color=TEXT, fontweight="bold")
        for sp in ax1.spines.values(): sp.set_color(SD_LIGHT)
        from matplotlib.patches import Patch
        ax1.legend(handles=[Patch(color=PRIM, label="Top 3"),
                             Patch(color=SUB,  label="Demais")],
                   frameon=False, fontsize=8, loc="lower right")
        row1.addWidget(chart_card(cv1, height=380))

        right_col = QVBoxLayout(); right_col.setSpacing(14)

        # desconto médio por produto (top 8)
        fig2, cv2 = make_fig((5.5, 2.8))
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.38, right=0.96, top=0.88, bottom=0.12)
        desc = (df.groupby("nome_produto")["desconto_perc"].mean() * 100).nlargest(8).sort_values(ascending=True)
        ax2.barh(desc.index, desc.values, color=WARN, height=0.55, edgecolor="none")
        for i, v in enumerate(desc.values):
            ax2.text(v + 0.1, i, f"{v:.1f}%", va="center", fontsize=7.5, color=TEXT)
        ax2.set_title("Maior Desconto Médio por Produto", color=TEXT, fontweight="bold")
        for sp in ax2.spines.values(): sp.set_color(SD_LIGHT)
        right_col.addWidget(chart_card(cv2, height=240))

        # unidades vendidas por categoria
        fig3, cv3 = make_fig((5.5, 2.6))
        ax3 = fig3.add_subplot(111)
        fig3.subplots_adjust(left=0.20, right=0.96, top=0.88, bottom=0.12)
        un = df.groupby("categoria")["quantidade"].sum().sort_values(ascending=True)
        ax3.barh(un.index, un.values, color=SEC, height=0.5, edgecolor="none")
        for i, v in enumerate(un.values):
            ax3.text(v + 5, i, f"{v:,}", va="center", fontsize=8, color=TEXT)
        ax3.set_title("Unidades Vendidas por Categoria", color=TEXT, fontweight="bold")
        for sp in ax3.spines.values(): sp.set_color(SD_LIGHT)
        right_col.addWidget(chart_card(cv3, height=220))

        row1.addLayout(right_col)
        lay.addLayout(row1)
        lay.addStretch()


class PageRFM(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(18)

        df  = DataStore.df
        rfm = DataStore.rfm
        lay.addWidget(SectionTitle("Segmentação de Clientes — RFM"))

        cores_rfm = {
            "Campeões":                  PRIM,
            "Clientes Fiéis":            SEC,
            "Potencial de Crescimento":  SUCC,
            "Regulares":                 SUB,
            "Em Risco":                  WARN,
            "Hibernando":                "#F59E0B",
            "Perdidos":                  DANG,
        }

        # row 1: barras + scatter
        row1 = QHBoxLayout(); row1.setSpacing(14)

        fig1, cv1 = make_fig((6.5, 4))
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.28, right=0.96, top=0.88, bottom=0.10)
        dist = rfm["segmento_rfm"].value_counts().sort_values()
        ax1.barh(dist.index, dist.values,
                 color=[cores_rfm.get(s, SUB) for s in dist.index],
                 height=0.6, edgecolor="none")
        for i, v in enumerate(dist.values):
            ax1.text(v + 0.3, i, str(v), va="center", fontsize=8, color=TEXT)
        ax1.set_title("Clientes por Segmento RFM", color=TEXT, fontweight="bold")
        for sp in ax1.spines.values(): sp.set_color(SD_LIGHT)
        row1.addWidget(chart_card(cv1, height=320))

        fig2, cv2 = make_fig((7.5, 4))
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.10, right=0.88, top=0.88, bottom=0.12)
        sc = ax2.scatter(rfm["recencia"], rfm["frequencia"],
                         c=rfm["rfm_total"], s=rfm["monetario"] / 80,
                         cmap="cool", alpha=0.65, edgecolors="none")
        fig2.colorbar(sc, ax=ax2, label="Score RFM")
        ax2.set_xlabel("Recência (dias)"); ax2.set_ylabel("Frequência (pedidos)")
        ax2.set_title("Recência × Frequência\n(tamanho = valor monetário)", color=TEXT, fontweight="bold")
        for sp in ax2.spines.values(): sp.set_color(SD_LIGHT)
        row1.addWidget(chart_card(cv2, height=320))
        lay.addLayout(row1)

        # ticket por segmento
        fig3, cv3 = make_fig((13, 3))
        ax3 = fig3.add_subplot(111)
        fig3.subplots_adjust(left=0.04, right=0.98, top=0.85, bottom=0.22)
        merged = df.merge(rfm[["id_cliente", "segmento_rfm"]], on="id_cliente", how="left")
        tick = merged.groupby("segmento_rfm")["valor_total"].mean().sort_values(ascending=False)
        ax3.bar(tick.index, tick.values,
                color=[cores_rfm.get(s, SUB) for s in tick.index],
                width=0.55, edgecolor="none")
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:.0f}"))
        ax3.set_title("Ticket Médio por Segmento RFM", color=TEXT, fontweight="bold")
        plt.setp(ax3.get_xticklabels(), rotation=22, ha="right", fontsize=8)
        for sp in ax3.spines.values(): sp.set_color(SD_LIGHT)
        lay.addWidget(chart_card(cv3, height=240))
        lay.addStretch()


class PageCohort(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 22, 28, 22)
        lay.setSpacing(18)

        cret = DataStore.cret
        ltv  = DataStore.ltv
        lay.addWidget(SectionTitle("Análise de Cohort — Retenção & LTV"))

        # heatmap full width
        fig1, cv1 = make_fig((14, 5.5))
        ax1 = fig1.add_subplot(111)
        fig1.subplots_adjust(left=0.10, right=0.96, top=0.92, bottom=0.16)
        pivot = cret.pivot_table(index="cohort_str", columns="mes_apos_aquisicao",
                                  values="taxa_retencao", fill_value=np.nan)
        try:
            pivot.index = pd.to_datetime(pivot.index).strftime("%b/%y")
        except Exception:
            pass
        n_cols = pivot.shape[1]
        mask = pd.DataFrame(False, index=pivot.index, columns=pivot.columns)
        for i in range(len(pivot)):
            avail = n_cols - i
            if avail < n_cols:
                mask.iloc[i, avail:] = True
        ann = pivot.map(lambda x: f"{x:.0%}" if pd.notna(x) and x > 0 else "")
        sns.heatmap(pivot, ax=ax1, annot=ann, fmt="", cmap="Blues",
                    vmin=0, vmax=0.6, linewidths=0.35, linecolor=BG,
                    cbar_kws={"label": "Taxa de Retenção", "shrink": 0.55},
                    annot_kws={"size": 8.5, "color": "#0F172A"}, mask=mask)
        xticklabels = (["Mês 0\n(aquisição)"] +
                       [f"Mês {m}" for m in range(1, n_cols)])[:n_cols]
        ax1.set_xticklabels(xticklabels, rotation=40, ha="right", fontsize=8)
        ax1.set_yticklabels(ax1.get_yticklabels(), rotation=0, fontsize=8.5)
        ax1.set_title("Heatmap de Retenção por Cohort de Aquisição", color=TEXT, fontweight="bold")
        ax1.set_xlabel(""); ax1.set_ylabel("")
        lay.addWidget(chart_card(cv1, height=420))

        # curva YoY + LTV
        row2 = QHBoxLayout(); row2.setSpacing(14)

        fig2, cv2 = make_fig((6.5, 3.4))
        ax2 = fig2.add_subplot(111)
        fig2.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.14)
        cret2 = cret.copy()
        cret2["ano"] = pd.to_datetime(cret2["cohort_str"]).dt.year
        for ano, cor, lbl in [(2023, SUB, "2023"), (2024, PRIM, "2024")]:
            g   = cret2[cret2["ano"]==ano].groupby("mes_apos_aquisicao")["taxa_retencao"].mean()
            std = cret2[cret2["ano"]==ano].groupby("mes_apos_aquisicao")["taxa_retencao"].std()
            ax2.plot(g.index, g.values, color=cor, lw=2.3, marker="o", markersize=4, label=lbl)
            ax2.fill_between(g.index, (g - std).clip(0), g + std, color=cor, alpha=0.09)
        ax2.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
        ax2.set_ylim(0, 1.02)
        ax2.set_xlabel("Meses após aquisição")
        ax2.set_title("Curva de Retenção — 2023 vs 2024", color=TEXT, fontweight="bold")
        ax2.legend(frameon=False, fontsize=9)
        for sp in ax2.spines.values(): sp.set_color(SD_LIGHT)
        row2.addWidget(chart_card(cv2, height=270))

        fig3, cv3 = make_fig((7.5, 3.4))
        ax3 = fig3.add_subplot(111)
        fig3.subplots_adjust(left=0.12, right=0.97, top=0.88, bottom=0.14)
        ltv2 = ltv.copy()
        ltv2["trim"] = pd.to_datetime(ltv2["cohort_str"]).dt.to_period("Q").astype(str)
        sizes = cret[cret["mes_apos_aquisicao"] == 0].set_index("cohort_str")["n_clientes"].to_dict()
        pal   = [PRIM, SEC, SUCC, WARN, DANG, "#0EA5E9", "#F43F5E", "#A78BFA"]
        for i, (trim, g) in enumerate(ltv2.groupby("trim")):
            g   = g.sort_values("mes_apos_aquisicao")
            sz  = np.mean([sizes.get(c, 1) for c in g["cohort_str"].unique()])
            acc = g.groupby("mes_apos_aquisicao")["receita"].sum().cumsum() / max(sz, 1)
            ax3.plot(acc.index, acc.values, color=pal[i % len(pal)],
                     lw=1.9, marker="o", markersize=3, label=trim)
        ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"R$ {x:,.0f}"))
        ax3.set_xlabel("Meses após aquisição")
        ax3.set_title("LTV Médio Acumulado por Trimestre", color=TEXT, fontweight="bold")
        ax3.legend(title="Trimestre", frameon=False, fontsize=7.5, ncol=2)
        for sp in ax3.spines.values(): sp.set_color(SD_LIGHT)
        row2.addWidget(chart_card(cv3, height=270))

        lay.addLayout(row2)
        lay.addStretch()


# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
class Sidebar(QWidget):
    page_changed = pyqtSignal(int)

    PAGES = [
        "Visão Geral",
        "Análise de Vendas",
        "Produtos",
        "Clientes / RFM",
        "Cohort",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(228)
        self.setStyleSheet(f"background-color: {BG};")
        self.buttons: list[NavButton] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 22, 12, 22)
        lay.setSpacing(0)

        # logo card
        logo = NeuCard(radius=14)
        logo.setFixedHeight(84)
        ll = QVBoxLayout(logo)
        ll.setContentsMargins(0, 0, 0, 0)
        t1 = QLabel("Inteligência")
        t1.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        t1.setStyleSheet(f"color: {TEXT}; background: transparent;")
        t2 = QLabel("Comercial")
        t2.setFont(QFont("Segoe UI", 10))
        t2.setStyleSheet(f"color: {PRIM}; background: transparent;")
        ll.addWidget(t1); ll.addWidget(t2)
        lay.addWidget(logo)

        lay.addSpacing(22)

        # divisor
        div = QLabel("N A V E G A Ç Ã O")
        div.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
        div.setStyleSheet(f"color: {SUB}; background: transparent; padding-left: 16px; letter-spacing: 2px;")
        lay.addWidget(div)
        lay.addSpacing(6)

        # botões de navegação
        for i, lbl in enumerate(self.PAGES):
            btn = NavButton(lbl)
            btn.clicked.connect(lambda _=False, idx=i: self._select(idx))
            self.buttons.append(btn)
            lay.addWidget(btn)

        lay.addStretch()

        # linha separadora
        sep = QFrame(); sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {SD_LIGHT};")
        lay.addWidget(sep)
        lay.addSpacing(12)

        # rodapé
        foot = QLabel("Felipe Huff\ngithub.com/felipehuff610")
        foot.setFont(QFont("Segoe UI", 8))
        foot.setAlignment(Qt.AlignmentFlag.AlignLeft)
        foot.setStyleSheet(f"color: {SUB}; background: transparent; padding-left: 16px;")
        lay.addWidget(foot)

        self._select(0)

    def _select(self, idx: int):
        for i, btn in enumerate(self.buttons):
            btn.set_selected(i == idx)
        self.page_changed.emit(idx)


# ══════════════════════════════════════════════════════════════════
#  JANELA PRINCIPAL
# ══════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    PAGE_TITLES = ["Visão Geral", "Análise de Vendas",
                   "Produtos", "Clientes / RFM", "Cohort"]
    PAGE_CLASSES = [PageOverview, PageEDA, PageProdutos, PageRFM, PageCohort]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inteligência Comercial — Felipe Huff")
        self.setMinimumSize(1300, 820)
        self.setStyleSheet(f"background-color: {BG};")

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # sidebar
        self.sidebar = Sidebar()
        root.addWidget(self.sidebar)

        # separador 1px
        sep = QFrame(); sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {SD_LIGHT};")
        root.addWidget(sep)

        # coluna de conteúdo
        content = QWidget()
        content.setStyleSheet(f"background-color: {BG};")
        cwl = QVBoxLayout(content)
        cwl.setContentsMargins(0, 0, 0, 0)
        cwl.setSpacing(0)

        # header bar
        self._header_lbl, header_bar = self._build_header()
        cwl.addWidget(header_bar)

        # páginas
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG};")
        for cls in self.PAGE_CLASSES:
            self.stack.addWidget(scroll_page(cls()))
        cwl.addWidget(self.stack)

        root.addWidget(content)
        self.sidebar.page_changed.connect(self._go)

    def _build_header(self):
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"background-color: {BG};"
            f"border-bottom: 1px solid {SD_LIGHT};"
        )
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(28, 0, 28, 0)

        title_lbl = QLabel("Visão Geral")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        bl.addWidget(title_lbl)
        bl.addStretch()

        meta_lbl = QLabel("Jan 2023 – Dez 2024  ·  500 clientes  ·  6.200 pedidos")
        meta_lbl.setFont(QFont("Segoe UI", 9))
        meta_lbl.setStyleSheet(f"color: {SUB}; background: transparent;")
        bl.addWidget(meta_lbl)

        return title_lbl, bar

    def _go(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self._header_lbl.setText(self.PAGE_TITLES[idx])


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(f"* {{ outline: 0; }}")

    # verificar dados
    if not DataStore.load():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Dados não encontrados")
        msg.setText(
            "Execute os notebooks primeiro:\n\n"
            "  python dados/gerar_dados.py\n"
            "  python notebooks/01_limpeza_tratamento.py\n"
            "  python notebooks/03_metricas_clientes.py\n"
            "  python notebooks/04_analise_cohort.py"
        )
        msg.exec()
        sys.exit(1)

    # splash
    pix = QPixmap(480, 220)
    pix.fill(QColor(BG))
    splash = QSplashScreen(pix)
    splash.showMessage(
        "   Carregando gráficos...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor(PRIM),
    )
    splash.show()
    app.processEvents()

    win = MainWindow()
    splash.finish(win)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()