import pandas as pd

VERSOES = {"Com altitude": "outputs", "Sem altitude": "outputs/sem_altitude"}

for versao, pasta in VERSOES.items():
    print(f"\n{versao}\n")
    print(pd.read_csv(f"{pasta}/hiperparametros.csv").to_markdown(index=False))