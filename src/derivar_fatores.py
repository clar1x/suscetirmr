import os

import numpy as np
import rioxarray
from xrspatial import aspect, curvature, slope

if not hasattr(np, "in1d"):
    np.in1d = np.isin  # remendo do ebook: pysheds usa np.in1d, removido no numpy 2.x

from pysheds.grid import Grid

MDT = "data/raw/mdt/mdt_rec_jab_5m.tif"
SAIDA = "data/processed/fatores"
RESOLUCAO = 5
DIRMAP = (64, 128, 1, 2, 4, 8, 16, 32)

os.makedirs(SAIDA, exist_ok=True)


def salvar(da, nome):
    da.astype("float32").rio.to_raster(f"{SAIDA}/{nome}.tif", compress="deflate", tiled=True)


dem = rioxarray.open_rasterio(MDT, masked=True).squeeze("band", drop=True)

# Declividade e orientação com xarray-spatial, como na aula de DEM (Week 3)
decl = slope(dem)
asp = aspect(dem)
rad = np.deg2rad(asp.where(asp >= 0))  # pixels planos (-1) viram 0 abaixo

# A orientação é circular (0° = 360°): decompõe em componentes norte e leste
salvar(dem, "altitude")
salvar(decl, "declividade")
salvar(np.cos(rad).fillna(0), "norte")
salvar(np.sin(rad).fillna(0), "leste")
salvar(curvature(dem), "curvatura")

# Hidrologia com pysheds, como na aula: condiciona o MDT, direção D8 e fluxo acumulado
grid = Grid.from_raster(MDT)
dem_grid = grid.read_raster(MDT)
condicionado = grid.resolve_flats(grid.fill_depressions(grid.fill_pits(dem_grid)))
fdir = grid.flowdir(condicionado, dirmap=DIRMAP)
acum = np.asarray(grid.accumulation(fdir, dirmap=DIRMAP), dtype="float64")

salvar(dem.copy(data=np.log10(acum + 1)), "acum_log")

# TWI = ln(área específica / tan(declividade)), com piso na declividade para evitar divisão por zero
tan_beta = np.tan(np.deg2rad(decl)).clip(min=0.001)
salvar(np.log(dem.copy(data=(acum + 1) * RESOLUCAO) / tan_beta), "twi")