import os

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, GroupKFold, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

BASE = "data/processed/base_modelagem.csv"
FATORES = ["declividade", "norte", "leste", "curvatura", "twi", "acum_log"]
BLOCO = 2000
SEED = 42
METRICA = "roc_auc"
SAIDA = "outputs/sem_altitude"

os.makedirs(SAIDA, exist_ok=True)
base = pd.read_csv(BASE)
X, y = base[FATORES], base["classe"]
blocos = (base["x"] // BLOCO).astype(int).astype(str) + "_" + (base["y"] // BLOCO).astype(int).astype(str)

# Teste = 20% dos blocos espaciais, usado uma única vez ao final (equivalente ao split temporal da aula)
idx_train, idx_test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(X, y, blocos))
X_train, y_train, g_train = X.iloc[idx_train], y.iloc[idx_train], blocos.iloc[idx_train]
X_test, y_test = X.iloc[idx_test], y.iloc[idx_test]
cv = GroupKFold(n_splits=4)
print(f"treino: {len(X_train)} | teste: {len(X_test)} | blocos: {blocos.nunique()}")


def pipeline(modelo):
    return Pipeline([("scaler", StandardScaler()), ("modelo", modelo)])


modelos = {
    "Random Forest": (
        pipeline(RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1)),
        {"modelo__max_depth": [3, 5, 10, None],
         "modelo__min_samples_leaf": [1, 5, 10],
         "modelo__max_features": ["sqrt", 0.5]},
    ),
    "XGBoost": (
        pipeline(XGBClassifier(random_state=SEED, n_jobs=-1, eval_metric="logloss")),
        {"modelo__n_estimators": [100, 300],
         "modelo__learning_rate": [0.03, 0.1],
         "modelo__max_depth": [2, 4, 6],
         "modelo__subsample": [0.8, 1.0]},
    ),
}

resumo = []
finais = {"Baseline": pipeline(DummyClassifier(strategy="constant", constant=1)).fit(X_train, y_train)}
for nome, (pipe, grade) in modelos.items():
    busca = GridSearchCV(pipe, grade, cv=cv, scoring=METRICA, refit=False, n_jobs=-1)
    busca.fit(X_train, y_train, groups=g_train)
    finais[nome] = clone(pipe).set_params(**busca.best_params_).fit(X_train, y_train)
    print(f"{nome:<15} {METRICA} na validação = {busca.best_score_:.3f}  {busca.best_params_}")
    resumo.append({
        "Modelo": nome,
        "AUC validação": round(busca.best_score_, 3),
        "Hiperparâmetros": ", ".join(f"{k.replace('modelo__', '')}={v}" for k, v in busca.best_params_.items()),
    })

pd.DataFrame(resumo).to_csv(f"{SAIDA}/hiperparametros.csv", index=False)


def metricas(modelo, X, y):
    pred = modelo.predict(X)
    return {
        "AUC-ROC": roc_auc_score(y, modelo.predict_proba(X)[:, 1]),
        "Precisão (macro)": precision_score(y, pred, average="macro", zero_division=0),
        "Recall (macro)": recall_score(y, pred, average="macro"),
        "F1 (macro)": f1_score(y, pred, average="macro"),
        "Acurácia": accuracy_score(y, pred),
    }


tabela = pd.DataFrame({n: metricas(m, X_test, y_test) for n, m in finais.items()}).T.round(3)
print("\nTeste (blocos nunca vistos):")
print(tabela)
tabela.to_csv(f"{SAIDA}/metricas_teste.csv")

municipios = base.loc[X_test.index, "municipio"]
for nome in ["Random Forest", "XGBoost"]:
    por_mun = {m: round(roc_auc_score(y_test[municipios == m],
                                      finais[nome].predict_proba(X_test[municipios == m])[:, 1]), 3)
               for m in municipios.unique()}
    print(f"{nome}, AUC no teste por município: {por_mun}")

fig, axes = plt.subplots(1, len(finais), figsize=(4 * len(finais), 4))
for ax, (nome, m) in zip(axes, finais.items()):
    ConfusionMatrixDisplay(confusion_matrix(y_test, m.predict(X_test)),
                           display_labels=["Ausência", "Presença"]).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(nome)
    ax.grid(False)
plt.tight_layout()
plt.savefig(f"{SAIDA}/matrizes_confusao.png", dpi=150)

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, nome in zip(axes, ["Random Forest", "XGBoost"]):
    imp = permutation_importance(finais[nome], X_train, y_train, scoring=METRICA,
                                 n_repeats=30, random_state=SEED, n_jobs=-1).importances_mean
    pd.Series(imp, index=FATORES).sort_values().plot.barh(ax=ax, title=nome)
    ax.set_xlabel("Queda média do AUC ao embaralhar (treino)")
plt.tight_layout()
plt.savefig(f"{SAIDA}/importancia_permutacao.png", dpi=150)

joblib.dump({"modelos": finais, "fatores": FATORES}, f"{SAIDA}/modelos.joblib")