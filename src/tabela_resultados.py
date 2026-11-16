import pandas as pd

VERSOES = {"Com altitude": "outputs", "Sem altitude": "outputs/sem_altitude"}

linhas = []
for versao, pasta in VERSOES.items():
    tabela = pd.read_csv(f"{pasta}/metricas_teste.csv", index_col=0).drop(index="Baseline")
    tabela.insert(0, "Versão", versao)
    linhas.append(tabela.reset_index(names="Modelo"))

print(pd.concat(linhas).round(3).to_markdown(index=False))