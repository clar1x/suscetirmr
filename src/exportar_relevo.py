import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import rioxarray
from affine import Affine
from PIL import Image
from rasterio.features import geometry_mask
from rasterio.transform import array_bounds
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds
from xrspatial import hillshade

MDT = "data/raw/mdt/mdt_rec_jab_5m.tif"
LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
MUNICIPIOS = ["Recife", "Jaboatão dos Guararapes"]
SAIDA = Path("docs/mapa/camadas")
FATOR = 2
EXAGERO = 2.0
AZIMUTE = 315
ALTITUDE = 45
PERCENTIL = 98
ALFA_SOMBRA = 0.85
ALFA_LUZ = 0.5
CRS_WEB = "EPSG:3857"

SAIDA.mkdir(parents=True, exist_ok=True)

dem = rioxarray.open_rasterio(MDT, masked=True).squeeze("band", drop=True)
crs = dem.rio.crs
# Médias de blocos 2 x 2 levam o MDT a 10 m: relevo nítido e arquivo leve para a web
dem = dem.coarsen(x=FATOR, y=FATOR, boundary="trim").mean().rio.write_crs(crs)

# Hillshade da aula de DEM (Week 3); o exagero vertical só realça o relevo na exibição
sombra = hillshade(dem * EXAGERO, azimuth=AZIMUTE, angle_altitude=ALTITUDE).values

# Em terreno plano o hillshade vale sen(altitude do sol): o desvio em relação a isso é a sombra (<0) ou a luz (>0)
desvio = sombra - np.sin(np.deg2rad(ALTITUDE))
valido = ~np.isnan(desvio)
escala = np.nanpercentile(np.abs(desvio), PERCENTIL)
contraste = np.clip(desvio / escala, -1, 1).astype("float32")

# O recorte pelos municípios vem depois do cálculo, para não criar artefatos na borda
transform_src = dem.rio.transform(recalc=True)
mun = gpd.read_file(LIMITES).to_crs(crs)
mun = mun[mun["NM_MUN"].isin(MUNICIPIOS)]
dentro = geometry_mask(mun.geometry, out_shape=contraste.shape, transform=transform_src, invert=True)
mantido = dentro & valido
contraste[~mantido] = np.nan

linhas, colunas = np.where(mantido)
l0, l1, c0, c1 = linhas.min(), linhas.max() + 1, colunas.min(), colunas.max() + 1
contraste = contraste[l0:l1, c0:c1]
transform_src = transform_src * Affine.translation(c0, l0)

altura_src, largura_src = contraste.shape
transform, largura, altura = calculate_default_transform(
    crs, CRS_WEB, largura_src, altura_src, *array_bounds(altura_src, largura_src, transform_src))
web = np.full((altura, largura), np.nan, dtype="float32")
reproject(contraste, web, src_transform=transform_src, src_crs=crs, dst_transform=transform,
          dst_crs=CRS_WEB, resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)

# Sombra = preto semitransparente; luz = branco semitransparente; terreno plano fica transparente
valor = np.nan_to_num(web, nan=0.0)
alfa = np.where(valor < 0, -valor * ALFA_SOMBRA, valor * ALFA_LUZ)
alfa[np.isnan(web)] = 0
cor = np.where(valor < 0, 0, 255).astype("uint8")
rgba = np.stack([cor, cor, cor, (alfa * 255).astype("uint8")], axis=-1)
Image.fromarray(rgba).save(SAIDA / "relevo.png", optimize=True)

oeste, sul, leste, norte = transform_bounds(CRS_WEB, "EPSG:4326", *array_bounds(altura, largura, transform))
coordenadas = [[oeste, norte], [leste, norte], [leste, sul], [oeste, sul]]
(SAIDA / "relevo.json").write_text(json.dumps({"imagem": "camadas/relevo.png", "coordenadas": coordenadas}))