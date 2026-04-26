import pytest
import numpy as np
import os
import joblib
from src.models.train import build_lstm

@pytest.fixture
def mock_config():
    return {
        'model': {
            'name': "lstm_baseline_v1",
            'window_size': 120,
            'learning_rate': 0.001
        }
    }

@pytest.fixture
def input_shape(mock_config):
    # (window_size, num_features)
    # assuming num_features is 1 for the baseline
    return (mock_config['model']['window_size'], 1)

def test_model_architecture(input_shape, mock_config):
    """Checks if the model architecture follows the expected LSTM pattern."""
    model = build_lstm(input_shape, mock_config['model']['learning_rate'])
    
    # verify main layers: 2 LSTMs + Dropout + Dense
    lstm_layers = [layer for layer in model.layers if 'lstm' in layer.name.lower()]
    assert len(lstm_layers) == 2, "The model should contain 2 layers of LSTM."
    
    dense_layers = [layer for layer in model.layers if 'dense' in layer.name.lower()]
    assert len(dense_layers) == 1, "The model must contain 1 Dense output layer."
    assert dense_layers[-1].units == 1, "The output layer must have 1 unit."

def test_model_prediction_shape(input_shape, mock_config):
    """Checks if the model generates predictions with the correct shape (batch_size, 1)."""
    model = build_lstm(input_shape, mock_config['model']['learning_rate'])
    
    # simulates 5 input samples. (batch_size=5, window_size=120, features=1)
    batch_size = 5
    dummy_input = np.random.rand(batch_size, input_shape[0], input_shape[1])
    
    predictions = model.predict(dummy_input)
    assert predictions.shape == (batch_size, 1), f"Expected shape (5, 1), but obtained {predictions.shape}"

def test_scaler_persistence(mock_config):
    """Checks if the scaler was saved in the models directory after training."""
    # this test will be ignored if the file does not exist.
    scaler_filename = f"models/scaler_{mock_config['model']['name']}.pkl"
    
    if os.path.exists(scaler_filename):
        scaler = joblib.load(scaler_filename)
        assert hasattr(scaler, 'scale_') or hasattr(scaler, 'min_'), "The saved file is not a valid scaler."
    else:
        pytest.skip(f"Scaler {scaler_filename} not found. Execute 'make train' first.")
