import geopandas as gpd
import glob

for f in sorted(glob.glob("data/raw/inventario/*.shp")):
    g = gpd.read_file(f)
    print("\n=====", f)
    print("registros:", len(g), "| CRS:", g.crs)
    print(g.drop(columns="geometry").dtypes)
    print(g.drop(columns="geometry").head(5))
