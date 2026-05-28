/*
==============================================================
  Meta × Realizado por Vendedor
==============================================================
  Compara a meta mensal de cada vendedor com o que foi
  efetivamente vendido no período. Inclui:
  - % de atingimento
  - Gap em R$
  - Ranking dentro da região
  - Tendência: se o mês atual está melhor que o anterior

  Ideal pra alimentar o dashboard de gestão comercial.
==============================================================
*/

WITH realizado AS (
    -- agrupa pedidos válidos por vendedor/mês
    SELECT
        p.id_vendedor,
        CAST(STRFTIME('%Y', p.data_pedido) AS INTEGER)  AS ano,
        CAST(STRFTIME('%m', p.data_pedido) AS INTEGER)  AS mes,
        COUNT(p.id_pedido)                              AS qtd_pedidos,
        SUM(p.valor_total)                              AS valor_realizado,
        COUNT(DISTINCT p.id_cliente)                    AS clientes_atendidos
    FROM pedidos p
    WHERE p.status IN ('Entregue', 'Em trânsito')
    GROUP BY p.id_vendedor, ano, mes
),

meta_real_mensal AS (
    SELECT
        m.id_vendedor,
        v.nome                                                   AS vendedor,
        v.regiao,
        m.ano,
        m.mes,
        m.meta_valor,
        COALESCE(r.valor_realizado, 0)                           AS valor_realizado,
        COALESCE(r.qtd_pedidos, 0)                               AS qtd_pedidos,
        COALESCE(r.clientes_atendidos, 0)                        AS clientes_atendidos,
        -- atingimento em %
        ROUND(
            COALESCE(r.valor_realizado, 0) / NULLIF(m.meta_valor, 0) * 100,
            1
        )                                                        AS pct_atingimento,
        -- gap: positivo = superou, negativo = não bateu
        ROUND(COALESCE(r.valor_realizado, 0) - m.meta_valor, 2)  AS gap_meta
    FROM metas m
    JOIN vendedores v ON v.id_vendedor = m.id_vendedor
    LEFT JOIN realizado r
        ON r.id_vendedor = m.id_vendedor
       AND r.ano         = m.ano
       AND r.mes         = m.mes
),

com_ranking AS (
    SELECT
        *,
        -- ranking por atingimento dentro da região no mês
        RANK() OVER (
            PARTITION BY regiao, ano, mes
            ORDER BY pct_atingimento DESC
        ) AS rank_regiao,
        -- média móvel 3 meses do realizado por vendedor
        ROUND(
            AVG(valor_realizado) OVER (
                PARTITION BY id_vendedor
                ORDER BY ano, mes
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            ),
            2
        ) AS media_movel_3m
    FROM meta_real_mensal
)

SELECT
    vendedor,
    regiao,
    ano,
    mes,
    ROUND(meta_valor, 2)       AS meta,
    ROUND(valor_realizado, 2)  AS realizado,
    pct_atingimento,
    gap_meta,
    qtd_pedidos,
    clientes_atendidos,
    rank_regiao,
    ROUND(media_movel_3m, 2)   AS media_movel_3m,
    -- semáforo simples pra visualização condicional no Power BI
    CASE
        WHEN pct_atingimento >= 100 THEN '🟢 Meta Batida'
        WHEN pct_atingimento >= 80  THEN '🟡 Quase Lá'
        ELSE                             '🔴 Abaixo da Meta'
    END AS status_meta
FROM com_ranking
ORDER BY ano, mes, regiao, rank_regiao;

/*
  ──────────────────────────────────────────
  Resumo anual por vendedor
  ──────────────────────────────────────────

  SELECT
      vendedor,
      regiao,
      ano,
      ROUND(SUM(meta_valor), 2)      AS meta_anual,
      ROUND(SUM(valor_realizado), 2) AS realizado_anual,
      ROUND(SUM(valor_realizado) / NULLIF(SUM(meta_valor),0) * 100, 1) AS pct_atingimento,
      SUM(qtd_pedidos)               AS total_pedidos,
      SUM(clientes_atendidos)        AS total_clientes
  FROM meta_real_mensal
  GROUP BY vendedor, regiao, ano
  ORDER BY ano, pct_atingimento DESC;
*/
