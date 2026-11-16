# Modelos treinados

Pipelines do scikit-learn (padronização + modelo) para estimar o índice de suscetibilidade a deslizamentos em Recife e Jaboatão dos Guararapes a partir de fatores de terreno.

| Arquivo | Fatores usados |
|---|---|
| `modelos_com_altitude.joblib` | altitude, declividade, norte, leste, curvatura, twi, acum_log |
| `modelos_sem_altitude.joblib` | declividade, norte, leste, curvatura, twi, acum_log |

Cada arquivo contém um dicionário com os modelos treinados (`Baseline`, `Random Forest`, `XGBoost`) e a lista de fatores, na ordem esperada.

## Exemplo de uso

```python
import joblib
import pandas as pd

arquivo = joblib.load("modelos/modelos_sem_altitude.joblib")
modelo = arquivo["modelos"]["XGBoost"]

fatores = pd.DataFrame([{"declividade": 18.0, "norte": 0.4, "leste": -0.2,
                         "curvatura": 0.1, "twi": 6.0, "acum_log": 0.9}],
                       columns=arquivo["fatores"])
print(modelo.predict_proba(fatores)[:, 1])
```

A saída é um índice relativo (0 a 1), não uma probabilidade de ocorrência. Os fatores devem ser calculados como na documentação (MDT a 5 m, média numa janela de 45 m). Desempenho, hiperparâmetros e limitações estão no README da raiz.

Os arquivos `.joblib` são serializações do Python (pickle): carregue-os apenas de fontes confiáveis.