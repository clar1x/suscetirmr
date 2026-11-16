import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import GroupShuffleSplit

BASE = "data/processed/base_modelagem.csv"
VERSOES = {"Com altitude": "outputs", "Sem altitude": "outputs/sem_altitude"}
BLOCO = 2000
SEED = 42

base = pd.read_csv(BASE)
blocos = (base["x"] // BLOCO).astype(int).astype(str) + "_" + (base["y"] // BLOCO).astype(int).astype(str)

# Mesma divisão espacial do treino: o teste reúne blocos nunca vistos pelo modelo
_, idx_teste = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(base, groups=blocos))
teste = base.iloc[idx_teste]

fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
for ax, (versao, pasta) in zip(axes, VERSOES.items()):
    arquivo = joblib.load(f"{pasta}/modelos.joblib")
    X, y = teste[arquivo["fatores"]], teste["classe"]
    for nome in ["Random Forest", "XGBoost"]:
        prob = arquivo["modelos"][nome].predict_proba(X)[:, 1]
        fpr, tpr, _ = roc_curve(y, prob)
        auc = f"{roc_auc_score(y, prob):.3f}".replace(".", ",")
        ax.plot(fpr, tpr, label=f"{nome} (AUC = {auc})")
    ax.plot([0, 1], [0, 1], "--", color="gray", label="Baseline (AUC = 0,500)")
    ax.set(title=versao, xlabel="Taxa de falsos positivos", ylabel="Taxa de verdadeiros positivos")
    ax.legend(loc="lower right")
plt.tight_layout()
plt.savefig("docs/figuras/curva_roc.png", dpi=150)