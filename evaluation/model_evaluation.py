import matplotlib.pyplot as plt
import numpy as np
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error

def evaluate_model(model, X_test, y_test, scaler):
    predictions = model.predict(X_test)
    y_test_real = scaler.inverse_transform(y_test.reshape(-1, 1))
    predictions_real = scaler.inverse_transform(predictions)
    
    mae = mean_absolute_error(y_test_real, predictions_real)
    rmse = np.sqrt(mean_squared_error(y_test_real, predictions_real))
    mape = np.mean(np.abs((y_test_real - predictions_real) / y_test_real)) * 100
    
    metrics = {"mae": float(mae), "rmse": float(rmse), "mape": float(mape)}
    return y_test_real, predictions_real, metrics

def save_plots(history, y_real, y_pred, model_name):
    os.makedirs('models/images', exist_ok=True)
    
    # Plot 1: Loss
    plt.figure(figsize=(10, 5))
    plt.plot(history.history['loss'], label='Treino')
    plt.plot(history.history['val_loss'], label='Validação')
    plt.title('Curva de Aprendizado')
    plt.legend()
    loss_path = f'models/images/loss_{model_name}.png'
    plt.savefig(loss_path)
    plt.close()
    
    # Plot 2: Predição
    plt.figure(figsize=(12, 6))
    plt.plot(y_real, label='Real', color='blue')
    plt.plot(y_pred, label='Predição', color='red', linestyle='--')
    plt.title('Real vs Predição')
    plt.legend()
    pred_path = f'models/images/pred_{model_name}.png'
    plt.savefig(pred_path)
    plt.close()
    
    return loss_path, pred_path