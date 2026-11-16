import geopandas as gpd

g = gpd.read_file("data/raw/inventario/RMRInventario2019_2025rev1_OK.shp")
print(len(g), g.geometry.isna().sum())
print(g["Ano_1"].value_counts(dropna=False).sort_index())
