import json
import shutil
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from rasterio.transform import array_bounds, rowcol
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds
from sklearn.model_selection import GroupShuffleSplit

from utilitarios import ler, media_focal

LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
MUNICIPIOS = ["Recife", "Jaboatão dos Guararapes"]
SAIDA = Path("docs/mapa/camadas")
MODELO = "XGBoost"
JANELA = 9
PASSO = 4
PERCENTIL_PLANO = 5
BLOCO = 2000
SEED = 42
VERSOES = {
    "completo": {"pasta": "outputs", "titulo": "Modelo completo (com altitude)"},
    "terreno": {"pasta": "outputs/sem_altitude", "titulo": "Somente fatores de terreno (sem altitude)"},
}
CORES = {1: (255, 255, 178), 2: (254, 204, 92), 3: (253, 141, 60), 4: (240, 59, 32),
         5: (189, 0, 38), 6: (190, 190, 190)}
ROTULOS = {1: "Muito baixa", 2: "Baixa", 3: "Média", 4: "Alta", 5: "Muito alta", 6: "Relevo plano (cinza)"}

SAIDA.mkdir(parents=True, exist_ok=True)
slug = MODELO.replace(" ", "_").lower()

base = pd.read_csv("data/processed/base_modelagem.csv")
presencas = base[base["classe"] == 1]
limiar_plano = float(np.percentile(presencas["declividade"], PERCENTIL_PLANO))
pct_presencas_planas = round(100 * float((presencas["declividade"] < limiar_plano).mean()), 1)
plano = media_focal(ler("declividade"), JANELA)[::PASSO, ::PASSO] < limiar_plano

# Mesma divisão espacial do treino: os registros de teste são os blocos nunca vistos pelo modelo
blocos = (base["x"] // BLOCO).astype(int).astype(str) + "_" + (base["y"] // BLOCO).astype(int).astype(str)
_, idx_teste = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(base, groups=blocos))
presencas_teste = base.iloc[idx_teste].query("classe == 1")


def classificar(pasta):
    """Quintis do índice na área de relevo não plano; classe 6 = relevo plano."""
    with rasterio.open(f"{pasta}/suscetibilidade_{slug}.tif") as src:
        indice, transform, crs = src.read(1), src.transform, src.crs
    util = ~np.isnan(indice)
    cortes = np.quantile(indice[util & ~plano], [0.2, 0.4, 0.6, 0.8])
    classes = np.where(util, np.digitize(indice, cortes) + 1, 0).astype("uint8")
    classes[util & plano] = 6
    return classes, transform, crs


def classes_nos_pontos(ds, transform, pontos):
    linhas, colunas = rowcol(transform, pontos["x"].values, pontos["y"].values)
    linhas, colunas = np.array(linhas), np.array(colunas)
    dentro = (linhas >= 0) & (linhas < ds.shape[0]) & (colunas >= 0) & (colunas < ds.shape[1])
    valores = np.zeros(len(pontos), dtype="uint8")
    valores[dentro] = ds[linhas[dentro], colunas[dentro]]
    return valores


def percentuais(valores):
    validos = valores[valores > 0]
    return {k: round(100 * float((validos == k).mean()), 1) for k in ROTULOS}


def distribuicao(ds, transform):
    """Percentual da área e dos registros em cada classe, sem expor contagens nem posições."""
    area = percentuais(ds.ravel())
    todos = percentuais(classes_nos_pontos(ds, transform, presencas))
    teste = percentuais(classes_nos_pontos(ds, transform, presencas_teste))
    return [{"classe": ROTULOS[k], "area": area[k], "presencas_teste": teste[k], "presencas_todas": todos[k]}
            for k in ROTULOS]


def exportar(pasta, chave):
    """Reprojeta as classes para EPSG:3857, salva um PNG RGBA e devolve cantos, área plana e distribuição."""
    ds, transform_src, crs_src = classificar(pasta)
    altura_src, largura_src = ds.shape
    transform, largura, altura = calculate_default_transform(
        crs_src, "EPSG:3857", largura_src, altura_src, *array_bounds(altura_src, largura_src, transform_src))
    classes = np.zeros((altura, largura), dtype="uint8")
    reproject(ds, classes, src_transform=transform_src, src_crs=crs_src,
              dst_transform=transform, dst_crs="EPSG:3857", resampling=Resampling.nearest,
              src_nodata=0, dst_nodata=0)
    rgba = np.zeros((altura, largura, 4), dtype="uint8")
    for classe, cor in CORES.items():
        rgba[classes == classe] = (*cor, 255)
    Image.fromarray(rgba).save(SAIDA / f"{chave}.png", optimize=True)
    pct_area_plana = round(100 * float((ds == 6).sum() / (ds > 0).sum()), 1)
    oeste, sul, leste, norte = transform_bounds("EPSG:3857", "EPSG:4326",
                                                *array_bounds(altura, largura, transform))
    coordenadas = [[oeste, norte], [leste, norte], [leste, sul], [oeste, sul]]
    return coordenadas, pct_area_plana, distribuicao(ds, transform_src)


def auc_teste(pasta):
    tabela = pd.read_csv(f"{pasta}/metricas_teste.csv", index_col=0)
    return round(float(tabela.loc[MODELO, "AUC-ROC"]), 3)


config = {}
for chave, v in VERSOES.items():
    coordenadas, pct_area_plana, dist = exportar(v["pasta"], chave)
    config[chave] = {
        "titulo": v["titulo"],
        "imagem": f"camadas/{chave}.png",
        "coordenadas": coordenadas,
        "auc_teste": auc_teste(v["pasta"]),
        "shap": f"camadas/shap_{chave}.png",
        "limiar_plano": round(limiar_plano, 1),
        "pct_area_plana": pct_area_plana,
        "pct_presencas_planas": pct_presencas_planas,
        "distribuicao": dist,
    }
    shutil.copy(f"{v['pasta']}/shap_beeswarm_{slug}.png", SAIDA / f"shap_{chave}.png")

mun = gpd.read_file(LIMITES).to_crs("EPSG:4326")
mun = mun[mun["NM_MUN"].isin(MUNICIPIOS)][["NM_MUN", "geometry"]]
mun.to_file(SAIDA / "limites.geojson", driver="GeoJSON")
(SAIDA / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2))

tabela = pd.concat([pd.DataFrame(c["distribuicao"]).assign(versao=VERSOES[k]["titulo"]) for k, c in config.items()])
tabela.to_csv("outputs/distribuicao_classes.csv", index=False)
print(tabela.to_markdown(index=False))
print(f"limiar plano: {limiar_plano:.2f} graus | presenças no plano: {pct_presencas_planas}%")