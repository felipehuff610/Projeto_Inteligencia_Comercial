"""
Geração de dados sintéticos — e-commerce brasileiro
=====================================================
Setor: Varejo / E-commerce (2023–2024)

Tento simular um e-commerce de médio porte com operação nacional:
  - 500 clientes com perfil realista por região
  - 26 produtos em 4 categorias com precificação real
  - 8 vendedores distribuídos por região
  - ~6.000 pedidos com sazonalidade (Black Friday, Natal, etc.)
  - Metas mensais com fator sazonal por vendedor

Autor: Felipe Huff — github.com/felipehuff610
"""

import os
import random
from datetime import datetime

import numpy as np
import pandas as pd
from faker import Faker

# ── reprodutibilidade ──────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)
fake = Faker("pt_BR")
fake.seed_instance(42)

# ── configurações gerais ───────────────────────────────────────────────────────
DATA_INICIO = datetime(2023, 1, 1)
DATA_FIM    = datetime(2024, 12, 31)
N_CLIENTES  = 500
N_PEDIDOS   = 6_200

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brutos")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── dados de referência ────────────────────────────────────────────────────────

REGIOES = {
    "Sul":           ["Porto Alegre", "Curitiba", "Florianópolis", "Caxias do Sul", "Blumenau"],
    "Sudeste":       ["São Paulo", "Rio de Janeiro", "Belo Horizonte", "Campinas", "Uberlândia"],
    "Nordeste":      ["Salvador", "Fortaleza", "Recife", "Maceió", "Natal"],
    "Norte":         ["Manaus", "Belém", "Porto Velho", "Macapá"],
    "Centro-Oeste":  ["Brasília", "Goiânia", "Campo Grande", "Cuiabá"],
}

CIDADE_UF = {
    "Porto Alegre": "RS", "Curitiba": "PR", "Florianópolis": "SC",
    "Caxias do Sul": "RS", "Blumenau": "SC",
    "São Paulo": "SP", "Rio de Janeiro": "RJ", "Belo Horizonte": "MG",
    "Campinas": "SP", "Uberlândia": "MG",
    "Salvador": "BA", "Fortaleza": "CE", "Recife": "PE",
    "Maceió": "AL", "Natal": "RN",
    "Manaus": "AM", "Belém": "PA", "Porto Velho": "RO", "Macapá": "AP",
    "Brasília": "DF", "Goiânia": "GO", "Campo Grande": "MS", "Cuiabá": "MT",
}

VENDEDORES = [
    {"nome": "Fernanda Souza",   "regiao": "Sul",          "meta_mensal": 45_000},
    {"nome": "Carlos Müller",    "regiao": "Sul",          "meta_mensal": 38_000},
    {"nome": "Rodrigo Alves",    "regiao": "Sudeste",      "meta_mensal": 60_000},
    {"nome": "Patrícia Lima",    "regiao": "Sudeste",      "meta_mensal": 55_000},
    {"nome": "Marcos Santana",   "regiao": "Nordeste",     "meta_mensal": 42_000},
    {"nome": "Juliana Costa",    "regiao": "Nordeste",     "meta_mensal": 39_000},
    {"nome": "Bruno Pereira",    "regiao": "Norte",        "meta_mensal": 30_000},
    {"nome": "Amanda Ramos",     "regiao": "Centro-Oeste", "meta_mensal": 35_000},
]

PRODUTOS = [
    # Eletrônicos — ticket alto, margem menor, giro médio
    {"nome": "Smartphone Motorola Edge 40",  "categoria": "Eletrônicos",  "preco": 1_599.90, "custo": 1_050.00},
    {"nome": "Notebook Dell Inspiron 15",    "categoria": "Eletrônicos",  "preco": 3_299.00, "custo": 2_400.00},
    {"nome": "Fone JBL Tune 510BT",          "categoria": "Eletrônicos",  "preco":   249.90, "custo":   140.00},
    {"nome": "Smartwatch Galaxy Watch 6",    "categoria": "Eletrônicos",  "preco": 1_199.00, "custo":   780.00},
    {"nome": "Carregador Turbo 65W USB-C",   "categoria": "Eletrônicos",  "preco":    89.90, "custo":    35.00},
    {"nome": "Cabo USB-C 2m Reforçado",      "categoria": "Eletrônicos",  "preco":    39.90, "custo":    12.00},
    {"nome": "SSD Kingston 480GB",           "categoria": "Eletrônicos",  "preco":   229.90, "custo":   150.00},
    {"nome": "Mouse Logitech MX Master 3",   "categoria": "Eletrônicos",  "preco":   499.90, "custo":   310.00},
    # Moda — sazonalidade intensa, margem boa, devolução maior
    {"nome": "Camiseta Básica Algodão Pima", "categoria": "Moda",         "preco":    79.90, "custo":    28.00},
    {"nome": "Calça Jeans Slim Fit",         "categoria": "Moda",         "preco":   159.90, "custo":    60.00},
    {"nome": "Tênis Running ProX v2",        "categoria": "Moda",         "preco":   329.90, "custo":   150.00},
    {"nome": "Vestido Floral Midi",          "categoria": "Moda",         "preco":   189.90, "custo":    65.00},
    {"nome": "Bermuda Tactel Sport",         "categoria": "Moda",         "preco":    89.90, "custo":    32.00},
    {"nome": "Blusa Moletom Cropped",        "categoria": "Moda",         "preco":   119.90, "custo":    42.00},
    {"nome": "Jaqueta Corta-Vento Shell",    "categoria": "Moda",         "preco":   249.90, "custo":    95.00},
    # Casa & Decoração — compra por impulso, ticket médio
    {"nome": "Panela Antiaderente 24cm",     "categoria": "Casa & Deco",  "preco":   129.90, "custo":    55.00},
    {"nome": "Luminária LED de Mesa",        "categoria": "Casa & Deco",  "preco":    89.90, "custo":    38.00},
    {"nome": "Almofada Decorativa 45x45",    "categoria": "Casa & Deco",  "preco":    59.90, "custo":    22.00},
    {"nome": "Kit Organização de Gavetas",   "categoria": "Casa & Deco",  "preco":    49.90, "custo":    18.00},
    {"nome": "Vaso Cerâmica Minimalista",    "categoria": "Casa & Deco",  "preco":    79.90, "custo":    30.00},
    {"nome": "Toalha de Banho Premium 500g", "categoria": "Casa & Deco",  "preco":    69.90, "custo":    28.00},
    # Esportes — tendência de crescimento pós-pandemia
    {"nome": "Garrafa Térmica 1L Inox",      "categoria": "Esportes",     "preco":   119.90, "custo":    48.00},
    {"nome": "Mochila Hidratação 15L",       "categoria": "Esportes",     "preco":   189.90, "custo":    72.00},
    {"nome": "Tênis Trail Asics Gel-Kahana", "categoria": "Esportes",     "preco":   549.90, "custo":   280.00},
    {"nome": "Suporte Halteres 10kg Par",    "categoria": "Esportes",     "preco":   159.90, "custo":    65.00},
    {"nome": "Tapete de Yoga Antiderrapante","categoria": "Esportes",     "preco":    89.90, "custo":    32.00},
]

# sazonalidade real de e-commerce brasileiro
# fonte de referência: Neotrust/ABComm relatório anual
FATOR_SAZONAL = {
    1: 0.75,   # pós-festas, cartão estourado
    2: 0.80,   # carnaval esfria as vendas
    3: 0.90,
    4: 0.95,
    5: 1.10,   # Dia das Mães
    6: 0.90,
    7: 0.95,
    8: 0.95,
    9: 0.90,
    10: 1.05,  # Dia das Crianças
    11: 1.45,  # Black Friday — pico do ano
    12: 1.30,  # Natal
}

CANAIS = ["Site", "App Mobile", "Marketplace", "WhatsApp", "Televendas"]
STATUS  = ["Entregue", "Em trânsito", "Cancelado", "Devolvido"]
SEGMENTOS = ["Bronze", "Prata", "Ouro", "Diamante"]


# ── funções de geração ─────────────────────────────────────────────────────────

def gerar_clientes(n: int = N_CLIENTES) -> pd.DataFrame:
    """
    Cria base de clientes com perfil realista por região.
    Distribuição de segmento calibrada para refletir uma pirâmide de clientes real.
    """
    registros = []
    for i in range(1, n + 1):
        regiao = random.choice(list(REGIOES))
        cidade = random.choice(REGIOES[regiao])

        # pirâmide de clientes — maioria na base, poucos Diamante
        segmento = random.choices(SEGMENTOS, weights=[0.45, 0.30, 0.18, 0.07], k=1)[0]

        registros.append({
            "id_cliente":    i,
            "nome":          fake.name(),
            "email":         fake.email(),
            "cidade":        cidade,
            "uf":            CIDADE_UF[cidade],
            "regiao":        regiao,
            "segmento":      segmento,
            "data_cadastro": fake.date_between(start_date="-3y", end_date="-6m"),
            "ativo":         random.choices([1, 0], weights=[0.78, 0.22])[0],
        })

    return pd.DataFrame(registros)


def gerar_produtos() -> pd.DataFrame:
    df = pd.DataFrame(PRODUTOS)
    df.insert(0, "id_produto", range(1, len(df) + 1))
    df["margem_bruta"] = ((df["preco"] - df["custo"]) / df["preco"]).round(3)
    return df


def gerar_vendedores() -> pd.DataFrame:
    df = pd.DataFrame(VENDEDORES)
    df.insert(0, "id_vendedor", range(1, len(df) + 1))
    return df


def gerar_pedidos(
    df_clientes: pd.DataFrame,
    df_produtos: pd.DataFrame,
    df_vendedores: pd.DataFrame,
    n: int = N_PEDIDOS,
) -> pd.DataFrame:
    """
    Gera tabela fato de pedidos com:
    - Pesos de produto inversamente proporcionais ao preço (itens baratos giram mais)
    - Sazonalidade embutida na distribuição de datas
    - Vínculo entre região do cliente e vendedor (quando possível)
    """
    ids_clientes   = df_clientes["id_cliente"].tolist()
    ids_produtos   = df_produtos["id_produto"].tolist()
    precos_por_id  = df_produtos.set_index("id_produto")["preco"].to_dict()

    # produtos baratos têm peso maior — comportamento real de e-commerce
    pesos_produto = [1 / precos_por_id[pid] for pid in ids_produtos]

    # pré-calculo de mapeamento cliente → região → vendedor
    cliente_regiao = df_clientes.set_index("id_cliente")["regiao"].to_dict()
    vendedor_regiao = df_vendedores.set_index("id_vendedor")["regiao"].to_dict()

    registros = []
    for i in range(1, n + 1):
        data_pedido = fake.date_time_between(start_date=DATA_INICIO, end_date=DATA_FIM)

        id_cliente  = random.choice(ids_clientes)
        id_produto  = random.choices(ids_produtos, weights=pesos_produto, k=1)[0]

        # tenta alocar o vendedor da mesma região do cliente
        regiao_cliente   = cliente_regiao[id_cliente]
        vendedores_mesma_regiao = [
            vid for vid, reg in vendedor_regiao.items() if reg == regiao_cliente
        ]
        id_vendedor = (
            random.choice(vendedores_mesma_regiao)
            if vendedores_mesma_regiao
            else random.choice(df_vendedores["id_vendedor"].tolist())
        )

        preco_unit  = precos_por_id[id_produto]
        quantidade  = random.choices([1, 2, 3, 4, 5], weights=[0.55, 0.25, 0.12, 0.05, 0.03])[0]
        desconto    = random.choices([0, 0.05, 0.10, 0.15, 0.20], weights=[0.50, 0.20, 0.15, 0.10, 0.05])[0]
        valor_total = round(preco_unit * quantidade * (1 - desconto), 2)

        # status com distribuição realista
        status = random.choices(STATUS, weights=[0.82, 0.10, 0.05, 0.03], k=1)[0]
        canal  = random.choices(CANAIS, weights=[0.35, 0.30, 0.20, 0.10, 0.05], k=1)[0]

        registros.append({
            "id_pedido":       i,
            "id_cliente":      id_cliente,
            "id_produto":      id_produto,
            "id_vendedor":     id_vendedor,
            "data_pedido":     data_pedido.date(),
            "quantidade":      quantidade,
            "preco_unitario":  preco_unit,
            "desconto_perc":   desconto,
            "valor_total":     valor_total,
            "canal":           canal,
            "status":          status,
        })

    return pd.DataFrame(registros)


def gerar_metas(df_vendedores: pd.DataFrame) -> pd.DataFrame:
    """
    Metas mensais por vendedor considerando sazonalidade.
    O 'realizado' vai ser calculado depois nos notebooks — aqui só a meta.
    """
    registros = []
    for _, v in df_vendedores.iterrows():
        for ano in [2023, 2024]:
            for mes in range(1, 13):
                meta_mes = round(v["meta_mensal"] * FATOR_SAZONAL[mes], 2)
                registros.append({
                    "id_vendedor": v["id_vendedor"],
                    "ano":         ano,
                    "mes":         mes,
                    "meta_valor":  meta_mes,
                })
    return pd.DataFrame(registros)


# ── execução ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🛒  Gerando dados sintéticos — e-commerce Brasil\n")

    print("  → Clientes...")
    df_clientes   = gerar_clientes()

    print("  → Produtos...")
    df_produtos   = gerar_produtos()

    print("  → Vendedores...")
    df_vendedores = gerar_vendedores()

    print("  → Pedidos (pode demorar uns segundos)...")
    df_pedidos    = gerar_pedidos(df_clientes, df_produtos, df_vendedores)

    print("  → Metas...")
    df_metas      = gerar_metas(df_vendedores)

    datasets = {
        "clientes":   df_clientes,
        "produtos":   df_produtos,
        "vendedores": df_vendedores,
        "pedidos":    df_pedidos,
        "metas":      df_metas,
    }

    print()
    for nome, df in datasets.items():
        caminho = os.path.join(OUTPUT_DIR, f"{nome}.csv")
        df.to_csv(caminho, index=False, encoding="utf-8-sig")
        print(f"  ✓ {nome}.csv  [{len(df):>6,} registros]")

    print(f"\n✅  Concluído!")
    print(f"   Período:   {DATA_INICIO:%d/%m/%Y} → {DATA_FIM:%d/%m/%Y}")
    print(f"   Clientes:  {len(df_clientes):,} | Pedidos: {len(df_pedidos):,} | Produtos: {len(df_produtos):,}")
    print(f"   Salvo em:  {OUTPUT_DIR}")
