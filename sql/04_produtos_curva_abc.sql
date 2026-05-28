/*
==============================================================
  Top Produtos — Receita, Volume e Margem
==============================================================
*/

WITH vendas_produto AS (
    SELECT
        p.id_produto,
        pr.nome                                             AS produto,
        pr.categoria,
        pr.preco                                            AS preco_tabela,
        pr.custo,
        ROUND(pr.preco - pr.custo, 2)                       AS margem_unitaria,
        ROUND((pr.preco - pr.custo) / NULLIF(pr.preco, 0) * 100, 1) AS pct_margem,
        COUNT(p.id_pedido)                                  AS qtd_pedidos,
        SUM(p.quantidade)                                   AS unidades_vendidas,
        ROUND(SUM(p.valor_total), 2)                        AS receita_total,
        ROUND(AVG(p.desconto_perc) * 100, 1)               AS desconto_medio_pct,
        COUNT(DISTINCT p.id_cliente)                        AS clientes_distintos
    FROM pedidos p
    JOIN produtos pr ON pr.id_produto = p.id_produto
    WHERE p.status IN ('Entregue', 'Em trânsito')
    GROUP BY p.id_produto, pr.nome, pr.categoria, pr.preco, pr.custo
),

com_rank AS (
    SELECT
        *,
        -- ranking global por receita
        RANK() OVER (ORDER BY receita_total DESC) AS rank_receita,
        -- ranking dentro da categoria
        RANK() OVER (PARTITION BY categoria ORDER BY receita_total DESC) AS rank_categoria,
        -- participação na receita total
        ROUND(
            receita_total / SUM(receita_total) OVER () * 100,
            2
        ) AS share_receita_pct,
        -- acumulado pra análise de Pareto (curva ABC)
        SUM(receita_total) OVER (ORDER BY receita_total DESC) AS receita_acumulada,
        SUM(receita_total) OVER ()                            AS receita_geral
    FROM vendas_produto
),

curva_abc AS (
    SELECT
        *,
        ROUND(receita_acumulada / NULLIF(receita_geral, 0) * 100, 1) AS pct_acumulado,
        CASE
            WHEN receita_acumulada / NULLIF(receita_geral, 0) <= 0.80 THEN 'A — Estratégico'
            WHEN receita_acumulada / NULLIF(receita_geral, 0) <= 0.95 THEN 'B — Relevante'
            ELSE                                                            'C — Cauda Longa'
        END AS curva_abc
    FROM com_rank
)

SELECT
    rank_receita,
    produto,
    categoria,
    curva_abc,
    qtd_pedidos,
    unidades_vendidas,
    receita_total,
    share_receita_pct,
    pct_acumulado,
    pct_margem          AS margem_bruta_pct,
    desconto_medio_pct,
    clientes_distintos,
    rank_categoria
FROM curva_abc
ORDER BY rank_receita;
