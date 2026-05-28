/*
==============================================================
  Clientes Inativos — sem compra há mais de 90 dias
==============================================================
  Contexto: clientes que já compraram mas sumiram do radar.
  Esses são candidatos prioritários pra campanha de reativação.
  
  Referência de corte: 90 dias (pode ajustar no WHERE final).
  A CTE "ultima_compra" exclui pedidos cancelados/devolvidos
  pra não distorcer a data real de última transação válida.
==============================================================
*/

WITH ultima_compra AS (
    -- só pedidos que efetivamente geraram receita
    SELECT
        p.id_cliente,
        MAX(p.data_pedido)                      AS data_ultima_compra,
        COUNT(p.id_pedido)                      AS total_pedidos,
        SUM(p.valor_total)                      AS receita_total,
        ROUND(AVG(p.valor_total), 2)            AS ticket_medio
    FROM pedidos p
    WHERE p.status IN ('Entregue', 'Em trânsito')
    GROUP BY p.id_cliente
),

classificacao AS (
    SELECT
        uc.id_cliente,
        c.nome,
        c.email,
        c.cidade,
        c.regiao,
        c.segmento,
        uc.data_ultima_compra,
        uc.total_pedidos,
        uc.receita_total,
        uc.ticket_medio,
        -- dias desde a última compra (em SQLite; no SQL Server use DATEDIFF)
        CAST(JULIANDAY('now') - JULIANDAY(uc.data_ultima_compra) AS INTEGER) AS dias_sem_compra,
        CASE
            WHEN CAST(JULIANDAY('now') - JULIANDAY(uc.data_ultima_compra) AS INTEGER) BETWEEN  91 AND 180 THEN 'Inativo Recente'
            WHEN CAST(JULIANDAY('now') - JULIANDAY(uc.data_ultima_compra) AS INTEGER) BETWEEN 181 AND 365 THEN 'Inativo Moderado'
            WHEN CAST(JULIANDAY('now') - JULIANDAY(uc.data_ultima_compra) AS INTEGER) > 365             THEN 'Inativo Crítico'
        END AS grau_inatividade
    FROM ultima_compra uc
    JOIN clientes c ON c.id_cliente = uc.id_cliente
)

SELECT
    id_cliente,
    nome,
    email,
    regiao,
    segmento,
    data_ultima_compra,
    dias_sem_compra,
    grau_inatividade,
    total_pedidos,
    ROUND(receita_total, 2)  AS receita_total,
    ticket_medio
FROM classificacao
WHERE dias_sem_compra > 90
ORDER BY
    -- priorizar quem gasta mais pra campanha de reativação
    receita_total DESC,
    dias_sem_compra ASC;

/*
  Análise complementar: quantos inativos por segmento?
  
  SELECT
      segmento,
      grau_inatividade,
      COUNT(*)                    AS qtd_clientes,
      ROUND(AVG(receita_total),2) AS ticket_medio_historico,
      ROUND(SUM(receita_total),2) AS receita_potencial
  FROM classificacao
  WHERE dias_sem_compra > 90
  GROUP BY segmento, grau_inatividade
  ORDER BY segmento, grau_inatividade;
*/
