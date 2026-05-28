/*
==============================================================
  Performance por Região — Receita, Crescimento e Mix
==============================================================
  Análise comparativa entre regiões incluindo:
  - Receita e volume por região
  - Crescimento YoY (ano sobre ano)
  - Mix de categorias por região
  - Ticket médio e clientes únicos
==============================================================
*/

WITH base AS (
    SELECT
        c.regiao,
        c.uf,
        pr.categoria,
        CAST(STRFTIME('%Y', p.data_pedido) AS INTEGER) AS ano,
        CAST(STRFTIME('%m', p.data_pedido) AS INTEGER) AS mes,
        p.id_cliente,
        p.valor_total
    FROM pedidos p
    JOIN clientes c  ON c.id_cliente  = p.id_cliente
    JOIN produtos pr ON pr.id_produto = p.id_produto
    WHERE p.status IN ('Entregue', 'Em trânsito')
),

por_regiao_ano AS (
    SELECT
        regiao,
        ano,
        COUNT(DISTINCT id_cliente)    AS clientes_unicos,
        COUNT(*)                      AS total_pedidos,
        ROUND(SUM(valor_total), 2)    AS receita_total,
        ROUND(AVG(valor_total), 2)    AS ticket_medio_pedido,
        ROUND(
            SUM(valor_total) / NULLIF(COUNT(DISTINCT id_cliente), 0),
            2
        )                             AS receita_por_cliente
    FROM base
    GROUP BY regiao, ano
),

com_crescimento AS (
    SELECT
        atual.*,
        anterior.receita_total                          AS receita_ano_anterior,
        ROUND(
            (atual.receita_total - COALESCE(anterior.receita_total, 0))
            / NULLIF(anterior.receita_total, 0) * 100,
            1
        )                                               AS crescimento_yoy_pct,
        -- share da receita total no ano
        ROUND(
            atual.receita_total / SUM(atual.receita_total) OVER (PARTITION BY atual.ano) * 100,
            1
        )                                               AS share_receita_pct,
        -- ranking por receita dentro do ano
        RANK() OVER (
            PARTITION BY atual.ano
            ORDER BY atual.receita_total DESC
        )                                               AS rank_ano
    FROM por_regiao_ano atual
    LEFT JOIN por_regiao_ano anterior
        ON anterior.regiao = atual.regiao
       AND anterior.ano    = atual.ano - 1
)

SELECT
    regiao,
    ano,
    rank_ano,
    clientes_unicos,
    total_pedidos,
    receita_total,
    share_receita_pct,
    ticket_medio_pedido,
    receita_por_cliente,
    receita_ano_anterior,
    crescimento_yoy_pct,
    CASE
        WHEN crescimento_yoy_pct >  10 THEN '📈 Acelerado'
        WHEN crescimento_yoy_pct >= 0  THEN '➡️  Estável'
        WHEN crescimento_yoy_pct < 0   THEN '📉 Em queda'
        ELSE '— Sem histórico'
    END AS tendencia
FROM com_crescimento
ORDER BY ano DESC, rank_ano;

/*
  ──────────────────────────────────────────
  Mix de categorias por região (2024)
  ──────────────────────────────────────────

  SELECT
      regiao,
      categoria,
      ROUND(SUM(valor_total), 2)                        AS receita,
      ROUND(
          SUM(valor_total) / SUM(SUM(valor_total)) OVER (PARTITION BY regiao) * 100,
          1
      )                                                 AS share_na_regiao_pct
  FROM base
  WHERE ano = 2024
  GROUP BY regiao, categoria
  ORDER BY regiao, share_na_regiao_pct DESC;
*/
