import geopandas as gpd
import pandas as pd

pd.set_option("display.max_rows", None)
pd.set_option("display.width", 200)

g = gpd.read_file("data/raw/inventario/Invent_REC_JAB.shp")

print("Colunas:")
print(list(g.columns))

print("\nColunas candidatas a ano/data:")
for c in g.columns:
    if any(k in c.lower() for k in ["ano", "data", "date", "year", "dt"]):
        print(f"\n--- {c} ({g[c].dtype}) | não nulos: {g[c].notna().sum()}")
        print(g[c].dropna().astype(str).value_counts().head(15))

print("\nGeometria:")
print("vazias:", g.geometry.is_empty.sum(), "| nulas:", g.geometry.isna().sum())
print("em (0,0):", ((g.geometry.x == 0) & (g.geometry.y == 0)).sum())
print("limites:", g.total_bounds)
