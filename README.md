# Pipeline de ETL e Análise de Vendas 📊

Este repositório contém um pipeline de dados completo de **Extração, Transformação e Carga (ETL)** desenvolvido em Python, focado em limpeza de dados corporativos de faturamento e geração de KPIs de vendas.

## 🚀 Estrutura do Projeto

* `etl_analysis.py`: Script principal em Python que realiza todo o fluxo de ETL utilizando as bibliotecas **Pandas** e **NumPy**.
* `data/`: Pasta (gerada automaticamente) contendo os dados de entrada brutos (`sales_raw.csv`) e os dados limpos após processamento (`sales_cleaned.csv`).
* `reports/`: Relatórios em formato JSON contendo estatísticas sumárias de faturamento.

## ⚙️ Como Funciona o Pipeline

1. **Extração (Extract)**: 
   * Geração de um conjunto de dados simulado com mais de 1.000 registros de transações (incluindo datas, produtos, quantidades, preços unitários, descontos e métodos de pagamento).
2. **Transformação (Transform)**:
   * Limpeza de valores nulos e inconsistentes.
   * Padronização de datas e categorias de produtos.
   * Cálculo de métricas derivadas (Valor Total de Vendas deduzido de desconto).
   * Detecção de anomalias/outliers utilizando o método IQR (Interquartile Range).
3. **Carga (Load)**:
   * Exportação dos dados transformados e sanitizados em CSV para análise de BI (ex: carregamento no Power BI).
   * Geração de relatórios sumários com estatísticas de vendas por região e produto.

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Pandas** (Estruturação e transformação de dados)
* **NumPy** (Cálculos matemáticos e lógicos)

## 📋 Pré-requisitos & Como Rodar

1. Certifique-se de ter o Python instalado.
2. Instale as dependências:
   ```bash
   pip install pandas numpy
   ```
3. Execute o script:
   ```bash
   python etl_analysis.py
   ```
