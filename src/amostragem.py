import geopandas as gpd
import pandas as pd

FONTES = [
    ("data/raw/inventario/Invent_REC_JAB.shp", "ANO_1", 2010, 2022),
    ("data/raw/inventario/RMRInventario2019_2025rev1_OK.shp", "Ano_1", 2019, 2025),
]
LIMITES = "data/raw/ibge/PE_Municipios_2024.shp"
MUNICIPIOS = ["Recife", "Jaboatão dos Guararapes"]
SAIDA = "data/processed/amostra_deslizamentos.gpkg"
CRS = "EPSG:31985"
TOL_DUPLICATA = 10
CELULA = 250
MAX_POR_CELULA = 5
DIST_MIN = 25
N_ALVO = 1500
SEED = 42


def carregar(caminho, coluna, ano_min, ano_max):
    """Lê o shapefile, descarta geometrias nulas, reprojeta e mantém só o ano dentro do período."""
    g = gpd.read_file(caminho)
    g = g[~(g.geometry.isna() | g.geometry.is_empty)].to_crs(CRS)
    ano = pd.to_numeric(g[coluna], errors="coerce").astype("Int64")
    g = gpd.GeoDataFrame({"ano": ano}, geometry=g.geometry, crs=CRS)
    return g[g.ano.between(ano_min, ano_max)]


def desbastar(gdf, dist):
    """Mantém apenas pontos separados por pelo menos 'dist' metros."""
    gdf = gdf.sample(frac=1, random_state=SEED).reset_index(drop=True)
    indice = gdf.sindex
    removidos = set()
    for i, geom in enumerate(gdf.geometry):
        if i not in removidos:
            vizinhos = indice.query(geom.buffer(dist), predicate="intersects")
            removidos.update(int(j) for j in vizinhos if j != i)
    return gdf.drop(index=list(removidos)).reset_index(drop=True)


log = []


def registrar(etapa, gdf):
    log.append((etapa, len(gdf)))
    print(f"{etapa:<30}{len(gdf):>8}")


# Junta os dois levantamentos, cada um restrito ao seu período
pts = pd.concat([carregar(*f) for f in FONTES], ignore_index=True)
registrar("Pontos no período", pts)

mun = gpd.read_file(LIMITES).to_crs(CRS)
mun = mun.loc[mun["NM_MUN"].isin(MUNICIPIOS), ["NM_MUN", "geometry"]]
pts = gpd.sjoin(pts, mun, predicate="within").drop(columns="index_right")
registrar("Recife e Jaboatão", pts)

# O mesmo evento pode constar nos dois levantamentos: remove duplicatas
pts = desbastar(pts, TOL_DUPLICATA)
registrar("Sem duplicatas", pts)

# Limita o número de pontos por célula para reduzir a concentração espacial
pts = pts.sample(frac=1, random_state=SEED).reset_index(drop=True)
celulas = [pts.geometry.x // CELULA, pts.geometry.y // CELULA]
pts = pts[pts.groupby(celulas).cumcount() < MAX_POR_CELULA]
registrar("Limite por célula", pts)

# Distância mínima entre pontos: reduz a autocorrelação espacial
pts = desbastar(pts, DIST_MIN)
registrar("Distância mínima", pts)

if len(pts) > N_ALVO:
    pts = pts.sample(N_ALVO, random_state=SEED)
registrar("Amostra final", pts)

saida = pts.rename(columns={"NM_MUN": "municipio"})[["ano", "municipio", "geometry"]]
saida.to_file(SAIDA, layer="pontos", driver="GPKG")
pd.DataFrame(log, columns=["etapa", "n"]).to_csv("data/processed/log_amostragem.csv", index=False)
print(saida.groupby(["municipio", "ano"]).size().unstack(fill_value=0))