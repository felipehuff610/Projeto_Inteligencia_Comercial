# %% [markdown]
# # 01 · Limpeza e Tratamento de Dados
# **Projeto:** Inteligência Comercial — Varejo E-commerce Brasil  
# **Objetivo:** Carregar os dados brutos, entender o que chegou, tratar o que tiver torto e salvar versões limpas.  
#
# > A limpeza não é glamourosa, mas é aqui que 80% dos problemas de análise nascem.
# > Prefiro gastar tempo aqui do que ter insight errado lá na frente.

# %% [markdown]
# ## 1. Imports e configuração

# %%
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# caminhos
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_BRUTOS      = os.path.join(BASE, "dados", "brutos")
DIR_PROCESSADOS = os.path.join(BASE, "dados", "processados")
os.makedirs(DIR_PROCESSADOS, exist_ok=True)

pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", "{:,.2f}".format)

print("Libs carregadas ✓")

# %% [markdown]
# ## 2. Carregamento dos dados brutos

# %%
def carregar_csv(nome: str) -> pd.DataFrame:
    caminho = os.path.join(DIR_BRUTOS, f"{nome}.csv")
    df = pd.read_csv(caminho, encoding="utf-8-sig")
    print(f"  {nome:15s} → {df.shape[0]:>6,} linhas × {df.shape[1]:>2} colunas")
    return df


print("Carregando datasets:")
df_clientes   = carregar_csv("clientes")
df_produtos   = carregar_csv("produtos")
df_vendedores = carregar_csv("vendedores")
df_pedidos    = carregar_csv("pedidos")
df_metas      = carregar_csv("metas")

# %% [markdown]
# ## 3. Inspeção rápida — o famoso "olhar pra cara do dado"

# %%
print("=" * 60)
print("PEDIDOS — primeiras linhas:")
print("=" * 60)
print(df_pedidos.head(5).to_string())

# %%
print("\n" + "=" * 60)
print("TIPOS DE DADO E NULOS:")
print("=" * 60)

def resumo_df(df: pd.DataFrame, nome: str) -> None:
    print(f"\n── {nome} ──")
    info = pd.DataFrame({
        "dtype":  df.dtypes,
        "nulos":  df.isna().sum(),
        "nulos%": (df.isna().mean() * 100).round(2),
        "únicos": df.nunique(),
    })
    print(info.to_string())

for nome_df, df in [
    ("clientes",   df_clientes),
    ("pedidos",    df_pedidos),
    ("produtos",   df_produtos),
    ("vendedores", df_vendedores),
]:
    resumo_df(df, nome_df)

# %% [markdown]
# ## 4. Limpeza — Clientes

# %%
df_cli = df_clientes.copy()

# converter datas — sempre faço isso logo no início pra não esquecer
df_cli["data_cadastro"] = pd.to_datetime(df_cli["data_cadastro"])

# padronizar segmento e região (case, espaços)
df_cli["segmento"] = df_cli["segmento"].str.strip().str.title()
df_cli["regiao"]   = df_cli["regiao"].str.strip()
df_cli["uf"]       = df_cli["uf"].str.upper().str.strip()

# e-mails: remover espaços e garantir lowercase
df_cli["email"] = df_cli["email"].str.lower().str.strip()

# checar duplicatas de e-mail — se existir, fico com o registro mais recente
n_antes = len(df_cli)
df_cli = df_cli.sort_values("data_cadastro", ascending=False).drop_duplicates("email", keep="first")
n_depois = len(df_cli)
print(f"Duplicatas de e-mail removidas: {n_antes - n_depois}")

# garantir que 'ativo' seja inteiro
df_cli["ativo"] = df_cli["ativo"].astype(int)

print(f"\nClientes após limpeza: {len(df_cli):,}")
print(df_cli.dtypes)

# %% [markdown]
# ## 5. Limpeza — Pedidos

# %%
df_ped = df_pedidos.copy()

# datas
df_ped["data_pedido"] = pd.to_datetime(df_ped["data_pedido"])

# extrair componentes temporais — vai ser útil na EDA e no SQL
df_ped["ano"]           = df_ped["data_pedido"].dt.year
df_ped["mes"]           = df_ped["data_pedido"].dt.month
df_ped["trimestre"]     = df_ped["data_pedido"].dt.quarter
df_ped["dia_semana"]    = df_ped["data_pedido"].dt.dayofweek   # 0=seg, 6=dom
df_ped["nome_mes"]      = df_ped["data_pedido"].dt.strftime("%b")
df_ped["ano_mes"]       = df_ped["data_pedido"].dt.to_period("M").astype(str)

# validações de negócio
assert (df_ped["valor_total"] > 0).all(), "Pedido com valor zerado ou negativo!"
assert (df_ped["quantidade"]  > 0).all(), "Pedido com quantidade inválida!"
assert df_ped["desconto_perc"].between(0, 1).all(), "Desconto fora do range esperado (0–1)!"

# filtrar só pedidos entregues + em trânsito para análises financeiras
# cancelados e devolvidos entram em análise separada de operações
df_ped_valido = df_ped[df_ped["status"].isin(["Entregue", "Em trânsito"])].copy()

n_cancelados  = df_ped["status"].eq("Cancelado").sum()
n_devolvidos  = df_ped["status"].eq("Devolvido").sum()
print(f"Pedidos cancelados: {n_cancelados:,} | Devolvidos: {n_devolvidos:,}")
print(f"Pedidos válidos para análise financeira: {len(df_ped_valido):,}")

# %% [markdown]
# ## 6. Limpeza — Produtos

# %%
df_prod = df_produtos.copy()

# padronizar categoria
df_prod["categoria"] = df_prod["categoria"].str.strip()

# calcular margem bruta caso ainda não exista
if "margem_bruta" not in df_prod.columns:
    df_prod["margem_bruta"] = ((df_prod["preco"] - df_prod["custo"]) / df_prod["preco"]).round(3)

# ticket esperado por categoria — útil pra contextualizar ticket médio depois
ticket_categoria = df_prod.groupby("categoria")["preco"].agg(["mean", "min", "max"]).round(2)
print("\nFaixa de preço por categoria:")
print(ticket_categoria.to_string())

# %% [markdown]
# ## 7. Enriquecimento — Pedidos com dimensões

# %%
# juntar todas as dimensões na tabela fato — eu prefiro trabalhar com um df denormalizado
# nos notebooks de análise, mesmo sabendo que no SQL vai ter os JOINs explícitos
df_analitico = (
    df_ped_valido
    .merge(df_cli[["id_cliente", "nome", "cidade", "uf", "regiao", "segmento"]], on="id_cliente", how="left")
    .merge(df_prod[["id_produto", "nome", "categoria", "custo", "margem_bruta"]], on="id_produto", how="left", suffixes=("", "_produto"))
    .merge(df_vendedores[["id_vendedor", "nome"]], on="id_vendedor", how="left", suffixes=("_cliente", "_vendedor"))
)

# renomear pra ficar mais claro
df_analitico = df_analitico.rename(columns={
    "nome_cliente":  "nome_cliente",
    "nome_vendedor": "nome_vendedor",
    "nome":          "nome_produto",  # sobra do merge de produtos
})

# lucro bruto por pedido
df_analitico["lucro_bruto"] = (
    (df_analitico["preco_unitario"] - df_analitico["custo"]) * df_analitico["quantidade"]
).round(2)

print(f"\nDataframe analítico: {df_analitico.shape}")
print(df_analitico.columns.tolist())

# %% [markdown]
# ## 8. Salvar versões processadas

# %%
def salvar(df: pd.DataFrame, nome: str) -> None:
    caminho = os.path.join(DIR_PROCESSADOS, f"{nome}.csv")
    df.to_csv(caminho, index=False, encoding="utf-8-sig")
    print(f"  ✓ {nome}.csv salvo — {len(df):,} registros")


print("Salvando dados processados:")
salvar(df_cli,        "clientes_limpos")
salvar(df_ped,        "pedidos_limpos")       # todos os pedidos com colunas novas
salvar(df_ped_valido, "pedidos_validos")      # filtrado: entregue + em trânsito
salvar(df_analitico,  "pedidos_analitico")    # denormalizado, pronto pra análise
salvar(df_prod,       "produtos_limpos")

print("\nEtapa de limpeza concluída ✓")
