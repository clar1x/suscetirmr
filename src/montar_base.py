import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import rowcol, xy
from scipy.ndimage import uniform_filter

PONTOS = "data/processed/amostra_deslizamentos.gpkg"
LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
MUNICIPIOS = ["Recife", "Jaboatão dos Guararapes"]
PASTA = "data/processed/fatores"
FATORES = ["altitude", "declividade", "norte", "leste", "curvatura", "twi", "acum_log"]
JANELA = 9
BUFFER_AUSENCIA = 100
SEED = 42


def ler(nome):
    with rasterio.open(f"{PASTA}/{nome}.tif") as r:
        return r.read(1, masked=True).astype("float32").filled(np.nan)


def media_focal(arr, janela):
    """Média numa janela janela x janela ignorando NaN; atenua a imprecisão posicional dos pontos."""
    valido = ~np.isnan(arr)
    soma = uniform_filter(np.where(valido, arr, 0), size=janela, mode="constant")
    cont = uniform_filter(valido.astype("float32"), size=janela, mode="constant")
    return np.where(cont > 0, soma / np.maximum(cont, 1e-9), np.nan)


with rasterio.open(f"{PASTA}/declividade.tif") as r:
    transform, crs, forma = r.transform, r.crs, r.shape

pres = gpd.read_file(PONTOS).to_crs(crs)
mun = gpd.read_file(LIMITES).to_crs(crs)
mun = mun[mun["NM_MUN"].isin(MUNICIPIOS)][["NM_MUN", "geometry"]]

valido = ~np.isnan(ler("altitude"))
longe = ~geometry_mask(pres.geometry.buffer(BUFFER_AUSENCIA), out_shape=forma,
                       transform=transform, invert=True)

# Ausências sorteadas por município, na mesma quantidade das presenças, em pixels
# válidos e a pelo menos BUFFER_AUSENCIA m de qualquer presença
rng = np.random.default_rng(SEED)
ausencias = []
for nome, n in pres["municipio"].value_counts().items():
    dentro = geometry_mask(mun.loc[mun["NM_MUN"] == nome].geometry, out_shape=forma,
                           transform=transform, invert=True)
    lin, col = np.nonzero(dentro & valido & longe)
    sorteio = rng.choice(len(lin), size=n, replace=False)
    xs, ys = xy(transform, lin[sorteio], col[sorteio])
    ausencias.append(gpd.GeoDataFrame({"municipio": [nome] * n},
                                      geometry=gpd.points_from_xy(xs, ys), crs=crs))

aus = pd.concat(ausencias, ignore_index=True).assign(classe=0)
pres = pres.assign(classe=1)
base = pd.concat([pres[["classe", "ano", "municipio", "geometry"]], aus], ignore_index=True)

linhas, colunas = rowcol(transform, base.geometry.x.values, base.geometry.y.values)
linhas, colunas = np.array(linhas), np.array(colunas)
for nome in FATORES:
    base[nome] = media_focal(ler(nome), JANELA)[linhas, colunas]

base["x"] = base.geometry.x
base["y"] = base.geometry.y
base.to_file("data/processed/base_modelagem.gpkg", layer="pontos", driver="GPKG")
base.drop(columns="geometry").to_csv("data/processed/base_modelagem.csv", index=False)

print(base.groupby(["classe", "municipio"]).size())
print(base[FATORES].isna().sum())
