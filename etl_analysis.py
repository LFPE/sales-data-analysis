import os
import json
import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configuração do ambiente
os.makedirs("data", exist_ok=True)
os.makedirs("reports", exist_ok=True)

print("--- INICIANDO PIPELINE DE ETL ---")

# ==========================================
# 1. ETAPA DE EXTRAÇÃO (MOCK DATA)
# ==========================================
print("[Extract] Gerando base de dados de vendas simulada...")

random.seed(42)
np.random.seed(42)

# Gerador de datas aleatórias nos últimos 6 meses
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
    # Adiciona algumas inconsistências de desconto para serem limpas na transformação
    discount = round(random.uniform(0, 0.25), 2) if random.random() > 0.3 else 0.0
    if random.random() > 0.98: # 2% de chance de desconto inválido (negativo ou > 100%)
        discount = random.choice([-0.1, 1.5])
        
    payment = random.choice(["Cartão de Crédito", "PIX", "Boleto", None]) # Alguns valores nulos
    region = random.choice(["Sul", "Sudeste", "Centro-Oeste", "Nordeste", "Norte"])
    
    data.append({
        "ID_Venda": f"V-{1000 + i}",
        "Data": dates[i].strftime("%Y-%m-%d") if random.random() > 0.05 else dates[i].strftime("%d/%m/%Y"), # Mistura de formatos de data
        "Produto": prod,
        "Quantidade": qty if random.random() > 0.02 else -1, # 2% de valores inválidos (negativos)
        "Preco_Unitario": price,
        "Desconto": discount,
        "Metodo_Pagamento": payment,
        "Regiao": region
    })

# Cria DataFrame bruto e salva
df_raw = pd.DataFrame(data)
raw_path = os.path.join("data", "sales_raw.csv")
df_raw.to_csv(raw_path, index=False)
print(f"[Extract] Dados brutos salvos em '{raw_path}' ({len(df_raw)} registros).")


# ==========================================
# 2. ETAPA DE TRANSFORMAÇÃO
# ==========================================
print("[Transform] Iniciando limpeza e transformação dos dados...")

# Carrega os dados brutos para processar
df = pd.read_csv(raw_path)

# A. Padronização de datas
def parse_date(date_str):
    try:
        if "/" in date_str:
            return pd.to_datetime(date_str, format="%d/%m/%Y")
        return pd.to_datetime(date_str, format="%Y-%m-%d")
    except Exception:
        return pd.NaT

df["Data"] = df["Data"].apply(parse_date)
# Preenche datas nulas (se houver) com a data anterior (forward fill)
df["Data"] = df["Data"].ffill()

# B. Limpeza de valores numéricos inválidos (ex: Quantidade negativa)
# Substitui quantidades negativas por 1 (quantidade padrão mínima)
df.loc[df["Quantidade"] <= 0, "Quantidade"] = 1

# C. Limpeza de Descontos inválidos (devem estar entre 0% e 50%)
df.loc[(df["Desconto"] < 0) | (df["Desconto"] > 0.5), "Desconto"] = 0.0

# D. Tratamento de nulos no Método de Pagamento
df["Metodo_Pagamento"] = df["Metodo_Pagamento"].fillna("Não Informado")

# E. Cálculos de negócio: Faturamento Total Bruto e Líquido
df["Faturamento_Bruto"] = df["Quantidade"] * df["Preco_Unitario"]
df["Faturamento_Liquido"] = df["Faturamento_Bruto"] * (1 - df["Desconto"])

# F. Adicionando categoria do produto
product_categories = {name: info["category"] for name, info in products.items()}
df["Categoria"] = df["Produto"].map(product_categories)

# G. Detecção de Outliers no Faturamento Líquido (usando IQR)
q1 = df["Faturamento_Liquido"].quantile(0.25)
q3 = df["Faturamento_Liquido"].quantile(0.75)
iqr = q3 - q1
limite_superior = q3 + 1.5 * iqr

df["Is_Outlier"] = df["Faturamento_Liquido"] > limite_superior
print(f"[Transform] Detecção de outliers concluída (limite: R$ {limite_superior:.2f}). {df['Is_Outlier'].sum()} outliers marcados.")


# ==========================================
# 3. ETAPA DE CARGA E RELATÓRIO
# ==========================================
print("[Load] Salvando dados limpos e gerando relatórios corporativos...")

# Salva arquivo limpo final
cleaned_path = os.path.join("data", "sales_cleaned.csv")
df.to_csv(cleaned_path, index=False)
print(f"[Load] Base de dados sanitizada salva em '{cleaned_path}'.")

# Geração de KPIs sumários em JSON
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

report_path = os.path.join("reports", "sales_summary.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(kpis, f, indent=4, ensure_ascii=False)

print(f"[Load] Relatório de métricas salvo em '{report_path}'.")
print("--- PIPELINE CONCLUÍDO COM SUCESSO ---")
