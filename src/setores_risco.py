from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.validation import make_valid

SETORES = "data/raw/risco/jaboatao/Shapefile/Setores.shp"
LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
CRS = "EPSG:31985"
SAIDA_WEB = Path("docs/mapa/camadas/setores_risco_jaboatao.geojson")
SAIDA_PROC = "data/processed/setores_risco_jaboatao.gpkg"
PROCESSOS = [f"TIPOLO_G{i}" for i in range(1, 6)]
SIMPLIFICACAO = 2

SAIDA_WEB.parent.mkdir(parents=True, exist_ok=True)

g = gpd.read_file(SETORES).to_crs(CRS)
g["geometry"] = g.geometry.map(make_valid)

# Mantém os setores em que deslizamento é um dos processos mapeados
g = g[g[PROCESSOS].eq("Deslizamento").any(axis=1)].copy()

jab = gpd.read_file(LIMITES).to_crs(CRS)
jab = jab.loc[jab["NM_MUN"] == "Jaboatão dos Guararapes", "geometry"].union_all()
g = g[g.intersects(jab)].copy()
g["geometry"] = g.geometry.intersection(jab)
g = g[~g.geometry.is_empty].copy()

for coluna in ("NUM_EDIF", "NUM_PESS"):
    g[coluna] = pd.to_numeric(g[coluna], errors="coerce")

g["grau"] = g["GRAU_RISCO"]
g["processo"] = np.where(g["TIPOLO_E1"].eq("Deslizamento planar"), "Deslizamento planar", "Deslizamento")
g["situacao"] = g["SITUACAO"]
g["local"] = g["LOCAL"].str.split(",").str[0].str.strip().str.replace(r"^Bairro\s+", "", regex=True)
g["ano"] = pd.to_datetime(g["DATA_SETOR"]).dt.year
g["area_m2"] = g.geometry.area.round(0)

colunas = ["NUM_SETOR", "grau", "processo", "situacao", "local", "ano", "NUM_EDIF", "NUM_PESS", "area_m2", "geometry"]
g[colunas].to_file(SAIDA_PROC, layer="setores", driver="GPKG")

# A camada pública leva só os atributos não sensíveis, com geometria simplificada
web = g[["grau", "processo", "situacao", "local", "ano", "geometry"]].copy()
web["geometry"] = web.geometry.simplify(SIMPLIFICACAO)
web.to_crs("EPSG:4326").to_file(SAIDA_WEB, driver="GeoJSON", COORDINATE_PRECISION=6)

print(len(g), "setores de deslizamento em Jaboatão")
resumo = g.groupby("grau").agg(setores=("grau", "size"), area_ha=("area_m2", lambda s: round(s.sum() / 1e4, 1)),
                               edificacoes=("NUM_EDIF", "sum"), pessoas=("NUM_PESS", "sum"))
print(resumo)
print(g["situacao"].value_counts())
print("área total (ha):", round(g["area_m2"].sum() / 1e4, 1))