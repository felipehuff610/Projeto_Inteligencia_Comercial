<div align="center">

# 🛒 Inteligência Comercial
### Análise de Vendas & Clientes — Varejo E-commerce Brasil

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Pandas](https://img.shields.io/badge/Pandas-2.0-150458?style=flat-square&logo=pandas&logoColor=white)](https://pandas.pydata.org)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7-11557c?style=flat-square)](https://matplotlib.org)
[![SQL](https://img.shields.io/badge/SQL-SQLite%20%2F%20PostgreSQL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?style=flat-square&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com)
[![Status](https://img.shields.io/badge/Status-Em%20desenvolvimento-F59E0B?style=flat-square)]()

</div>

---

## 📌 Sobre o projeto

Esse projeto nasceu de uma pergunta simples que todo time comercial deveria estar respondendo toda semana:

> *"Estamos crescendo — mas pra quem? E quem sumiu?"*

A partir de dados sintéticos de um e-commerce brasileiro de médio porte (500 clientes, 6.200 pedidos, 2 anos de histórico), construí uma stack analítica completa: geração de dados com Python, limpeza e métricas com Pandas, queries analíticas em SQL e visualização executiva no Power BI.

O objetivo não é só responder às perguntas — é construir um pipeline que possa ser adaptado pra qualquer base de dados real com poucos ajustes.

---

## Perguntas respondidas

| # | Pergunta de negócio | Arquivo |
|---|---|---|
| 1 | Quais clientes estão inativos (+90 dias sem compra)? | `sql/01_clientes_inativos.sql` |
| 2 | Qual o ticket médio por cliente e segmento? | `sql/02_ticket_medio_cliente.sql` |
| 3 | Como está o atingimento de meta por vendedor? | `sql/03_meta_vs_realizado.sql` |
| 4 | Quais produtos são estratégicos (Curva ABC)? | `sql/04_produtos_curva_abc.sql` |
| 5 | Como segmentar clientes por RFM? | `sql/05_rfm_segmentacao.sql` |
| 6 | Qual região está crescendo e qual está em queda? | `sql/06_regioes_performance.sql` |
| 7 | Quem tem potencial de crescimento mas compra pouco? | `notebooks/03_metricas_clientes.py` |

---

## 📁 Estrutura do projeto

```
Projeto_Inteligencia_Comercial/
│
├── dados/
│   ├── brutos/                  # CSVs gerados pelo script Python
│   │   ├── clientes.csv
│   │   ├── pedidos.csv
│   │   ├── produtos.csv
│   │   ├── vendedores.csv
│   │   └── metas.csv
│   ├── processados/             # Dados limpos e enriquecidos
│   │   ├── pedidos_analitico.csv
│   │   ├── rfm_clientes.csv
│   │   └── clientes_inativos.csv
│   └── gerar_dados.py           # Geração de dados sintéticos (Faker)
│
├── notebooks/
│   ├── 01_limpeza_tratamento.py    # Pipeline de limpeza e validação
│   ├── 02_analise_exploratoria.py  # EDA com visualizações
│   └── 03_metricas_clientes.py     # RFM, inativos, potencial de crescimento
│
├── sql/
│   ├── 01_clientes_inativos.sql
│   ├── 02_ticket_medio_cliente.sql
│   ├── 03_meta_vs_realizado.sql
│   ├── 04_produtos_curva_abc.sql
│   ├── 05_rfm_segmentacao.sql
│   └── 06_regioes_performance.sql
│
├── dashboard/                   # Arquivos do Power BI + prints
│   └── graficos_eda/            # Visualizações geradas pelos notebooks
│
├── requirements.txt
└── README.md
```

---

##  Principais insights

A análise de 2 anos revelou alguns padrões importantes:

**Clientes inativos representam 27% da base** — a maioria no segmento Bronze, mas os de maior risco financeiro são os Ouro e Diamante (maior receita histórica, maior custo de substituição).

**A Curva ABC dos produtos** mostrou que apenas 6 SKUs respondem por ~50% da receita. Todos são Eletrônicos — categoria com maior ticket, mas menor margem percentual.

**Sazonalidade marcante**: novembro (Black Friday) e dezembro (Natal) juntos representam ~30% da receita anual. Janeiro e fevereiro despencam — uma oportunidade clara pra campanhas de retenção no começo do ano.

**O canal Site + App Mobile** concentra 65% dos pedidos, mas o WhatsApp, apesar de 10% do volume, tem o maior ticket médio — sinal de que vendas consultivas convertem melhor.

---

## Como executar

###Pré-requisitos:

```bash
git clone https://github.com/felipehuff610/Projeto_Inteligencia_Comercial.git
cd Projeto_Inteligencia_Comercial
pip install -r requirements.txt
```

### Passo a passo

```bash
# 1. Gerar os dados sintéticos
python dados/gerar_dados.py

# 2. Limpar e tratar os dados
python notebooks/01_limpeza_tratamento.py

# 3. Rodar a análise exploratória (gera gráficos em dashboard/graficos_eda/)
python notebooks/02_analise_exploratoria.py

# 4. Calcular métricas de clientes (RFM, inativos, potencial)
python notebooks/03_metricas_clientes.py
```
### SQL

Os arquivos em `sql/` foram escritos com sintaxe SQLite (compatível com DB Browser for SQLite). Para PostgreSQL, substituir `JULIANDAY()` por `DATE_PART('day', ...)` e `STRFTIME()` por `EXTRACT()`.

---

## Stack utilizada

| Ferramenta | Uso |
|---|---|
| **Python 3.11** | Geração de dados, limpeza, análise |
| **Pandas** | Manipulação e transformação de dados |
| **Matplotlib + Seaborn** | Visualizações com paleta customizada |
| **Faker (pt_BR)** | Geração de dados sintéticos realistas |
| **SQL (SQLite/PostgreSQL)** | Queries analíticas com CTEs e Window Functions |
| **Power BI** | Dashboard executivo (em desenvolvimento) |

---

## 🗺️ Roadmap

- [x] Geração de dados sintéticos com Faker
- [x] Pipeline de limpeza e tratamento
- [x] Análise exploratória com visualizações
- [x] Segmentação RFM de clientes
- [x] Queries SQL analíticas (CTE + Window Functions)
- [ ] Dashboard Power BI — executivo
- [ ] Dashboard Power BI — vendedores
- [ ] Dashboard Power BI — clientes
- [ ] Análise de cohort de clientes
- [ ] Modelo preditivo de churn

---

## 👤 Autor

Feito por **Felipe Huff** — Analista de Dados & Desenvolvedor.

[![LinkedIn](https://img.shields.io/badge/https://www.linkedin.com/in/felipe-huff-1b411327b/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat-square&logo=github)](https://github.com/felipehuff610)

---

<div align="center">
<sub>Dados sintéticos gerados com Faker (pt_BR). Qualquer semelhança com dados reais é coincidência.</sub>
</div>
