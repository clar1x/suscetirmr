import glob
import sys
from collections import Counter

import rasterio

arquivos = sorted(glob.glob(sys.argv[1]))
combinacoes = Counter()
for a in arquivos:
    with rasterio.open(a) as r:
        combinacoes[(str(r.crs), r.res, r.dtypes[0], r.nodata)] += 1

print(len(arquivos), "arquivos")
for chave, n in combinacoes.items():
    print(n, chave)
