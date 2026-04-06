# Baseline Scikit-Learn + MLP PyTorch
import os
import yaml
import mlflow
import joblib
# import numpy as np
from sklearn.ensemble import RandomForestRegressor
# from sklearn.metrics import mean_absolute_error, mean_squared_error
from src.features.feature_engineering import prepare_data
from evaluation.model_evaluation import evaluate_model

def run_baseline():
    with open('configs/model_config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)

    # mlflow
    mlflow.set_experiment("Stock_Analysis_Datathon")
    
    with mlflow.start_run(run_name="Baseline_RandomForest"):
        X_train, X_test, y_train, y_test, s_feat, s_target = prepare_data(
            cfg['data']['raw_path'], 
            window_size=cfg['model']['window_size']
        )
        
        X_train_flat = X_train.reshape(X_train.shape[0], -1)
        X_test_flat = X_test.reshape(X_test.shape[0], -1)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_flat, y_train)

        # evaluation
        _, _, metrics = evaluate_model(model, X_test_flat, y_test, s_target)
        
        # mlflow logging
        mlflow.log_params({
            "model_type": "RandomForest",
            "n_estimators": 100,
            "window_size": cfg['model']['window_size']
        })
        mlflow.log_metrics(metrics)

        # saving baseline model
        os.makedirs('models', exist_ok=True)
        baseline_path = "models/baseline_rf_model.pkl"
        joblib.dump(model, baseline_path)
        mlflow.log_artifact(baseline_path)

        print(f"Baseline training finished! RMSE: {metrics['rmse']:.2f}")

if __name__ == "__main__":
    run_baseline()