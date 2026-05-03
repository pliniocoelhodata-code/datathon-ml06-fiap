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

## 4. Métricas de segurança e governança

A Etapa 4 adiciona métricas para acompanhar riscos do agente financeiro em produção:

* **Bloqueios de guardrail:** `guardrail_events_total{stage, action, detection}` mede tentativas bloqueadas ou sanitizadas por entrada, saída e tipo de detecção.
* **Redação de PII:** `pii_redactions_total{surface}` mede quando dados pessoais são removidos de input, output, contextos retornados ou contexto RAG.
* **Segurança em RAG:** `rag_context_guardrail_events_total{action, detection}` mede conteúdo inseguro ou sensível recuperado antes de chegar ao LLM.
* **Disponibilidade do agente:** `agent_requests_total{status}` e `agent_duration_seconds` acompanham volume, erros e latência do endpoint `/agent`.

Essas métricas alimentam o dashboard `Datathon ML - Security & Governance` no Grafana e apoiam auditoria LGPD/OWASP.
