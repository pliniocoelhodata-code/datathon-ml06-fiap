# Pipeline de treino com MLflow — implementar.
import os
import yaml
import joblib
import mlflow
import mlflow.keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping
from src.features.feature_engineering import prepare_data
from evaluation.model_evaluation import evaluate_model, save_plots

def build_lstm(input_shape, lr):
    model = Sequential([
        Input(shape=input_shape),
        LSTM(100, return_sequences=True),
        Dropout(0.2),
        LSTM(100, return_sequences=False),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer=Adam(learning_rate=lr), loss='mse')
    return model

def run_pipeline():
    with open('configs/model_config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # mlflow
    mlflow.set_experiment("Stock_Analysis_Datathon")
    
    with mlflow.start_run(run_name=config['model']['name']):
        mlflow.log_params(config['model'])
        mlflow.log_param("symbol", config['data']['symbol'])

        X_train, X_test, y_train, y_test, s_feat, s_target = prepare_data(
            config['data']['raw_path'], 
            window_size=config['model']['window_size']
        )

        # train
        model = build_lstm((X_train.shape[1], X_train.shape[2]), config['model']['learning_rate'])
        early_stop = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)

        history = model.fit(
            X_train, y_train,
            epochs=config['model']['epochs'],
            batch_size=config['model']['batch_size'],
            validation_data=(X_test, y_test),
            callbacks=[early_stop],
            verbose=1
        )

        # evaluation
        y_real, y_pred, metrics = evaluate_model(model, X_test, y_test, s_target)
        mlflow.log_metrics(metrics)

        loss_p, pred_p = save_plots(history, y_real, y_pred, config['model']['name'])
        mlflow.log_artifact(loss_p)
        mlflow.log_artifact(pred_p)

        os.makedirs('/app/data/models', exist_ok=True)
        model.save('/app/data/models/modelo_global_v1.keras')

        ticker = config['data']['symbol'].upper()
        ticker_dir = f"/app/data/models/{ticker}"
        os.makedirs(ticker_dir, exist_ok=True)
        joblib.dump(s_feat, f"{ticker_dir}/scaler_features_{ticker}.pkl")
        joblib.dump(s_target, f"{ticker_dir}/scaler_target_{ticker}.pkl")

        scaler_path = f"/app/data/models/{ticker}/scaler_target_{ticker}.pkl"
        mlflow.log_artifact(scaler_path)

        mlflow.keras.log_model(model, "model")
        
        print(f"Successful training! RMSE: {metrics['rmse']:.2f}")

if __name__ == "__main__":
    run_pipeline()