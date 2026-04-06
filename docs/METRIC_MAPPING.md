# Mapeamento de Métricas - Projeto Disney (DIS)

## 1. Objetivo de Negócio
O objetivo é reduzir a incerteza no fechamento diário das ações da DIS.

## 2. Tradução das Métricas

### Métrica Primária: MAPE (Mean Absolute Percentage Error)
* **Mapeamento:** Um MAPE de 1% em um volume de negociação de US$ 100M representa uma exposição de risco de US$ 1M. 
* **Meta:** < 3.0%.

### Métrica de Risco: RMSE
* **Mapeamento:** Se o RMSE for muito superior ao MAE, o modelo é instável para períodos de crise política ou anúncios de balanço da empresa.

## 3. Baseline vs. Candidato
O modelo Baseline (Random Forest) estabelece o custo de oportunidade. Se a LSTM (Candidata) não superar o Baseline, manteremos a solução mais simples por questões de custo computacional.