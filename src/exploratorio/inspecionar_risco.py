import glob

import geopandas as gpd
import pandas as pd

PADROES = ["**/*.shp", "**/*.gpkg", "**/*.geojson", "**/*.json"]
arquivos = sorted({f for p in PADROES for f in glob.glob(f"data/raw/risco/{p}", recursive=True)})

for caminho in arquivos:
    print("\n=====", caminho)
    try:
        g = gpd.read_file(caminho)
    except Exception as erro:
        print("não é um arquivo geográfico legível:", erro)
        continue
    atributos = g.columns.drop("geometry")
    print("feições:", len(g), "| CRS:", g.crs, "| geometria:", dict(g.geom_type.value_counts()))
    print("colunas:", list(atributos))
    for coluna in atributos:
        n = g[coluna].nunique(dropna=True)
        if 0 < n <= 15:
            print(f"\n-- {coluna} ({n} valores)")
            print(g[coluna].value_counts(dropna=False).to_string())
    print("\nprimeiras linhas:")
    print(g[atributos].head(5).T.to_string())

for caminho in sorted(glob.glob("data/raw/risco/**/*.csv", recursive=True)):
    print("\n=====", caminho)
    tabela = pd.read_csv(caminho, sep=None, engine="python", encoding_errors="replace")
    print("linhas:", len(tabela), "| colunas:", list(tabela.columns))
    print(tabela.head(5).T.to_string())