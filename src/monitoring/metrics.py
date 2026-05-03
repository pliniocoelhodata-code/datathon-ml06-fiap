"""Prometheus metrics shared by serving, monitoring and security layers."""

from prometheus_client import Counter, Gauge, Histogram

# Prediction metrics used by predict.py
PREDICTION_REQUESTS = Counter(
    "prediction_requests_total",
    "Total de pedidos de predicao",
    ["ticker", "status"],
)

PREDICTION_LATENCY = Histogram(
    "prediction_duration_seconds",
    "Tempo de execucao da predicao",
)

LAST_PREDICTED_PRICE = Gauge(
    "last_predicted_stock_price",
    "Ultimo preco previsto pela IA",
    ["ticker"],
)

# Drift metrics used by drift.py
DRIFT_SHARE_GAUGE = Gauge(
    "model_drift_share",
    "Proporcao de colunas que apresentaram drift (0.0 a 1.0)",
    ["model_name"],
)

PSI_GAUGE = Gauge(
    "model_psi",
    "Population Stability Index entre dados de referencia e dados atuais",
    ["model_name"],
)

# Agent and guardrail metrics used by Etapa 4
AGENT_REQUESTS = Counter(
    "agent_requests_total",
    "Total number of requests to the Financial Agent",
    ["status"],
)

AGENT_LATENCY = Histogram(
    "agent_duration_seconds",
    "Tempo de execucao do endpoint do agente financeiro",
)

GUARDRAIL_EVENTS = Counter(
    "guardrail_events_total",
    "Eventos dos guardrails por etapa, acao e tipo de deteccao",
    ["stage", "action", "detection"],
)

PII_REDACTIONS = Counter(
    "pii_redactions_total",
    "Total de redacoes de PII por superficie protegida",
    ["surface"],
)

RAG_CONTEXT_GUARDRAIL_EVENTS = Counter(
    "rag_context_guardrail_events_total",
    "Eventos de guardrail aplicados ao contexto recuperado pelo RAG",
    ["action", "detection"],
)
