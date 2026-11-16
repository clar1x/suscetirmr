import sys

import geopandas as gpd
import numpy as np
import rasterio

pts = gpd.read_file("data/processed/amostra_deslizamentos.gpkg")

with rasterio.open(sys.argv[1]) as r:
    pts = pts.to_crs(r.crs)
    coords = list(zip(pts.geometry.x, pts.geometry.y))
    vals = np.array([v[0] for v in r.sample(coords)], dtype="float64")

vals[vals < 0] = np.nan
pts["declividade"] = vals

print(pts.groupby("municipio")["declividade"].describe(percentiles=[.01, .02, .05, .1, .25, .5]).round(1))
for limiar in (3, 5, 8, 10):
    print(limiar, "graus:", (pts["declividade"] >= limiar).mean().round(3))
