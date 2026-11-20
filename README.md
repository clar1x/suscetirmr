# SuscetiRMR

Suscetibilidade a deslizamentos em Recife e Jaboatão dos Guararapes (PE) com Random Forest (RF), XGBoost e interpretação por SHAP, apresentada em um WebGIS.

Projeto final (Capstone) do Future Tech Leaders Brasil, Space Tech Bootcamp 2026.

**WebGIS:** [_Mapa_](https://clar1x.github.io/suscetirmr/mapa/)

## Objetivo

- **Problema:** a ocupação de encostas urbanas e os deslizamentos desafiam o planejamento territorial da Região Metropolitana do Recife (RMR).
- **Tarefa:** classificação supervisionada binária (presença de deslizamento × não ocorrência presumida) a partir de fatores derivados de um modelo digital de terreno.
- **Objetivo específico:** desenvolver e comparar modelos de suscetibilidade, examinar a contribuição das variáveis com SHAP e disponibilizar os mapas resultantes em um WebGIS
- **Escopo.** o recorte inicial contempla Recife e Jaboatão dos Guararapes, os municípios para os quais havia registros históricos de deslizamentos disponíveis para este trabalho. A expansão para a RMR inteira depende de novos registros.

O produto é um mapa de **suscetibilidade**. Ele não substitui análises de risco, que consideram exposição e vulnerabilidade, nem avaliações geotécnicas locais ou sistemas de alerta. O projeto se relaciona aos ODS 11 (Cidades e Comunidades Sustentáveis) e 13 (Ação Contra a Mudança Global do Clima).

## Estrutura do repositório

```
docs/              documentação, política de dados e WebGIS (docs/mapa/)
src/               scripts do pipeline (amostragem, fatores, base, treino, SHAP, mapas, WebGIS)
src/exploratorio/  scripts de inspeção usados na análise exploratória
scripts/           mosaico do MDT com GDAL
modelos/           modelos treinados (RF e XGBoost), com e sem altitude
mapas/             produtos cartográficos
data/              dados de entrada e intermediários (não versionado)
outputs/           métricas, gráficos e mapas gerados (não versionado)
pyproject.toml, uv.lock   dependências
```

## Acesso aos dados

O código, os modelos treinados, os mapas e os demais resultados são abertos. Os registros históricos de deslizamentos usados no treinamento têm acesso restrito: não são exibidos nem disponibilizados para download em nenhuma forma (original, amostra, subconjuntos ou tabelas com os valores nos pontos). Detalhes em [docs/politica_dados.md](docs/politica_dados.md).

| Dado | Uso | Acesso |
|---|---|---|
| Registros históricos de deslizamentos (pontos) | presenças | Restrito |
| MDT PE3D/APAC, 1 m (produzido entre 2014 e 2016) | fatores de terreno | Público ([serviço PE3D](https://www.gov.br/en/state-services/servico_estadual?id=14370)) |
| Limites municipais, IBGE (malha 2024) | recorte e ausências | Público ([Malhas Territoriais](https://ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/15774-malhas.html)) |
| Modelos treinados (`modelos/`) | previsão do índice de suscetibilidade | Aberto |
| Mapas, camadas do WebGIS e gráficos SHAP | produto final | Aberto |

Layout esperado em `data/` (não versionado):

```
data/raw/inventario/    shapefiles dos registros de deslizamentos (restrito)
data/raw/ibge/          PE_Municipios_2024.shp
data/raw/mdt/           mdt_rec_jab_5m.tif (mosaico do MDT, gerado por scripts/mosaico_mdt.sh)
data/processed/         gerado pelos scripts
```

### Reprodução sem o inventário

Quem não tem acesso ao inventário consegue regenerar os fatores e o índice de suscetibilidade a partir do MDT público e dos modelos publicados:

```bash
mkdir -p outputs/sem_altitude
cp modelos/modelos_com_altitude.joblib outputs/modelos.joblib
cp modelos/modelos_sem_altitude.joblib outputs/sem_altitude/modelos.joblib
uv run python src/derivar_fatores.py
uv run python src/mapa_suscetibilidade.py
uv run python src/mapa_sem_altitude.py
```

Os arquivos `.joblib` são serializações do Python (pickle): carregue-os apenas de fontes confiáveis.

## Instalação

Pré-requisitos: Git, [uv](https://docs.astral.sh/uv/) e GDAL de linha de comando (`sudo apt install gdal-bin`).

```bash
git clone https://github.com/clar1x/suscetirmr.git
cd suscetirmr
uv sync
```

## Como executar e reproduzir

Cada etapa lê a saída da anterior. O pipeline completo exige os registros restritos.

```bash
bash scripts/mosaico_mdt.sh data/raw/mdt/mdt_rec_jab_5m.tif <pasta_mdt_recife> <pasta_mdt_jaboatao>
uv run python src/amostragem.py
uv run python src/derivar_fatores.py
uv run python src/montar_base.py
uv run python src/eda_base.py
uv run python src/treinar.py
uv run python src/treinar_sem_altitude.py
uv run python src/eda_figuras.py
uv run python src/curva_roc.py
uv run python src/shap_analise.py
uv run python src/shap_sem_altitude.py
uv run python src/mapa_suscetibilidade.py
uv run python src/mapa_sem_altitude.py
uv run python src/exportar_relevo.py
uv run python src/exportar_webgis.py
uv run python -m http.server 8000 --directory docs/mapa
```

Os caminhos de entrada ficam no bloco de configuração no início de cada script. As sementes aleatórias são fixas (`SEED = 42`), então a amostra e os modelos são reproduzíveis.

## Metodologia (resumo)

1. **Amostragem.** Registros de deslizamentos de 2010 a 2025 em Recife e Jaboatão, sem duplicatas (10 m), com no máximo 5 por célula de 250 m e distância mínima de 25 m (1.500 presenças).
2. **Fatores.** Derivados do MDT (mosaico reamostrado para 5 m): altitude, declividade, orientação (componentes norte e leste), curvatura, TWI e fluxo acumulado (log). Declividade e orientação seguem o método visto no curso (`xarray-spatial`) e o fluxo segue `pysheds`. Extraídos como média numa janela de 45 m, para atenuar a imprecisão posicional dos pontos.
3. **Ausências.** 1.500 pontos sorteados por município, na mesma quantidade das presenças, em pixels com MDT válido e a pelo menos 100 m de qualquer presença.
4. **Modelos.** RF e XGBoost em `Pipeline` com padronização, baseline `DummyClassifier` e `GridSearchCV`, no roteiro da aula de Machine Learning I.
5. **Validação espacial.** Blocos de 2 km: 20% dos blocos reservados para teste (reservados para a avaliação final e não usados no ajuste dos hiperparâmetros) e validação cruzada em 4 folds por bloco (`GroupKFold`), que faz o papel do `TimeSeriesSplit` da aula (Roberts et al., 2017).
6. **Interpretação.** SHAP (`TreeExplainer`) e importância por permutação.
7. **Mapa.** Índice relativo (saída do modelo, 0 a 1) em cinco classes por quintis, calculados na área de relevo não plano. O relevo plano (declividade média abaixo de 1,5°, definido pelo percentil 5 das presenças; 26,9% da área mapeada) aparece em cinza apenas na exibição.
8. **Duas versões.** Com e sem altitude, porque a altitude domina o modelo e funciona em parte como proxy do contexto geomorfológico.

## Resultados

Métricas no conjunto de teste (20% dos blocos espaciais de 2 km, nunca vistos no treino):

| Modelo | Versão | AUC-ROC | Precisão (macro) | Recall (macro) | F1 (macro) | Acurácia |
|:--|:--|--:|--:|--:|--:|--:|
| Random Forest | Com altitude | 0,863 | 0,838 | 0,818 | 0,823 | 0,830 |
| XGBoost | Com altitude | 0,867 | 0,820 | 0,808 | 0,812 | 0,818 |
| Random Forest | Sem altitude | 0,682 | 0,616 | 0,617 | 0,617 | 0,622 |
| XGBoost | Sem altitude | 0,679 | 0,627 | 0,626 | 0,626 | 0,633 |

O baseline (classe constante) tem AUC de 0,500.

- Os dois modelos superam o baseline. RF e XGBoost ficam empatados: a diferença de AUC é de até 0,004, dentro do ruído de um teste com 725 pontos.
- A altitude responde pela maior parte do desempenho. Sem ela, o AUC cai de cerca de 0,86 para 0,68. No SHAP, com altitude, ela domina com folga; sem altitude, a declividade (SHAP médio absoluto de 0,52 a 0,56) e a curvatura (0,23 a 0,24) passam a ser os fatores mais importantes.
- AUC no teste por município (XGBoost): com altitude, Jaboatão 0,881 e Recife 0,824; sem altitude, Jaboatão 0,656 e Recife 0,761.
- Sensibilidade à janela de extração dos fatores (15 m × 45 m): a janela de 45 m elevou o AUC sem altitude de 0,656 para cerca de 0,68 e foi adotada. A janela de extração e a comparação com e sem altitude foram decididas olhando também o desempenho no teste; a validação cruzada apontou a mesma direção apenas na versão sem altitude.
- Validação externa com 178 setores de risco do SGB em Jaboatão: razão de concentração nas classes alta e muito alta de 2,0 com altitude e de 1,1 sem altitude, em relação à área não plana do município.

Distribuição dos registros por classe de suscetibilidade (percentual da área e dos registros; não expõe contagens nem posições):

**Modelo completo (com altitude)**

| Classe | Área (%) | Registros, teste (%) | Registros, todos (%) |
|:--|--:|--:|--:|
| Muito baixa | 14,6 | 0,0 | 0,2 |
| Baixa | 14,6 | 0,7 | 3,8 |
| Média | 14,6 | 15,0 | 14,4 |
| Alta | 14,6 | 33,1 | 28,9 |
| Muito alta | 14,6 | 47,1 | 47,5 |
| Relevo plano (cinza) | 26,9 | 4,2 | 5,2 |

**Somente fatores de terreno (sem altitude)**

| Classe | Área (%) | Registros, teste (%) | Registros, todos (%) |
|:--|--:|--:|--:|
| Muito baixa | 14,6 | 10,5 | 7,6 |
| Baixa | 14,6 | 13,5 | 12,2 |
| Média | 14,6 | 21,6 | 18,9 |
| Alta | 14,6 | 23,3 | 23,0 |
| Muito alta | 14,6 | 27,0 | 33,1 |
| Relevo plano (cinza) | 26,9 | 4,2 | 5,2 |

**Leitura.** Com altitude, as duas classes mais altas (29,2% da área) concentram 80,2% dos registros de teste, e a classe "muito alta" sozinha tem cerca de 3,2 vezes a sua fatia da área; as duas classes mais baixas somam apenas 0,7%. Sem altitude, a ordem das classes se mantém (o percentual de registros cresce de 10,5% a 27,0% da classe muito baixa à muito alta, no teste), mas a separação é mais fraca: as duas classes mais altas concentram 50,3% dos registros de teste, cerca de 1,7 vez a sua fatia da área, e as duas mais baixas ainda retêm 24,0%. Isso é coerente com o AUC (cerca de 0,86 contra 0,68). Os registros no relevo plano (cinza) são 4,2% no teste e 5,2% no total, próximos dos 5% usados para definir o limiar; a pequena diferença vem de a classificação ser feita na grade de 20 m.

Hiperparâmetros e detalhes da validação cruzada estão na página do relatório (`docs/`).

## Limitações

Os mapas representam suscetibilidade e não substituem avaliações geotécnicas locais ou sistemas de alerta.

- **Fatores.** Apenas fatores derivados do MDT. Geologia e uso e cobertura da terra não foram incorporados por escala incompatível; a importância da altitude pode refletir, em parte, essa ausência.
- **Registros e ausências.** Os registros se concentram onde há ocupação e atendimento a ocorrências; as ausências são presumidas e podem incluir deslizamentos não registrados. Áreas sem registros, como a zona rural, não foram validadas.
- **Posição e escala.** Os registros têm incerteza de posição (atenuada pela janela de 45 m), o MDT foi reamostrado de 1 m para 5 m e o PE3D é de 2014 a 2016.
- **Avaliação.** Um único conjunto de teste (725 pontos), sem intervalos de confiança; a janela de extração e a comparação com e sem altitude foram decididas olhando também o teste; a validação externa cobre apenas Jaboatão (setores de risco do SGB) e não é totalmente independente do inventário; não houve validação temporal.
- **Índice.** Não é uma probabilidade calibrada; as classes são quintis, ou seja, posições relativas, não níveis absolutos de perigo.
- **Cobertura.** Apenas Recife e Jaboatão dos Guararapes; a expansão para a RMR depende de novos registros.

## Referências

- Pfaltzgraff, P. A. dos S. (2007). *Mapa de suscetibilidade a deslizamentos na região metropolitana do Recife*. Tese (Doutorado em Geociências), Universidade Federal de Pernambuco, Recife.
- Torres, F. S. de M.; Pfaltzgraff, P. A. dos S. (2024). Construção de mapas de suscetibilidade a deslizamentos com uso de dados de acesso livre: Região Metropolitana do Recife (PE). *Geotecnia*, 160, 25-36. doi:10.14195/2184-8394_160_2
- Reichenbach, P. et al. (2018). A review of statistically-based landslide susceptibility models. *Earth-Science Reviews*, 180, 60-91. doi:10.1016/j.earscirev.2018.03.001
- Merghadi, A. et al. (2020). Machine learning methods for landslide susceptibility studies: a comparative overview of algorithm performance. *Earth-Science Reviews*, 207, 103225. doi:10.1016/j.earscirev.2020.103225
- Zhang, J. et al. (2023). Insights into geospatial heterogeneity of landslide susceptibility based on the SHAP-XGBoost model. *Journal of Environmental Management*, 332, 117357. doi:10.1016/j.jenvman.2023.117357
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography*, 40, 913-929.
- Lundberg, S. M.; Lee, S.-I. (2017). A unified approach to interpreting model predictions. *Advances in Neural Information Processing Systems*, 30.
- Material do curso: ebook do Future Tech Leaders Brasil (<https://ftl-brazil-2026.github.io/ebook/>).

