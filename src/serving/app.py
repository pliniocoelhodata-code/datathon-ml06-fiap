from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app
from src.serving.api import auth, predict, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.serving.core.database import Base, engine
    from src.serving.models.user import User  # noqa: F401 — registra modelo no metadata

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Stock Price Prediction API",
    description="API for predicting stock prices using LSTM model.",
    version="1.0.0",
    lifespan=lifespan,
)

metrics_app = make_asgi_app()

# 2. Montagem do endpoint /metrics
# O Prometheus irá ler os dados deste caminho conforme configurado no prometheus.yml
app.mount("/metrics", metrics_app)

# Registro de Rotas
app.include_router(
    auth.router, 
    prefix="/api/v1",
    tags=["Auth"])

app.include_router(
    user.router, 
    prefix="/api/v1",
    tags=["Users"])

app.include_router(
    predict.router,
    prefix="/api/v1",
    tags=["Prediction"])


@app.get("/health")
def health_check():
    """
    Endpoint de health check para monitoramento (Etapa 3).
    """
    return {
        "status": "healthy",
        "service": "predict-api",
        "version": "1.0.0"
    }