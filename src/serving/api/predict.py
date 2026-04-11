import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from tensorflow.keras.models import load_model
from fastapi import APIRouter, HTTPException, Depends
from prometheus_client import Counter, Histogram, Gauge

from src.common.logging_setup import setup_logging
from src.serving.core.security import get_current_user
from src.serving.schemas.prediction import PredictionInput
from src.serving.schemas.user import UserResponse

logger = setup_logging(__name__)


def _prediction_audit_extra(
    current_user: UserResponse,
    ticker: str,
    *,
    predicted_price: float | None = None,
) -> dict[str, object]:
    return {
        "user": current_user.username,
        "ticker": ticker,
        "predicted_price": predicted_price,
    }


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

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
ML_MODELS_DIR = BASE_DIR / "src/ml/models" # TODO: Rafael, ajustar quando modelo estiver pronto
MODEL_GLOBAL_PATH = ML_MODELS_DIR / 'modelo_global_v1.keras' # TODO: Rafael, ajustar quando modelo estiver pronto   


model = None
try:
    if MODEL_GLOBAL_PATH.exists():
        model = load_model(MODEL_GLOBAL_PATH)
        logger.info(f"Modelo global carregado com sucesso de {MODEL_GLOBAL_PATH}")
    else:
        logger.error(f"Modelo global não encontrado em {MODEL_GLOBAL_PATH}")
except Exception as e:
    logger.error(f"Falha ao carregar o modelo global: {e}")

def load_ticker_scalers(ticker: str):
    ticker = ticker.upper()
    ticker_dir = ML_MODELS_DIR / ticker
    
    feat_path = ticker_dir / f'scaler_features_{ticker}.pkl'
    targ_path = ticker_dir / f'scaler_target_{ticker}.pkl'

    if not feat_path.exists() or not targ_path.exists():
        raise FileNotFoundError(f"Scalers para {ticker} não encontrados.")

    s_feat = joblib.load(feat_path)
    s_targ = joblib.load(targ_path)
    return s_feat, s_targ

@router.post("/predict")
def predict_stock_price(
    input_data: PredictionInput,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Endpoint documentado para predição de preços de ações.
    Instrumentado para Prometheus/Grafana.
    """
    ticker = input_data.ticker.upper()
    
    # Iniciamos a medição de tempo
    with PREDICTION_LATENCY.time():
        try:
            # Validação de modelo carregado
            if model is None:
                PREDICTION_REQUESTS.labels(ticker=ticker, status="error").inc()
                logger.error(
                    "Modelo não inicializado no servidor.",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(status_code=500, detail="Modelo não inicializado no servidor.")

            # Carregamento de Scalers
            try:
                scaler_features, scaler_target = load_ticker_scalers(ticker)
            except FileNotFoundError:
                PREDICTION_REQUESTS.labels(ticker=ticker, status="not_found").inc()
                logger.warning(
                    "Ticker não suportado (scalers ausentes).",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(
                    status_code=404, 
                    detail=f"Ticker {ticker} não suportado. Escolha entre: AAPL, MSFT, GOOGL, DIS, AMZN, TSLA, META, NFLX"
                )

            # Validação de Input (30 dias / 5 features)
            if len(input_data.data) != 30 or any(len(day) != 5 for day in input_data.data):
                PREDICTION_REQUESTS.labels(ticker=ticker, status="bad_request").inc()
                logger.warning(
                    "Payload inválido para predição.",
                    extra=_prediction_audit_extra(current_user, ticker),
                )
                raise HTTPException(status_code=400, detail="Dados devem conter exatamente 30 dias com 5 features cada.")

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
            
            # Escalonamento e Predição
            data_scaled = scaler_features.transform(window_data.values)
            data_scaled = data_scaled.reshape(1, 30, 9) # 5 originais + 4 novas features
            
            prediction_scaled = model.predict(data_scaled, verbose=0)
            prediction = scaler_target.inverse_transform(prediction_scaled.reshape(-1, 1))
            
            final_price = float(f"{prediction[0][0]:.2f}")

            # 3. Atualizando métricas de sucesso
            PREDICTION_REQUESTS.labels(ticker=ticker, status="success").inc()
            LAST_PREDICTED_PRICE.labels(ticker=ticker).set(final_price)
            
            logger.info(
                "Predição concluída com sucesso.",
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
            raise HTTPException(status_code=500, detail="Erro interno no processamento da predição.")