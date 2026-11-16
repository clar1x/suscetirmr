import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

BASE = "data/processed/base_modelagem.csv"
SAIDA = "docs/figuras"
FATORES = ["altitude", "declividade", "norte", "leste", "curvatura", "twi", "acum_log"]
ROTULOS = {
    "altitude": "Altitude (m)",
    "declividade": "Declividade (°)",
    "norte": "Face norte (cos da orientação)",
    "leste": "Face leste (sen da orientação)",
    "curvatura": "Curvatura",
    "twi": "TWI",
    "acum_log": "Fluxo acumulado (log)",
}

base = pd.read_csv(BASE)
base["Classe"] = base["classe"].map({0: "Ausência", 1: "Presença"})

# Caixas sem valores extremos: mostram a distribuição sem expor valores individuais
fig, axes = plt.subplots(2, 4, figsize=(15, 7))
for ax, fator in zip(axes.flat, FATORES):
    sns.boxplot(data=base, x="Classe", y=fator, order=["Ausência", "Presença"],
                color="#9ecae1", showfliers=False, ax=ax)
    ax.set(title=ROTULOS[fator], xlabel="", ylabel="")
axes.flat[-1].axis("off")
plt.tight_layout()
plt.savefig(f"{SAIDA}/eda_boxplots.png", dpi=150)
plt.close()

# Correlação entre fatores: indica redundância (multicolinearidade), como na aula de ML I
corr = base[FATORES].rename(columns=ROTULOS).corr()
fig, ax = plt.subplots(figsize=(8, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1, square=True, ax=ax)
ax.set_title("Correlação entre os fatores condicionantes")
plt.tight_layout()
plt.savefig(f"{SAIDA}/eda_correlacao.png", dpi=150)

print(base.groupby("Classe")[FATORES].median().round(2))
print(corr.round(2))