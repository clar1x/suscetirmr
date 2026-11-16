# Política de dados

## Princípio

O código, os modelos treinados, os mapas de suscetibilidade e os demais resultados do projeto são abertos. A única restrição é aos registros de deslizamentos usados no treinamento, que não podem ser disponibilizados para download nem exibidos, em nenhuma forma.

## Conteúdo aberto

- Código-fonte do pipeline, dos scripts e do WebGIS.
- Modelos treinados (Random Forest e XGBoost) e seus hiperparâmetros.
- Mapas de suscetibilidade e as camadas exibidas no WebGIS.
- Gráficos SHAP, métricas de desempenho e documentação metodológica.
- A distribuição percentual dos registros por classe de suscetibilidade, sem exibir os pontos.
- Dados públicos de entrada (MDT PE3D/APAC e limites do IBGE) e os fatores derivados deles.

## Conteúdo restrito

Não publicar, exibir no mapa nem disponibilizar para download:

- Os registros de deslizamentos: pontos e polígonos das ocorrências, coordenadas, endereços e identificadores.
- Qualquer subconjunto ou amostra desses registros, em qualquer formato.
- Tabelas com a posição dos registros ou com os valores dos fatores nos pontos de ocorrência, pois permitem reencontrar a localização cruzando com os rasters.
- Anexos de issues, pull requests e releases que contenham esse conteúdo.

## Critério para produtos derivados

Os produtos derivados só são divulgados se não permitirem a identificação ou a reconstrução dos registros restritos. Mapas em classes, gráficos agregados, percentuais por classe e modelos de árvores (que guardam limiares sobre os fatores, e não os pontos) atendem a esse critério. Tabelas por ocorrência, não.

## Revisão antes da publicação

Antes de cada commit, verificar os arquivos e as saídas incluídas (`git status` e `git diff --cached --stat`). A mesma revisão se aplica a anexos de issues, pull requests e releases.

O `.gitignore` é uma proteção complementar e não impede a publicação de arquivos já rastreados pelo Git.