# SuscetiRMR

Projeto de WebGIS para modelagem da suscetibilidade a deslizamentos
na Região Metropolitana do Recife (RMR), com Random Forest (RF),
XGBoost e interpretação dos modelos por SHAP.

## Estágio atual

O projeto está em organização inicial. A metodologia será detalhada
e os códigos e produtos serão incorporados conforme seu desenvolvimento.

## Objetivo

Desenvolver e comparar modelos de suscetibilidade a deslizamentos,
examinar a contribuição das variáveis com SHAP e disponibilizar
os mapas resultantes em um WebGIS.

O recorte inicial previsto contempla Recife e Jaboatão dos Guararapes.

## Etapas previstas

1. Organizar as fontes e avaliar a qualidade e a cobertura do inventário.
2. Selecionar e preparar as variáveis condicionantes, compatibilizando
   projeção, resolução espacial e extensão.
3. Definir a amostragem e a estratégia de validação, considerando
   a dependência espacial e evitando vazamento entre treino e avaliação.
4. Ajustar e comparar RF e XGBoost sob o mesmo protocolo de avaliação.
5. Aplicar SHAP para interpretar a contribuição das variáveis
   nas predições dos modelos.
6. Produzir os mapas, documentar suas limitações e preparar
   as camadas autorizadas para publicação no WebGIS.

## Organização prevista

- docs/: documentação metodológica e política de dados.
- src/: código desenvolvido para as etapas de análise.
- dados/derivados/: produtos derivados autorizados para divulgação.
- mapas/: produtos cartográficos destinados à publicação.

## Acesso aos dados

O inventário de deslizamentos é de acesso restrito e não será
publicado neste repositório nem disponibilizado pelo WebGIS.
Seu uso e compartilhamento dependem de autorização dos responsáveis.

Os mapas de suscetibilidade serão publicados após revisão.
Dados derivados somente serão divulgados quando sua publicação
for autorizada e não permitir a identificação ou reconstrução
dos registros restritos.


## Limitações

Os mapas representam suscetibilidade e não substituem avaliações
geotécnicas locais ou sistemas de alerta.
