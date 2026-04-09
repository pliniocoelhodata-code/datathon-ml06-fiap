from fastapi import APIRouter, HTTPException, Depends
import joblib
import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
from pathlib import Path
from src.serving.core.security import get_current_user
from src.serving.schemas.prediction import PredictionInput
from src.serving.schemas.user import UserResponse
from sentry_sdk import logger as sentry_logger

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
ML_MODELS_DIR = BASE_DIR / "src/ml/models"

MODEL_GLOBAL_PATH = ML_MODELS_DIR / 'modelo_global_v1.keras'

try:
    if MODEL_GLOBAL_PATH:
        model = load_model(MODEL_GLOBAL_PATH)
        sentry_logger.info("Global model loaded successfully.")
    else:
        sentry_logger.error(f"Global model not found at {MODEL_GLOBAL_PATH}")
        model = None
except Exception as e:
    sentry_logger.error(f"Failed to load global model: {e}")
    model = None

# função para selecionar os scalers corretos para cada ação
def load_ticker_scalers(ticker: str):
    ticker = ticker.upper()
    print("path", ML_MODELS_DIR)
    ticker_dir = ML_MODELS_DIR / ticker
    
    feat_path = ticker_dir / f'scaler_features_{ticker}.pkl'
    targ_path = ticker_dir / f'scaler_target_{ticker}.pkl'
 
    s_feat = joblib.load(feat_path)
    s_targ = joblib.load(targ_path)
    return s_feat, s_targ

@router.post("/predict")
def predict_stock_price(
    input: PredictionInput,
    current_user: UserResponse = Depends(get_current_user)):
    """
    Predict the stock price using the trained LSTM model.

    This endpoint takes 30 days of stock data (Open, High, Low, Close, Volume)
    and predicts the next day's closing price.

    Args:
        input (PredictionInput): Input data containing a list of 30 days,
                                 each with 5 features and symbol of the stock

    Returns:
        dict: Dictionary containing the predicted price under 'predicted_price'.

    Raises:
        HTTPException: 400 if input data is invalid, 500 if prediction fails,
                       or 401 if authentication fails.
    """
    try:

        ticker = input.ticker.upper()
        try:
            scaler_features, scaler = load_ticker_scalers(ticker)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not supported or not trained. Must chose between: 'AAPL', 'MSFT', 'GOOGL', 'DIS', 'AMZN', 'TSLA', 'META', 'NFLX'")

        if len(input.data) != 30 or any(len(day) != 5 for day in input.data):
            raise HTTPException(status_code=400, detail="Input data must contain exactly 30 days of 5 features each (Open, High, Low, Close, Volume).")

        # data = np.array(input.data)
        df = pd.DataFrame(input.data, columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        # necessário devido a engenharia de feature
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

        window_data = df.ffill(inplace=True)
        window_data = df.bfill(inplace=True)

        window_data = df.tail(30)
        
        data_scaled = scaler_features.transform(window_data.values)
        data_scaled = data_scaled.reshape(1, 30, 9)
        
        prediction_scaled = model.predict(data_scaled, verbose=0)
        
        prediction = scaler.inverse_transform(prediction_scaled.reshape(-1, 1))
        
        return {"predicted_price": float(f"{prediction[0][0]:.2f}")}
    
    except Exception as e:
        sentry_logger.error(f"Prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
