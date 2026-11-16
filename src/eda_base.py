import pandas as pd
from sklearn.metrics import roc_auc_score

FATORES = ["altitude", "declividade", "norte", "leste", "curvatura", "twi", "acum_log"]
base = pd.read_csv("data/processed/base_modelagem.csv")

print(base.groupby("classe")[FATORES].median().round(2))

for nome, g in base.groupby("municipio"):
    auc = {f: round(max(a, 1 - a), 3) for f in FATORES for a in [roc_auc_score(g["classe"], g[f])]}
    print(f"\nAUC por fator isolado, {nome}:\n{auc}")
