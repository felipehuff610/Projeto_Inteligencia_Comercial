# Layout dos Dashboards — Guia Visual
**Projeto Inteligência Comercial | Felipe Huff**

> Tamanho de página recomendado: **1280 × 720px** (16:9)
> Exibição → Tamanho da Página → Personalizado → 1280 × 720

---

## Dashboard 1 — Executivo

**Narrativa:** visão do CEO/gerente. Responde em 30 segundos:
faturamos quanto? crescemos? o que está vendendo? onde?

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER: Logo/título   [Slicer: Ano]  [Slicer: Trimestre]       │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│ CARTÃO       │ CARTÃO       │ CARTÃO       │ CARTÃO              │
│ Receita Total│ Total Pedidos│ Ticket Médio │ Margem Bruta %      │
│ R$ 1,2M      │ 5.667        │ R$ 212       │ 38,4%               │
│ ▲ +8,3% YoY  │ ▲ +6,1% YoY  │ ▲ +2,1% YoY  │ ▲ +1,2pp YoY        │
├──────────────────────────────────┬───────────────────────────────┤
│                                  │                               │
│  GRÁFICO DE LINHA                │  GRÁFICO DE BARRAS HORIZ.    │
│  Receita mensal                  │  Receita por Região          │
│  (2023 vs 2024 — duas linhas)    │  (5 barras, ordem decrescente│
│  Eixo X: AnoMesLabel             │   com valor no final)        │
│  Destaque: Nov (Black Friday)    │                               │
│                                  │                               │
├──────────────────┬───────────────┴───────────────────────────────┤
│                  │                                               │
│  GRÁFICO ROSCA   │  GRÁFICO DE BARRAS VERTICAIS                 │
│  Share por Canal │  Top 10 Produtos por Receita                 │
│  (5 fatias)      │  (barras horizontais, cor destaque top 3)    │
│                  │                                               │
└──────────────────┴───────────────────────────────────────────────┘
```

### Especificações por visual

**Cartões de KPI (4x)**
- Tamanho: ~285px × 90px cada
- Fundo: `#F8FAFC` (quase branco)
- Valor principal: 28px, cor `#0F172A`
- Rótulo: 12px, cor `#64748B`
- Variação YoY: 13px — verde `#059669` se positivo, vermelho `#DC2626` se negativo
- Borda esquerda colorida: 3px sólida (use formatação condicional ou shape)

**Gráfico de Linha — Receita Mensal**
- Eixo X: `dCalendario[AnoMesLabel]`
- Eixo Y: `[Receita Total]`  
- Legenda: Ano (2023 = cinza `#94A3B8`, 2024 = azul `#2563EB`)
- Desativar marcadores — linha limpa
- Linha de referência horizontal na média do período
- Adicionar anotação de texto em Nov/2024: "Black Friday"

**Barras Horizontais — Regiões**
- Medida: `[Receita Total]`
- Eixo Y: `Pedidos[regiao]`
- Cor única: `#2563EB`
- Rótulos de dados no final da barra (formato R$ compacto)
- Ordenar: decrescente por receita

**Rosca — Canal de Venda**
- Medida: `[Receita Total]`
- Legenda: `Pedidos[canal]`
- Cores: usar as 5 primeiras da paleta (azul, roxo, verde, âmbar, vermelho)
- Rótulo central: "Canal" (texto fixo) + receita total da seleção

**Barras Verticais — Top 10 Produtos**
- Medida: `[Receita Total]`
- Eixo X: `Pedidos[nome_produto]` (top N = 10 via filtro visual)
- Top 3: cor `#2563EB` | Demais: cor `#CBD5E1`
  → Implementar com medida de formatação condicional ou separar em dois visuais sobrepostos
- Rótulos acima de cada barra

---

## Dashboard 2 — Vendedores

**Narrativa:** quem está batendo meta? Qual a tendência? Onde focar atenção?

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER                [Slicer: Ano]  [Slicer: Vendedor]        │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│ CARTÃO       │ CARTÃO       │ CARTÃO       │ CARTÃO              │
│ Meta Total   │ Realizado    │ Atingimento %│ Acima da Meta       │
│ R$ 846K      │ R$ 712K      │ 84,2%        │ 5 de 8              │
├──────────────────────────────────┬───────────────────────────────┤
│                                  │                               │
│  GRÁFICO DE BARRAS CLUSTERIZADO  │  GRÁFICO DE LINHA            │
│  Meta × Realizado por Vendedor   │  Evolução mensal             │
│                                  │  Meta (tracejado) ×          │
│  - 2 barras por vendedor         │  Realizado (sólido)          │
│  - Meta: cinza | Realiz.: azul   │  Filtrado pelo slicer        │
│  - Linha de referência: 100%     │  de vendedor                 │
│                                  │                               │
├──────────────────────────────────┴───────────────────────────────┤
│                                                                  │
│  TABELA — Ranking de Vendedores                                  │
│  Colunas: Vendedor | Região | Meta | Realizado | Gap R$ |        │
│           Atingimento % | Status (semáforo emoji) | Meses Batendo│
│  Formatação condicional na coluna Atingimento %:                 │
│    >= 100% → fundo verde claro | 80-99% → amarelo | <80% → rosa │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Especificações por visual

**Cartão Atingimento %**
- Mostrar `[Label Atingimento]` (medida com emoji)
- Formatação condicional na cor do valor

**Barras Clusterizadas — Meta × Realizado**
- Eixo X: `MetaRealizado[nome]` (vendedor)
- Valores: `[Meta Total]` e `[Realizado Total]`
- Cores: Meta = `#CBD5E1` (cinza claro), Realizado = `#2563EB` (azul)
- Linha de referência analítica: linha constante no valor médio da meta
- Desativar legenda padrão — criar caixas de texto manuais "Meta" e "Realizado"

**Gráfico de Linha — Evolução Mensal**
- Eixo X: `dCalendario[NomeMes]` (com ordenação por mês numérico)
- Série 1 — Realizado: linha sólida `#2563EB`
- Série 2 — Meta: linha tracejada `#94A3B8`
- Requer slicer de vendedor conectado (filtro cruzado)

**Tabela — Ranking**
- Ordenação padrão: Atingimento % decrescente
- Formatação condicional na coluna "Atingimento %":
  - Escala de cor: vermelho → amarelo → verde (0% a 150%)
- Coluna "Status": usar `[Label Atingimento]` — exibe emoji automaticamente
- Larguras sugeridas: Vendedor 20%, Região 12%, demais automático

---

## Dashboard 3 — Clientes

**Narrativa:** quem é nossa base? Quem está sumindo? Quem tem potencial?

```
┌──────────────────────────────────────────────────────────────────┐
│  HEADER           [Slicer: Segmento]  [Slicer: Região]  [RFM]  │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│ CARTÃO       │ CARTÃO       │ CARTÃO       │ CARTÃO              │
│ Total Clientes│ Ativos 90d  │ Inativos     │ Ticket Médio        │
│ 500          │ 365 (73%)    │ 135 (27%)    │ R$ 2.405            │
├──────────────────────────────────┬───────────────────────────────┤
│                                  │                               │
│  GRÁFICO DE BARRAS HORIZ.        │  SCATTER PLOT                │
│  Clientes por Segmento RFM       │  Recência × Frequência       │
│  (7 segmentos, cor por tipo)     │  Tamanho bolha = Monetário   │
│                                  │  Cor = Segmento RFM          │
│                                  │                               │
├──────────────────────────────────┴───────────────────────────────┤
│                                                                  │
│  GRÁFICO BARRAS — Ticket médio por segmento (Bronze→Diamante)   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TABELA — Top 20 Clientes por Receita                            │
│  Colunas: Cliente | Segmento | Região | Pedidos | Receita |      │
│           Ticket Médio | Segmento RFM | Dias sem Compra          │
│  Formatação condicional em "Dias sem Compra":                    │
│    > 180 → vermelho | 90-180 → amarelo | < 90 → verde           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Especificações por visual

**Barras — Segmento RFM**
- Tabela: `RFM`
- Eixo Y: `RFM[segmento_rfm]`
- Medida: `[Clientes no Segmento RFM]`
- Cores por segmento (formatação condicional por valor de categoria):
  - Campeões → `#2563EB`
  - Clientes Fiéis → `#7C3AED`
  - Potencial → `#059669`
  - Regulares → `#64748B`
  - Em Risco → `#D97706`
  - Hibernando → `#F59E0B`
  - Perdidos → `#DC2626`

**Scatter Plot**
- Eixo X: `RFM[recencia]` (média — use `AVERAGE`)
- Eixo Y: `RFM[frequencia]` (soma)
- Tamanho da bolha: `RFM[monetario]` (soma)
- Detalhes (legenda de cores): `RFM[segmento_rfm]`
- Desativar linha de tendência
- Inverter eixo X (recência: menor = melhor → botão "Inverter eixo" nas propriedades)

**Tabela — Top Clientes**
- Para calcular os dados por cliente, criar medidas usando LOOKUPVALUE ou
  relacionamento RFM → Clientes → Pedidos
- Ordenar por `[Receita Total]` decrescente
- Limitar via Top N no filtro do visual (N = 20)
- Coluna "Dias sem Compra": calcular via medida ou trazer direto da tabela RFM[recencia]

---

## Dicas gerais de layout

**Fundo do relatório**
- Cor: `#F8FAFC` (branco levemente acinzentado — não use branco puro)
- Cartões e visuais: fundo branco `#FFFFFF` com borda 1px `#E2E8F0`

**Tipografia**
- Título dos visuais: Segoe UI Semibold, 13px, cor `#0F172A`
- Rótulos de eixo: Segoe UI, 10px, cor `#64748B`
- Valores em cartões: 22px, cor `#0F172A`
- Rótulos de cartão: 11px, cor `#64748B`

**Slicers**
- Estilo: Lista (não dropdown — visualmente mais profissional)
- Fundo: transparente
- Seleção: cor primária `#2563EB`
- Separar slicers por uma linha divisória sutil

**Título do relatório (header)**
- Retângulo de fundo: `#0F172A` (azul escuro quase preto)
- Texto: branco, 18px, "Inteligência Comercial — [nome do dashboard]"
- Subtítulo: `#94A3B8`, 12px, "Felipe Huff | Dados: Jan 2023 – Dez 2024"
