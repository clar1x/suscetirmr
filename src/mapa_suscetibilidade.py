import geopandas as gpd
import joblib
import numpy as np
import pandas as pd
import rasterio
from affine import Affine
from rasterio.features import geometry_mask
from scipy.ndimage import uniform_filter

PASTA = "data/processed/fatores"
LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
MUNICIPIOS = ["Recife", "Jaboatão dos Guararapes"]
SAIDA = "outputs"
MODELOS = ["Random Forest", "XGBoost"]
JANELA = 9
PASSO = 4

arquivo = joblib.load(f"{SAIDA}/modelos.joblib")
FATORES = arquivo["fatores"]


def ler(nome):
    with rasterio.open(f"{PASTA}/{nome}.tif") as r:
        return r.read(1, masked=True).astype("float32").filled(np.nan)


def media_focal(arr, janela):
    valido = ~np.isnan(arr)
    soma = uniform_filter(np.where(valido, arr, 0), size=janela, mode="constant")
    cont = uniform_filter(valido.astype("float32"), size=janela, mode="constant")
    return np.where(cont > 0, soma / np.maximum(cont, 1e-9), np.nan)


with rasterio.open(f"{PASTA}/declividade.tif") as r:
    crs, transform = r.crs, r.transform

# Mesma média focal usada no treino, depois reamostragem 1:PASSO para o mapa ficar leve
pilha = np.stack([media_focal(ler(n), JANELA)[::PASSO, ::PASSO] for n in FATORES], axis=-1)
transform_ds = transform * Affine.scale(PASSO)

mun = gpd.read_file(LIMITES).to_crs(crs)
mun = mun[mun["NM_MUN"].isin(MUNICIPIOS)]
dentro = geometry_mask(mun.geometry, out_shape=pilha.shape[:2], transform=transform_ds, invert=True)
alvo = dentro & ~np.isnan(pilha).any(axis=-1)
X = pd.DataFrame(pilha[alvo], columns=FATORES)

perfil = dict(driver="GTiff", count=1, crs=crs, transform=transform_ds,
              height=pilha.shape[0], width=pilha.shape[1], compress="deflate")

for nome in MODELOS:
    indice = np.full(pilha.shape[:2], np.nan, dtype="float32")
    indice[alvo] = arquivo["modelos"][nome].predict_proba(X)[:, 1]
    slug = nome.replace(" ", "_").lower()

    with rasterio.open(f"{SAIDA}/suscetibilidade_{slug}.tif", "w", dtype="float32", nodata=np.nan, **perfil) as dst:
        dst.write(indice, 1)

    # Classes por quintis (1 = muito baixa ... 5 = muito alta)
    cortes = np.nanquantile(indice, [0.2, 0.4, 0.6, 0.8])
    classes = np.where(np.isnan(indice), 0, np.digitize(indice, cortes) + 1).astype("uint8")
    with rasterio.open(f"{SAIDA}/classes_{slug}.tif", "w", dtype="uint8", nodata=0, **perfil) as dst:
        dst.write(classes, 1)
    print(nome, "ok:", int(alvo.sum()), "pixels")
