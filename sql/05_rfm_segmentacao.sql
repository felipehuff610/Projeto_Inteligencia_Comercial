/*
==============================================================
  Segmentação RFM — Recência, Frequência, Valor Monetário
==============================================================
  Implementação completa do modelo RFM em SQL puro.
  Funciona em PostgreSQL, BigQuery e (com ajustes mínimos) SQL Server.
  
  O score vai de 1–5 em cada dimensão:
    R: quanto mais recente, maior o score
    F: quanto mais frequente, maior o score
    M: quanto maior o valor, maior o score
  
  A classificação final mapeia combinações de scores
  pra segmentos de negócio acionáveis.
==============================================================
*/

-- ── passo 1: métricas brutas por cliente ──────────────────────────────────────

WITH metricas AS (
    SELECT
        p.id_cliente,
        c.nome,
        c.email,
        c.segmento,
        c.regiao,
        -- recência: dias desde a última compra
        CAST(
            JULIANDAY((SELECT MAX(data_pedido) FROM pedidos)) 
            - JULIANDAY(MAX(p.data_pedido))
        AS INTEGER)                          AS recencia_dias,
        -- frequência: total de pedidos
        COUNT(p.id_pedido)                   AS frequencia,
        -- monetário: receita total do cliente
        ROUND(SUM(p.valor_total), 2)         AS monetario
    FROM pedidos p
    JOIN clientes c ON c.id_cliente = p.id_cliente
    WHERE p.status IN ('Entregue', 'Em trânsito')
    GROUP BY p.id_cliente, c.nome, c.email, c.segmento, c.regiao
),

-- ── passo 2: calcular os scores 1–5 via NTILE ─────────────────────────────────
-- nota: recência é invertida (menos dias = score maior)

scores AS (
    SELECT
        *,
        -- R invertido: rank por recência crescente → score decrescente
        CASE NTILE(5) OVER (ORDER BY recencia_dias DESC)
            WHEN 1 THEN 5
            WHEN 2 THEN 4
            WHEN 3 THEN 3
            WHEN 4 THEN 2
            WHEN 5 THEN 1
        END AS score_r,
        NTILE(5) OVER (ORDER BY frequencia ASC)  AS score_f,
        NTILE(5) OVER (ORDER BY monetario ASC)   AS score_m
    FROM metricas
),

-- ── passo 3: score consolidado e segmentação ──────────────────────────────────

segmentado AS (
    SELECT
        *,
        score_r + score_f + score_m           AS rfm_total,
        -- código de 3 dígitos pra análises matriciais
        CAST(score_r AS TEXT) 
            || CAST(score_f AS TEXT) 
            || CAST(score_m AS TEXT)           AS rfm_codigo,
        CASE
            WHEN score_r >= 4 AND score_f >= 4 AND score_m >= 4
                THEN 'Campeões'
            WHEN score_r >= 4 AND (score_f >= 3 OR score_m >= 3)
                THEN 'Clientes Fiéis'
            WHEN score_r >= 3 AND score_f >= 3 AND score_m <= 2
                THEN 'Potencial de Crescimento'
            WHEN score_r <= 2 AND score_f >= 4
                THEN 'Em Risco'
            WHEN score_r <= 2 AND score_f <= 2 AND score_m >= 3
                THEN 'Hibernando'
            WHEN score_r <= 2 AND score_f <= 2 AND score_m <= 2
                THEN 'Perdidos'
            ELSE
                'Regulares'
        END AS segmento_rfm
    FROM scores
)

-- ── resultado final ────────────────────────────────────────────────────────────

SELECT
    id_cliente,
    nome,
    email,
    segmento          AS segmento_cadastro,
    regiao,
    recencia_dias,
    frequencia,
    monetario,
    score_r,
    score_f,
    score_m,
    rfm_total,
    rfm_codigo,
    segmento_rfm
FROM segmentado
ORDER BY rfm_total DESC, monetario DESC;

/*
  ──────────────────────────────────────────
  Consolidado por segmento RFM — visão executiva
  ──────────────────────────────────────────

  SELECT
      segmento_rfm,
      COUNT(*)                         AS total_clientes,
      ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_base,
      ROUND(AVG(recencia_dias), 0)     AS recencia_media,
      ROUND(AVG(frequencia), 1)        AS frequencia_media,
      ROUND(AVG(monetario), 2)         AS ticket_medio,
      ROUND(SUM(monetario), 2)         AS receita_total
  FROM segmentado
  GROUP BY segmento_rfm
  ORDER BY receita_total DESC;
*/

/*
  ──────────────────────────────────────────
  Ações recomendadas por segmento:
  
  Campeões          → Programa de fidelidade VIP, acesso antecipado
  Clientes Fiéis    → Upsell, cross-sell, solicitar avaliação
  Potencial         → Cupom de segunda compra, email de reengajamento
  Em Risco          → Campanha urgente, pesquisa de satisfação
  Hibernando        → Oferta de reativação agressiva
  Perdidos          → Pesquisa de churn, ou remover da base ativa
  ──────────────────────────────────────────
*/
