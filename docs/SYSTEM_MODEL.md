# Cartão do modelo

## Visão geral

Este documento descreve o modelo preditivo de séries temporais usado no projeto
Datathon ML06 para estimar preço de fechamento de ações. O modelo principal é uma
rede LSTM treinada sobre dados OHLCV e servida pela API FastAPI no endpoint
`/predict`.

O escopo atual do dataset versionado é o ativo Disney (`DIS`), conforme
`configs/model_config.yaml` e `data/raw/stock_data.csv.dvc`.

## Objetivo

O modelo apoia análise financeira ao prever o próximo valor de fechamento a partir
de uma janela recente de preços e volume. Ele é parte de um MVP acadêmico de MLOps,
com foco em:

- demonstrar pipeline de treino e serving;
- registrar experimentos e métricas no MLflow;
- versionar dados com DVC;
- expor predições via API;
- monitorar drift e métricas operacionais.

O modelo não deve ser usado como recomendação direta de compra, venda ou alocação
de capital.

## Dados

Fonte versionada:

- `data/raw/stock_data.csv.dvc`
- arquivo materializado esperado: `data/raw/stock_data.csv`

Configuração:

- símbolo principal: `DIS`
- caminho de entrada: `data/raw/stock_data.csv`
- janela de treino: `120`
- teste temporal: últimos `20%` das janelas geradas

Features usadas no treino:

- `Open`
- `High`
- `Low`
- `Close`
- `Volume`

Target:

- coluna de fechamento (`Close`)

O pré-processamento em `src/features/feature_engineering.py` converte colunas para
numérico, remove nulos, seleciona colunas OHLCV e usa `MinMaxScaler` separado para
features e target.

## Arquitetura

Implementação principal:

- `src/models/train.py`

Arquitetura LSTM:

- camada `Input`;
- `LSTM(100, return_sequences=True)`;
- `Dropout(0.2)`;
- `LSTM(100, return_sequences=False)`;
- `Dropout(0.2)`;
- `Dense(1)`;
- otimizador `Adam`;
- loss `mse`.

Hiperparâmetros principais:

- `window_size: 120`
- `epochs: 50`
- `batch_size: 32`
- `learning_rate: 0.001`
- `EarlyStopping` com `patience=10` e `restore_best_weights=True`

## Baseline

O baseline em `src/models/baseline.py` usa `RandomForestRegressor` com:

- `n_estimators=100`;
- `random_state=42`;
- janelas temporais achatadas como entrada.

O objetivo do baseline é servir como referência de custo-benefício: se a LSTM não
superar uma solução mais simples, o projeto deve justificar o uso do modelo neural.

## Avaliação

A avaliação do modelo numérico é feita em `evaluation/model_evaluation.py`.

Métricas calculadas:

- MAE;
- RMSE;
- MAPE.

Os valores são registrados no MLflow durante o treino. O repositório também salva
gráficos de curva de aprendizado e comparação real vs. predito em `models/images/`
quando o treino é executado.

Observação: este arquivo descreve o método de avaliação e os artefatos esperados.
Os valores finais dependem da execução local do treino e dos artefatos gerados em
MLflow.

## Artefatos

O treino da LSTM salva:

- modelo global: `data/models/modelo_global_v1.keras`;
- scaler de features por ticker: `data/models/<TICKER>/scaler_features_<TICKER>.pkl`;
- scaler de target por ticker: `data/models/<TICKER>/scaler_target_<TICKER>.pkl`;
- modelo e métricas no MLflow.

O teste `tests/test_models.py` verifica a arquitetura esperada e pula a validação
do scaler quando o artefato de treino ainda não existe localmente.

## Serving

Endpoint:

- `POST /predict`

Implementação:

- `src/serving/api/predict.py`

Entrada esperada pela API:

- ticker;
- matriz com exatamente 30 dias;
- 5 valores por dia: `Open`, `High`, `Low`, `Close`, `Volume`.

Durante a inferência, a API:

1. valida o tamanho do payload;
2. calcula indicadores auxiliares (`SMA_10`, `SMA_20`, `EMA_10`, `EMA_20`);
3. usa apenas as 5 colunas OHLCV originais para o scaler/modelo;
4. carrega scalers do ticker;
5. executa `model.predict`;
6. aplica `inverse_transform` no target;
7. retorna o preço previsto.

## Observabilidade

Métricas Prometheus relacionadas ao modelo:

- `prediction_requests_total{ticker, status}`;
- `prediction_duration_seconds`;
- `last_predicted_stock_price{ticker}`;
- `model_drift_share{model_name}`;
- `model_psi{model_name}`.

O monitoramento de drift usa `data/raw/stock_data.csv` como referência e
`data/monitoring/current_requests.csv` como amostra corrente de requisições.

## Segurança e governança

O modelo numérico é exposto separadamente do endpoint `/agent`. A Etapa 4 protege
o fluxo do agente com guardrails, redigindo PII e bloqueando prompt injection antes
de o LLM responder ao usuário.

Para o modelo numérico, os principais controles atuais são:

- validação do formato de entrada;
- autenticação via usuário atual no endpoint;
- logs estruturados de predição;
- métricas de sucesso/erro;
- monitoramento de drift.

## Limitações

- O escopo versionado atual está centrado em `DIS`; outros tickers dependem de
  artefatos e scalers existentes em `data/models/<TICKER>/`.
- Há uma divergência operacional relevante: o treino usa `window_size=120`, mas o
  endpoint `/predict` valida exatamente 30 dias de entrada e remodela o payload
  para `(1, 30, 5)`. Antes de uso produtivo, treino, scalers e serving devem ser
  alinhados para a mesma janela temporal.
- O modelo prevê preço, mas não estima intervalo de confiança.
- A solução não incorpora eventos externos como balanços, notícias, política
  monetária ou choques macroeconômicos.
- Resultados financeiros passados não garantem comportamento futuro.
- Artefatos de treino precisam ser gerados localmente ou disponibilizados via
  pipeline/MLflow/DVC para que o serving funcione em novo ambiente.

## Reprodução

Com o dataset materializado em `data/raw/stock_data.csv`:

```bash
make train
```

Ou, usando ambiente gerenciado:

```bash
uv run make train
```

Para acompanhar experimentos:

```bash
docker compose up -d mlflow
```

Depois acesse:

```text
http://localhost:5000
```

## Status

Status atual: adequado para MVP acadêmico e demonstração MLOps.

Antes de produção, recomenda-se:

- alinhar `window_size` entre treino e API;
- registrar métricas finais do treino neste cartão;
- versionar e disponibilizar artefatos de modelo/scalers;
- adicionar validação de intervalo de valores no payload de predição;
- definir processo formal de retreinamento em caso de drift.
