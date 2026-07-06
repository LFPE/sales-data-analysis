import os
import json
import random
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class SalesETLPipeline:
    def __init__(self, raw_data_path="data/sales_raw.csv", cleaned_data_path="data/sales_cleaned.csv", report_path="reports/sales_summary.json"):
        self.raw_data_path = raw_data_path
        self.cleaned_data_path = cleaned_data_path
        self.report_path = report_path
        self.logger = self._setup_logging()

    def _setup_logging(self):
        # Configura o registro de logs estruturado
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("pipeline.log", encoding="utf-8")
            ]
        )
        return logging.getLogger("SalesETL")

    def extract(self):
        """Simula a extração de dados brutos e gera o arquivo inicial."""
        self.logger.info("Etapa de Extração iniciada...")
        os.makedirs(os.path.dirname(self.raw_data_path), exist_ok=True)
        
        try:
            random.seed(42)
            np.random.seed(42)

            start_date = datetime.now() - timedelta(days=180)
            dates = [start_date + timedelta(days=random.randint(0, 180)) for _ in range(1200)]

            products = {
                "Notebook Pro": {"category": "Tecnologia", "price": 4500.0},
                "Smartphone X": {"category": "Tecnologia", "price": 2800.0},
                "Monitor 27'": {"category": "Periféricos", "price": 1200.0},
                "Teclado Mecânico": {"category": "Periféricos", "price": 350.0},
                "Mouse Wireless": {"category": "Periféricos", "price": 180.0},
                "Cadeira Gamer": {"category": "Móveis", "price": 950.0},
                "Mesa de Escritório": {"category": "Móveis", "price": 750.0}
            }

            product_names = list(products.keys())
            data = []
            for i in range(1200):
                prod = random.choice(product_names)
                qty = random.randint(1, 5)
                price = products[prod]["price"]
                discount = round(random.uniform(0, 0.25), 2) if random.random() > 0.3 else 0.0
                
                # Valores intencionalmente inválidos para simular dados brutos a serem tratados
                if random.random() > 0.98:
                    discount = random.choice([-0.1, 1.5])
                    
                payment = random.choice(["Cartão de Crédito", "PIX", "Boleto", None])
                region = random.choice(["Sul", "Sudeste", "Centro-Oeste", "Nordeste", "Norte"])
                
                data.append({
                    "ID_Venda": f"V-{1000 + i}",
                    "Data": dates[i].strftime("%Y-%m-%d") if random.random() > 0.05 else dates[i].strftime("%d/%m/%Y"),
                    "Produto": prod,
                    "Quantidade": qty if random.random() > 0.02 else -1,
                    "Preco_Unitario": price,
                    "Desconto": discount,
                    "Metodo_Pagamento": payment,
                    "Regiao": region
                })

            df_raw = pd.DataFrame(data)
            df_raw.to_csv(self.raw_data_path, index=False)
            self.logger.info(f"Dados brutos extraídos com sucesso. Salvo em: {self.raw_data_path}")
            return df_raw
        except Exception as e:
            self.logger.error(f"Erro catastrófico na extração de dados: {e}")
            raise

    def transform(self, df):
        """Aplica as regras de transformação de dados e limpeza."""
        self.logger.info("Etapa de Transformação iniciada...")
        try:
            # 1. Padronização de datas
            def _parse_date(date_str):
                try:
                    if "/" in str(date_str):
                        return pd.to_datetime(date_str, format="%d/%m/%Y")
                    return pd.to_datetime(date_str, format="%Y-%m-%d")
                except Exception:
                    return pd.NaT

            df["Data"] = df["Data"].apply(_parse_date)
            df["Data"] = df["Data"].ffill()

            # 2. Limpeza de valores inválidos de quantidade e desconto
            df.loc[df["Quantidade"] <= 0, "Quantidade"] = 1
            df.loc[(df["Desconto"] < 0) | (df["Desconto"] > 0.5), "Desconto"] = 0.0

            # 3. Tratamento de nulos
            df["Metodo_Pagamento"] = df["Metodo_Pagamento"].fillna("Não Informado")

            # 4. Cálculos financeiros
            df["Faturamento_Bruto"] = df["Quantidade"] * df["Preco_Unitario"]
            df["Faturamento_Liquido"] = df["Faturamento_Bruto"] * (1 - df["Desconto"])

            # 5. Mapeamento de Categoria
            products_categories = {
                "Notebook Pro": "Tecnologia", "Smartphone X": "Tecnologia",
                "Monitor 27'": "Periféricos", "Teclado Mecânico": "Periféricos",
                "Mouse Wireless": "Periféricos", "Cadeira Gamer": "Móveis",
                "Mesa de Escritório": "Móveis"
            }
            df["Categoria"] = df["Produto"].map(products_categories)

            # 6. Detecção de Outliers no Faturamento Líquido (método IQR)
            q1 = df["Faturamento_Liquido"].quantile(0.25)
            q3 = df["Faturamento_Liquido"].quantile(0.75)
            iqr = q3 - q1
            limite_superior = q3 + 1.5 * iqr

            df["Is_Outlier"] = df["Faturamento_Liquido"] > limite_superior
            self.logger.info(f"Dados limpos e transformados. {df['Is_Outlier'].sum()} outliers detectados.")
            return df
        except Exception as e:
            self.logger.error(f"Erro durante a transformação dos dados: {e}")
            raise

    def load(self, df):
        """Salva a base limpa e exporta relatórios sumários."""
        self.logger.info("Etapa de Carga iniciada...")
        try:
            # Salva o dataset final limpo
            df.to_csv(self.cleaned_data_path, index=False)
            self.logger.info(f"Dados limpos carregados com sucesso em: {self.cleaned_data_path}")

            # Gera KPIs e Relatório
            os.makedirs(os.path.dirname(self.report_path), exist_ok=True)
            kpis = {
                "data_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_vendas_registradas": int(df["Quantidade"].sum()),
                "faturamento_total_bruto": float(df["Faturamento_Bruto"].sum()),
                "faturamento_total_liquido": float(df["Faturamento_Liquido"].sum()),
                "ticket_medio": float(df["Faturamento_Liquido"].mean()),
                "regiao_mais_lucrativa": df.groupby("Regiao")["Faturamento_Liquido"].sum().idxmax(),
                "categoria_mais_vendida": df.groupby("Categoria")["Faturamento_Liquido"].sum().idxmax(),
                "kpis_por_regiao": df.groupby("Regiao")["Faturamento_Liquido"].sum().to_dict(),
                "kpis_por_categoria": df.groupby("Categoria")["Faturamento_Liquido"].sum().to_dict()
            }

            with open(self.report_path, "w", encoding="utf-8") as f:
                json.dump(kpis, f, indent=4, ensure_ascii=False)

            self.logger.info(f"Relatório de KPIs salvo em: {self.report_path}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar/carregar dados processados: {e}")
            raise

    def run(self):
        """Executa todo o pipeline de ETL."""
        self.logger.info("=== Executando Pipeline de ETL ===")
        start_time = datetime.now()
        
        raw_df = self.extract()
        transformed_df = self.transform(raw_df)
        self.load(transformed_df)
        
        duration = datetime.now() - start_time
        self.logger.info(f"=== Pipeline concluído com sucesso em {duration.total_seconds():.2f}s ===")

if __name__ == "__main__":
    pipeline = SalesETLPipeline()
    pipeline.run()
