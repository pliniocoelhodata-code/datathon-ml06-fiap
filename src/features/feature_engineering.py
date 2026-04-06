import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def prepare_data(csv_path, window_size=30, test_size=0.2):
    df = pd.read_csv(csv_path, index_col=0, low_memory=False)

    # removing the header
    if df.iloc[0].apply(lambda x: isinstance(x, str)).any():
        df = df.iloc[1:].copy()

    # converting columns to numeric
    df.index = pd.to_datetime(df.index, errors='coerce')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()
    
    # features selection
    features_cols = [col for col in df.columns if any(x in col for x in ['Open', 'High', 'Low', 'Close', 'Volume'])]
    target_col = [col for col in df.columns if 'Close' in col][0]

    data_features = df[features_cols].values
    data_target = df[[target_col]].values
    
    # scaler
    scaler_features = MinMaxScaler(feature_range=(0, 1))
    scaler_target = MinMaxScaler(feature_range=(0, 1))
    
    scaled_features = scaler_features.fit_transform(data_features)
    scaled_target = scaler_target.fit_transform(data_target)
    
    X, y = [], []
    for i in range(window_size, len(scaled_features)):
        X.append(scaled_features[i-window_size:i, :])
        y.append(scaled_target[i, 0])
    
    X, y = np.array(X), np.array(y)
    
    # train/test split
    split = int(len(X) * (1 - test_size))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    
    return X_train, X_test, y_train, y_test, scaler_features, scaler_target