import joblib
import matplotlib.pyplot as plt
import pandas as pd
import shap

BASE = "data/processed/base_modelagem.csv"
SAIDA = "outputs/sem_altitude"
ROTULOS = {
    "altitude": "Altitude",
    "declividade": "Declividade",
    "norte": "Face norte (cos da orientação)",
    "leste": "Face leste (sen da orientação)",
    "curvatura": "Curvatura",
    "twi": "Índice topográfico de umidade (TWI)",
    "acum_log": "Fluxo acumulado (log)",
}
INVERSO = {v: k for k, v in ROTULOS.items()}

arquivo = joblib.load(f"{SAIDA}/modelos.joblib")
FATORES = arquivo["fatores"]
base = pd.read_csv(BASE)
X = base[FATORES]
Xr = X.rename(columns=ROTULOS)


def valores_shap(pipe, X):
    """SHAP da classe presença, calculado sobre os fatores já padronizados pelo pipeline."""
    escalado = pd.DataFrame(pipe.named_steps["scaler"].transform(X), columns=X.columns, index=X.index)
    exp = shap.TreeExplainer(pipe.named_steps["modelo"])(escalado, check_additivity=False)
    return exp.values[:, :, 1] if exp.values.ndim == 3 else exp.values


resultado = {}
for nome in ["Random Forest", "XGBoost"]:
    valores = valores_shap(arquivo["modelos"][nome], X)
    resultado[nome] = pd.DataFrame(valores, columns=Xr.columns, index=X.index)
    shap.summary_plot(valores, Xr, show=False)
    plt.title(f"SHAP: {nome}")
    plt.xlabel("Valor SHAP (impacto no índice de suscetibilidade)")
    plt.gcf().axes[-1].set_ylabel("Valor do fator")
    plt.tight_layout()
    plt.savefig(f"{SAIDA}/shap_beeswarm_{nome.replace(' ', '_').lower()}.png", dpi=150)
    plt.close()

importancia = pd.DataFrame({n: df.abs().mean() for n, df in resultado.items()})
importancia.to_csv(f"{SAIDA}/shap_importancia.csv")

por_municipio = resultado["XGBoost"].abs().groupby(base["municipio"]).mean().T
por_municipio.to_csv(f"{SAIDA}/shap_por_municipio.csv")
por_municipio.plot.barh(title="SHAP médio absoluto por município (XGBoost)")
plt.tight_layout()
plt.savefig(f"{SAIDA}/shap_por_municipio.png", dpi=150)
plt.close()

for fator in resultado["XGBoost"].abs().mean().nlargest(3).index:
    shap.dependence_plot(fator, resultado["XGBoost"].values, Xr, show=False)
    plt.tight_layout()
    plt.savefig(f"{SAIDA}/shap_dependencia_{INVERSO[fator]}.png", dpi=150)
    plt.close()

print(importancia.round(3))
print(por_municipio.round(3))
