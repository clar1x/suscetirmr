#!/usr/bin/env bash
set -euo pipefail

saida="$1"
shift
resolucao="${RESOLUCAO:-5}"

for pasta in "$@"; do ls "$pasta"/*.tif; done > /tmp/lista_mdt.txt
gdalbuildvrt -input_file_list /tmp/lista_mdt.txt -srcnodata -9999 -vrtnodata -9999 /tmp/mdt.vrt
gdalwarp -tr "$resolucao" "$resolucao" -r average -srcnodata -9999 -dstnodata -9999 -multi \
  -co COMPRESS=DEFLATE -co TILED=YES -co BIGTIFF=YES /tmp/mdt.vrt "$saida"