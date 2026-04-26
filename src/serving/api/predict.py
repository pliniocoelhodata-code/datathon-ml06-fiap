import asyncio
import joblib
import pandas as pd
import numpy as np
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4
from tensorflow.keras.models import load_model
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram, Gauge

from src.common.logging_setup import setup_logging
from src.serving.core.security import get_current_user
from src.serving.schemas.prediction import PredictionInput, AgentInput, AgentResponse
from src.serving.schemas.user import UserResponse
from src.monitoring.metrics import PREDICTION_REQUESTS, PREDICTION_LATENCY, LAST_PREDICTED_PRICE
from src.agent.react_agent import get_financial_agent

logger = setup_logging(__name__)

AGENT_REQUESTS = Counter(
    "agent_requests_total", 
    "Total number of requests to the Financial Agent", 
    ["status"]
)

# Singleton for the agent to avoid reloading the model on each request.
_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = get_financial_agent()
    return _agent

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
ML_MODELS_DIR = BASE_DIR / "data/models"
MODEL_GLOBAL_PATH = ML_MODELS_DIR / 'modelo_global_v1.keras'
MONITORING_DIR = BASE_DIR / "data/monitoring"
CURRENT_REQUESTS_PATH = MONITORING_DIR / "current_requests.csv"


def _save_request_for_drift(ticker: str, data_frame: pd.DataFrame) -> None:
    MONITORING_DIR.mkdir(parents=True, exist_ok=True)
    request_id = uuid4().hex
    timestamp = datetime.utcnow().isoformat()
    request_df = data_frame.copy()
    request_df["ticker"] = ticker
    request_df["request_id"] = request_id
    request_df["request_ts"] = timestamp

    # Singleton for the agent to avoid reloading the model on each request.
    numeric_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    drift_df = request_df[numeric_columns].copy()
    drift_df["ticker"] = ticker
    drift_df["request_id"] = request_id
    drift_df["request_ts"] = timestamp

    write_header = not CURRENT_REQUESTS_PATH.exists()
    drift_df.to_csv(CURRENT_REQUESTS_PATH, mode="a", header=write_header, index=False)


model = None
try:
    if MODEL_GLOBAL_PATH.exists():
        model = load_model(MODEL_GLOBAL_PATH)
        logger.info(f"Global model successfully loaded {MODEL_GLOBAL_PATH}")
    else:
        logger.error(f"Global model not found in {MODEL_GLOBAL_PATH}")
except Exception as e:
    logger.error(f"Failed to load global model: {e}")

def load_ticker_scalers(ticker: str):
    ticker = ticker.upper()
    ticker_dir = ML_MODELS_DIR / ticker
    
    feat_path = ticker_dir / f'scaler_features_{ticker}.pkl'
    targ_path = ticker_dir / f'scaler_target_{ticker}.pkl'

    if not feat_path.exists() or not targ_path.exists():
        raise FileNotFoundError(f"Scalers to {ticker} not found.")

    s_feat = joblib.load(feat_path)
    s_targ = joblib.load(targ_path)
    return s_feat, s_targ

def _prediction_audit_extra(user: UserResponse, ticker: str, predicted_price: float = None) -> dict:
    """
    Returns a dictionary with extra fields for auditing predictions.
    """
    extra = {
        "user_id": str(user.id),
        "username": user.username,
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if predicted_price is not None:
        extra["predicted_price"] = predicted_price
    return extra

@router.post("/predict")
def predict_stock_price(
    input_data: PredictionInput,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Receives a 30-day window of OHLCV data, applies feature engineering, and returns the predicted price for the requested ticker.
    """
    ticker = input_data.ticker.upper()
    
    with PREDICTION_LATENCY.time():
        try:
            if model is None:
                PREDICTION_REQUESTS.labels(ticker=ticker, status="error").inc()
                logger.error(
                    "Model not initialized on the server.",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(status_code=500, detail="Model not initialized on the server.")

            # Carregamento de Scalers
            try:
                scaler_features, scaler_target = load_ticker_scalers(ticker)
            except FileNotFoundError:
                PREDICTION_REQUESTS.labels(ticker=ticker, status="not_found").inc()
                logger.warning(
                    "Ticker not supported (missing scalers).",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(
                    status_code=404, 
                    detail=f"Ticker {ticker} not supported. Choose from: AAPL, MSFT, GOOGL, DIS, AMZN, TSLA, META, NFLX"
                )

            # Validação de Input (30 dias / 5 features)
            if len(input_data.data) != 30 or any(len(day) != 5 for day in input_data.data):
                PREDICTION_REQUESTS.labels(ticker=ticker, status="bad_request").inc()
                logger.warning(
                    "Invalid payload for prediction.",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(status_code=400, detail="Data should contain exactly 30 days with 5 features each.")

            # Engenharia de Features (Fase 02)
            df = pd.DataFrame(input_data.data, columns=['Open', 'High', 'Low', 'Close', 'Volume'])
            
            df['SMA_10'] = df['Close'].rolling(window=10).mean()
            df['SMA_20'] = df['Close'].rolling(window=20).mean()
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
            df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

            # Tratamento de nulos pós-janelamento
            df.ffill(inplace=True)
            df.bfill(inplace=True)
            
            window_data = df.tail(30)
            _save_request_for_drift(ticker, window_data)
            
            # Seleciona apenas as 5 colunas originais para o scaler e modelo
            original_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            window_data_filtered = window_data[original_columns]
            
            # Escalonamento e Predição
            data_scaled = scaler_features.transform(window_data_filtered.values)
            data_scaled = data_scaled.reshape(1, 30, 5) # Ajustado para 5 features
            
            prediction_scaled = model.predict(data_scaled, verbose=0)
            prediction = scaler_target.inverse_transform(prediction_scaled.reshape(-1, 1))
            
            final_price = float(f"{prediction[0][0]:.2f}")

            # 3. Atualizando métricas de sucesso
            PREDICTION_REQUESTS.labels(ticker=ticker, status="success").inc()
            LAST_PREDICTED_PRICE.labels(ticker=ticker).set(final_price)
            
            logger.info(
                "Prediction successfully completed.",
                extra=_prediction_audit_extra(
                    current_user, ticker, predicted_price=final_price
                ),
            )

            return {"ticker": ticker, "predicted_price": final_price}

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(
                f"Erro na predição: {str(e)}",
                extra=_prediction_audit_extra(current_user, ticker),
            )
            PREDICTION_REQUESTS.labels(ticker=ticker, status="failure").inc()
            raise HTTPException(status_code=500, detail="Internal error in prediction processing.")

@router.post("/agent", response_model=AgentResponse)
async def ask_financial_agent(
    input_data: AgentInput,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Endpoint for interacting with the Financial Agent (RAG + Tools).
    """
    try:
        agent = get_agent()
        
        # Executa o agente de forma assíncrona para não bloquear o worker da API
        # Como o agente é síncrono internamente, usamos asyncio.to_thread
        result = await asyncio.to_thread(agent.invoke, {"input": input_data.query})
        
        AGENT_REQUESTS.labels(status="success").inc()
        
        return AgentResponse(
            answer=result["output"],
            contexts=result.get("contexts", ["No context retrieved."])
        )
    except Exception as e:
        logger.error(f"Erro at the agent: {e}")
        AGENT_REQUESTS.labels(status="error").inc()
        raise HTTPException(status_code=500, detail=f"Error in agent processing.: {str(e)}")