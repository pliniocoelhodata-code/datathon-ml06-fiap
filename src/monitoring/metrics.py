# Métricas Prometheus customizadas centralizadas
from prometheus_client import Counter, Histogram, Gauge

# Métricas de predição (usadas em predict.py)
PREDICTION_REQUESTS = Counter(
    "prediction_requests_total",
    "Total de pedidos de predição",
    ["ticker", "status"]
)

PREDICTION_LATENCY = Histogram(
    "prediction_duration_seconds",
    "Tempo de execução da predição"
)

LAST_PREDICTED_PRICE = Gauge(
    "last_predicted_stock_price",
    "Último preço previsto pela IA",
    ["ticker"]
)

# Métricas de drift (usadas em drift.py)
DRIFT_SHARE_GAUGE = Gauge(
    "model_drift_share",
    "Proporção de colunas que apresentaram drift (0.0 a 1.0)",
    ["model_name"]
)

PSI_GAUGE = Gauge(
    "model_psi",
    "Population Stability Index entre dados de referência e dados atuais",
    ["model_name"]
)
