import numpy as np
import rasterio
from PIL import Image

with rasterio.open("data/raw/mdt/mdt_rec_jab_5m.tif") as r:
    print("MDT:", r.crs, r.shape, r.res, r.bounds)
    amostra = r.read(1, masked=True, out_shape=(r.height // 20, r.width // 20))
    print("MDT, fração válida:", round(float(1 - np.ma.getmaskarray(amostra).mean()), 3))

with rasterio.open("data/processed/fatores/altitude.tif") as r:
    print("altitude:", r.crs, r.shape, r.res, r.bounds)

png = np.array(Image.open("docs/mapa/camadas/relevo.png"))
print("PNG:", png.shape, "fração opaca:", round(float((png[..., 3] > 0).mean()), 3))