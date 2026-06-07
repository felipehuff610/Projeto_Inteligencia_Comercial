# Medidas DAX — Inteligência Comercial
**Felipe Huff | github.com/felipehuff610**

> Como usar: No Power BI, crie uma tabela vazia chamada `_Medidas`
> (Modelagem → Nova Tabela → `_Medidas = {""}`).
> Cole cada medida nessa tabela via **Modelagem → Nova Medida**.
> Organizar tudo numa tabela só facilita manutenção e deixa o modelo limpo.

---

## Bloco 1 — Medidas base (usadas em todos os dashboards)

```dax
// Receita total (só pedidos válidos — já filtrado no CSV)
Receita Total =
SUM ( Pedidos[valor_total] )

// Número de pedidos
Total Pedidos =
COUNTROWS ( Pedidos )

// Clientes únicos que compraram
Clientes com Compra =
DISTINCTCOUNT ( Pedidos[id_cliente] )

// Ticket médio por pedido
Ticket Médio Pedido =
DIVIDE ( [Receita Total], [Total Pedidos], 0 )

// Ticket médio por cliente (receita ÷ clientes únicos)
Ticket Médio Cliente =
DIVIDE ( [Receita Total], [Clientes com Compra], 0 )

// Lucro bruto total
Lucro Bruto Total =
SUM ( Pedidos[lucro_bruto] )

// Margem bruta %
Margem Bruta % =
DIVIDE ( [Lucro Bruto Total], [Receita Total], 0 )

// Unidades vendidas
Unidades Vendidas =
SUM ( Pedidos[quantidade] )
```

---

## Bloco 2 — Comparativo temporal (YoY)

```dax
// Receita do mesmo período no ano anterior
Receita Ano Anterior =
CALCULATE (
    [Receita Total],
    SAMEPERIODLASTYEAR ( dCalendario[Date] )
)

// Crescimento ano sobre ano em valor absoluto
Crescimento R$ YoY =
[Receita Total] - [Receita Ano Anterior]

// Crescimento ano sobre ano em %
Crescimento % YoY =
DIVIDE (
    [Crescimento R$ YoY],
    [Receita Ano Anterior],
    BLANK()
)

// Receita acumulada no ano (YTD)
Receita YTD =
TOTALYTD ( [Receita Total], dCalendario[Date] )

// Receita acumulada no ano anterior (pra comparar o YTD)
Receita YTD Ano Anterior =
CALCULATE (
    [Receita YTD],
    SAMEPERIODLASTYEAR ( dCalendario[Date] )
)

// Receita do mês anterior (MoM)
Receita Mês Anterior =
CALCULATE (
    [Receita Total],
    PREVIOUSMONTH ( dCalendario[Date] )
)

// Crescimento mês sobre mês %
Crescimento % MoM =
DIVIDE (
    [Receita Total] - [Receita Mês Anterior],
    [Receita Mês Anterior],
    BLANK()
)
```

---

## Bloco 3 — Dashboard Executivo

```dax
// Desconto médio concedido
Desconto Médio % =
AVERAGE ( Pedidos[desconto_perc] )

// Pedidos com desconto aplicado
Pedidos com Desconto =
COUNTROWS ( FILTER ( Pedidos, Pedidos[desconto_perc] > 0 ) )

// % de pedidos que tiveram desconto
% Pedidos com Desconto =
DIVIDE ( [Pedidos com Desconto], [Total Pedidos], 0 )

// Receita perdida por desconto (quanto foi aberto de desconto em R$)
Receita Descontada =
SUMX (
    Pedidos,
    Pedidos[preco_unitario] * Pedidos[quantidade] * Pedidos[desconto_perc]
)

// Share de receita da categoria selecionada sobre o total
// (útil em visual com filtro por categoria)
Share Receita Categoria % =
DIVIDE (
    [Receita Total],
    CALCULATE ( [Receita Total], ALL ( Produtos[categoria] ) ),
    0
)

// Produto mais vendido em receita (retorna o nome)
Top Produto =
CALCULATE (
    SELECTEDVALUE ( Pedidos[nome_produto] ),
    TOPN ( 1, VALUES ( Pedidos[nome_produto] ), [Receita Total] )
)

// Região líder em receita (retorna o nome)
Região Líder =
CALCULATE (
    SELECTEDVALUE ( Pedidos[regiao] ),
    TOPN ( 1, VALUES ( Pedidos[regiao] ), [Receita Total] )
)
```

---

## Bloco 4 — Dashboard Vendedores

```dax
// Meta total do período filtrado
Meta Total =
SUM ( MetaRealizado[meta_valor] )

// Realizado total (já calculado no Python e salvo no CSV)
Realizado Total =
SUM ( MetaRealizado[realizado] )

// % de atingimento de meta
Atingimento % =
DIVIDE ( [Realizado Total], [Meta Total], 0 )

// Gap: positivo = superou a meta, negativo = ficou abaixo
Gap Meta R$ =
[Realizado Total] - [Meta Total]

// Número de meses em que o vendedor bateu a meta
Meses Batendo Meta =
COUNTROWS (
    FILTER (
        MetaRealizado,
        MetaRealizado[realizado] >= MetaRealizado[meta_valor]
    )
)

// Número de vendedores acima da meta (útil em cartão no painel geral)
Vendedores Acima da Meta =
COUNTROWS (
    FILTER (
        SUMMARIZE (
            MetaRealizado,
            MetaRealizado[nome],
            "Atinge", DIVIDE ( SUM ( MetaRealizado[realizado] ), SUM ( MetaRealizado[meta_valor] ) )
        ),
        [Atinge] >= 1
    )
)

// Melhor mês de um vendedor (label pra cartão)
Melhor Mês Vendedor =
VAR tbl =
    ADDCOLUMNS (
        SUMMARIZE ( MetaRealizado, MetaRealizado[ano], MetaRealizado[mes] ),
        "R", CALCULATE ( SUM ( MetaRealizado[realizado] ) )
    )
VAR melhor = MAXX ( tbl, [R] )
RETURN
    MAXX ( FILTER ( tbl, [R] = melhor ), MetaRealizado[mes] )

// Cor do semáforo de atingimento (retorna texto — use em formatação condicional)
Status Meta Cor =
SWITCH (
    TRUE(),
    [Atingimento %] >= 1,    "Verde",
    [Atingimento %] >= 0.8,  "Amarelo",
    "Vermelho"
)
```

---

## Bloco 5 — Dashboard Clientes

```dax
// Total de clientes cadastrados
Total Clientes =
COUNTROWS ( Clientes )

// Clientes que compraram nos últimos 90 dias
// (data de referência = último pedido do dataset)
Clientes Ativos 90d =
VAR dataRef = CALCULATE ( MAX ( Pedidos[data_pedido] ), ALL ( Pedidos ) )
VAR ultimaCompra =
    ADDCOLUMNS (
        VALUES ( Pedidos[id_cliente] ),
        "UltimaCompra", CALCULATE ( MAX ( Pedidos[data_pedido] ) )
    )
RETURN
    COUNTROWS (
        FILTER ( ultimaCompra, [UltimaCompra] >= dataRef - 90 )
    )

// Clientes inativos (sem compra há mais de 90 dias)
Clientes Inativos =
[Clientes com Compra] - [Clientes Ativos 90d]

// % de clientes inativos
% Clientes Inativos =
DIVIDE ( [Clientes Inativos], [Clientes com Compra], 0 )

// Recência média da base (em dias)
Recência Média =
VAR dataRef = CALCULATE ( MAX ( Pedidos[data_pedido] ), ALL ( Pedidos ) )
RETURN
    AVERAGEX (
        VALUES ( Pedidos[id_cliente] ),
        dataRef - CALCULATE ( MAX ( Pedidos[data_pedido] ) )
    )

// Frequência média de compras por cliente
Frequência Média =
DIVIDE ( [Total Pedidos], [Clientes com Compra], 0 )

// Clientes com segmento RFM específico (use com slicer de segmento_rfm)
Clientes no Segmento RFM =
DISTINCTCOUNT ( RFM[id_cliente] )

// Receita dos clientes Campeões (fixo — não se altera com filtros de data)
Receita Campeões =
CALCULATE (
    [Receita Total],
    RFM[segmento_rfm] = "Campeões"
)

// % da receita que vem dos clientes Campeões
% Receita Campeões =
DIVIDE (
    [Receita Campeões],
    CALCULATE ( [Receita Total], ALL ( RFM ) ),
    0
)
```

---

## Bloco 6 — Formatações úteis

```dax
// Formata valor em R$ compacto (ex: R$ 1,2M | R$ 350K | R$ 1.500)
Receita Formatada =
VAR v = [Receita Total]
RETURN
    SWITCH (
        TRUE(),
        v >= 1000000, FORMAT ( v / 1000000, "R$ #,##0.0""M""" ),
        v >= 1000,    FORMAT ( v / 1000,    "R$ #,##0""K""" ),
        FORMAT ( v, "R$ #,##0" )
    )

// Label de crescimento com seta (ex: ▲ 12,3% | ▼ -5,1%)
Label Crescimento YoY =
VAR pct = [Crescimento % YoY]
RETURN
    IF (
        ISBLANK ( pct ),
        "—",
        IF (
            pct >= 0,
            "▲ " & FORMAT ( pct, "0.0%" ),
            "▼ " & FORMAT ( ABS ( pct ), "0.0%" )
        )
    )

// Label de atingimento com semáforo (ex: 🟢 104,2% | 🔴 73,1%)
Label Atingimento =
VAR pct = [Atingimento %]
RETURN
    SWITCH (
        TRUE(),
        pct >= 1,   "🟢 " & FORMAT ( pct, "0.0%" ),
        pct >= 0.8, "🟡 " & FORMAT ( pct, "0.0%" ),
        "🔴 " & FORMAT ( pct, "0.0%" )
    )
```

---

## Dica de organização no Power BI

Depois de criar todas as medidas, organize-as em **pastas de exibição**:
- Clique na medida → Propriedades → "Pasta de exibição"
- Sugestão de pastas: `Base`, `Tempo`, `Vendedores`, `Clientes`, `Formatação`

Isso mantém o painel de campos limpo e profissional.
