# Guia Power BI — Modelo de Dados e Conexão
**Projeto Inteligência Comercial | Felipe Huff**

---

## 1. Quais arquivos carregar

Abra o Power BI Desktop e vá em **Página Inicial → Obter Dados → Texto/CSV**.  
Carregue os seguintes arquivos da pasta `dados/processados/`:


> **Não carregar** os demais CSVs (analitico, inativos, potencial) — tudo isso será calculado
> por medidas DAX. Manter o modelo enxuto evita ambiguidade nos relacionamentos.

## 2. Ajustes no Power Query (antes de fechar)

Para cada tabela, faça estes ajustes no **Editor do Power Query**:

### Tabela Pedidos
- `data_pedido` → tipo **Data**
- `valor_total`, `preco_unitario`, `custo` → tipo **Número decimal fixo**
- `desconto_perc` → tipo **Número decimal** (vai de 0 a 1)
- `quantidade` → tipo **Número inteiro**
- `ano`, `mes`, `trimestre` → tipo **Número inteiro**

### Tabela Clientes
- `data_cadastro` → tipo **Data**
- `ativo` → tipo **Número inteiro**

### Tabela MetaRealizado
- `meta_valor`, `realizado` → tipo **Número decimal fixo**
- `ano`, `mes` → tipo **Número inteiro**

### Tabela RFM
- `recencia`, `frequencia` → tipo **Número inteiro**
- `monetario` → tipo **Número decimal fixo**
- `score_r`, `score_f`, `score_m`, `rfm_total` → tipo **Número inteiro**

## 3. Criar a tabela dCalendario (obrigatório)

No Power BI, uma tabela de datas dedicada é essencial para análises temporais corretas
(YoY, MTD, acumulados). Crie via **Modelagem → Nova Tabela** e cole:

```dax
dCalendario = 
ADDCOLUMNS(
    CALENDAR(DATE(2023,1,1), DATE(2024,12,31)),
    "Ano",           YEAR([Date]),
    "Mes",           MONTH([Date]),
    "NomeMes",       FORMAT([Date], "MMM", "pt-BR"),
    "NomeMesLongo",  FORMAT([Date], "MMMM", "pt-BR"),
    "Trimestre",     "T" & QUARTER([Date]),
    "AnoMes",        FORMAT([Date], "YYYY-MM"),
    "AnoMesLabel",   FORMAT([Date], "MMM/YY", "pt-BR"),
    "DiaSemana",     WEEKDAY([Date], 2),
    "NomeDia",       FORMAT([Date], "ddd", "pt-BR"),
    "Semana",        WEEKNUM([Date]),
    "EhFimDeSemana", IF(WEEKDAY([Date],2) >= 6, 1, 0)
)
```
Depois marque a coluna `[Date]` como **Tabela de Datas**:  
com botão direito na tabela → Marcar como Tabela de Datas → selecionar `Date`.

## 4. Ordem de criação dos visuais por dashboard

### Dashboard Executivo (página 1)
Crie nesta ordem para facilitar o alinhamento:

1. Cartões de KPI (linha superior): Receita Total, Pedidos, Ticket Médio, Margem Bruta
2. Gráfico de linha: Receita por mês (eixo X = dCalendario[AnoMesLabel])
3. Gráfico de barras horizontais: Receita por Região
4. Gráfico de barras verticais: Top 10 Produtos
5. Gráfico de rosca: Share por Canal de Venda
6. Segmentadores: Ano, Trimestre, Categoria

### Dashboard Vendedores (página 2)
1. Cartões: Meta Total, Realizado, % Atingimento, Vendedores acima da meta
2. Gráfico de barras: Atingimento % por Vendedor (com linha de referência a 100%)
3. Gráfico de linha: Evolução mensal realizado × meta (por vendedor selecionado)
4. Tabela: Ranking detalhado por vendedor (meta, realizado, gap, atingimento)
5. Segmentadores: Ano, Vendedor, Região

### Dashboard Clientes (página 3)
1. Cartões: Total Clientes, Ativos (compraram em 2024), Inativos +90 dias, Ticket Médio
2. Gráfico de barras horizontais: Clientes por segmento RFM
3. Scatter plot: Recência × Frequência (tamanho = valor monetário)
4. Tabela: Top 20 clientes por receita (com segmento RFM e dias sem compra)
5. Gráfico de barras: Ticket médio por segmento (Bronze, Prata, Ouro, Diamante)
6. Segmentadores: Segmento, Região, Segmento RFM

## 5. Paleta de cores recomendada

Use esta paleta no **Tema do relatório** para manter consistência com os gráficos Python:

| Uso | Cor HEX |
|---|---|
| Primária (destaque) | `#2563EB` |
| Secundária | `#7C3AED` |
| Sucesso / positivo | `#059669` |
| Alerta / atenção | `#D97706` |
| Perigo / negativo | `#DC2626` |
| Neutro / cinza | `#64748B` |
| Fundo de cartões | `#F8FAFC` |
| Texto principal | `#0F172A` |

Para aplicar: **Exibição → Temas → Personalizar tema atual** → cole os HEX nos campos de cor.

------

## Próximo passo

Com o modelo montado, abra o arquivo `02_medidas_dax.md` e cole as medidas
na tabela de medidas dedicada (`_Medidas`).
