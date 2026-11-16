import numpy as np
import rasterio
from scipy.ndimage import uniform_filter

PASTA_FATORES = "data/processed/fatores"


def ler(nome, pasta=PASTA_FATORES):
    with rasterio.open(f"{pasta}/{nome}.tif") as r:
        return r.read(1, masked=True).astype("float32").filled(np.nan)


def media_focal(arr, janela):
    """Média numa janela janela x janela ignorando NaN."""
    valido = ~np.isnan(arr)
    soma = uniform_filter(np.where(valido, arr, 0), size=janela, mode="constant")
    cont = uniform_filter(valido.astype("float32"), size=janela, mode="constant")
    return np.where(cont > 0, soma / np.maximum(cont, 1e-9), np.nan)
