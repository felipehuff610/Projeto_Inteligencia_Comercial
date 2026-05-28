/*
==============================================================
  Ticket Médio por Cliente — com percentis e benchmark
==============================================================
  Vai além do AVG simples: categoriza cada cliente em relação
  à base toda usando NTILE. Útil pra identificar quem está
  abaixo do potencial esperado pro seu segmento.
==============================================================
*/

WITH base_pedidos AS (
    SELECT
        p.id_cliente,
        p.id_pedido,
        p.valor_total,
        p.data_pedido,
        p.canal,
        c.nome,
        c.segmento,
        c.regiao
    FROM pedidos p
    JOIN clientes c ON c.id_cliente = p.id_cliente
    WHERE p.status IN ('Entregue', 'Em trânsito')
),

metricas_cliente AS (
    SELECT
        id_cliente,
        nome,
        segmento,
        regiao,
        COUNT(id_pedido)                        AS total_pedidos,
        SUM(valor_total)                        AS receita_total,
        ROUND(AVG(valor_total), 2)              AS ticket_medio,
        ROUND(MIN(valor_total), 2)              AS menor_pedido,
        ROUND(MAX(valor_total), 2)              AS maior_pedido,
        MIN(data_pedido)                        AS primeira_compra,
        MAX(data_pedido)                        AS ultima_compra,
        -- canal favorito: simplificado aqui, subquery seria mais preciso
        COUNT(DISTINCT canal)                   AS canais_utilizados
    FROM base_pedidos
    GROUP BY id_cliente, nome, segmento, regiao
),

com_percentil AS (
    SELECT
        *,
        -- NTILE divide a base em 4 grupos iguais por ticket
        -- no BigQuery/Postgres é nativo; SQLite não tem, mas simulamos com subquery
        CASE
            WHEN ticket_medio >= (SELECT PERCENTILE_APPROX(ticket_medio, 0.75) 
                                  FROM metricas_cliente)
            THEN 'Top 25%'
            WHEN ticket_medio >= (SELECT PERCENTILE_APPROX(ticket_medio, 0.50) 
                                  FROM metricas_cliente)
            THEN '50%–75%'
            WHEN ticket_medio >= (SELECT PERCENTILE_APPROX(ticket_medio, 0.25) 
                                  FROM metricas_cliente)
            THEN '25%–50%'
            ELSE 'Bottom 25%'
        END AS faixa_ticket
    FROM metricas_cliente
)

SELECT
    id_cliente,
    nome,
    segmento,
    regiao,
    total_pedidos,
    ROUND(receita_total, 2)  AS receita_total,
    ticket_medio,
    menor_pedido,
    maior_pedido,
    faixa_ticket,
    primeira_compra,
    ultima_compra
FROM com_percentil
ORDER BY ticket_medio DESC;

/*
  ──────────────────────────────────────────
  Benchmark: ticket médio por segmento
  (cole em ferramenta separada ou subconsulta)
  ──────────────────────────────────────────

  SELECT
      segmento,
      COUNT(*)                       AS total_clientes,
      ROUND(AVG(ticket_medio), 2)   AS ticket_medio_segmento,
      ROUND(MIN(ticket_medio), 2)   AS menor,
      ROUND(MAX(ticket_medio), 2)   AS maior
  FROM metricas_cliente
  GROUP BY segmento
  ORDER BY ticket_medio_segmento DESC;
*/

/*
  ──────────────────────────────────────────
  Versão compatível com PostgreSQL / BigQuery
  (substitui PERCENTILE_APPROX por PERCENTILE_CONT)
  ──────────────────────────────────────────

  WITH quartis AS (
      SELECT
          PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ticket_medio) AS q1,
          PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY ticket_medio) AS q2,
          PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ticket_medio) AS q3
      FROM metricas_cliente
  )
  SELECT
      m.*,
      CASE
          WHEN m.ticket_medio >= q.q3 THEN 'Top 25%'
          WHEN m.ticket_medio >= q.q2 THEN '50%–75%'
          WHEN m.ticket_medio >= q.q1 THEN '25%–50%'
          ELSE 'Bottom 25%'
      END AS faixa_ticket
  FROM metricas_cliente m
  CROSS JOIN quartis q
  ORDER BY m.ticket_medio DESC;
*/
