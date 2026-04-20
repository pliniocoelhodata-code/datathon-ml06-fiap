from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch
from src.serving.api.predict import load_ticker_scalers

import numpy as np
import pytest
from starlette.testclient import TestClient


def _unique_user() -> str:
    return f"user_{uuid.uuid4().hex[:16]}"


def _register(client: TestClient, username: str, password: str) -> dict:
    r = client.post("/api/v1/users", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def _login_token(client: TestClient, username: str, password: str) -> str:
    r = client.post(
        "/api/v1/login",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("token_type") == "bearer"
    assert "access_token" in data
    return data["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _valid_prediction_body(ticker: str = "AAPL") -> dict:
    rows = [
        [float(i), float(i) + 1.0, float(i) + 0.5, float(i) + 0.8, 1_000_000.0]
        for i in range(30)
    ]
    return {"ticker": ticker, "data": rows}


@pytest.fixture
def registered_user(client: TestClient) -> tuple[str, str]:
    username = _unique_user()
    password = "secret123"
    _register(client, username, password)
    return username, password


@pytest.fixture
def bearer_token(client: TestClient, registered_user: tuple[str, str]) -> str:
    username, password = registered_user
    return _login_token(client, username, password)


# --- Users ---


def test_register_creates_user(client: TestClient) -> None:
    username = _unique_user()
    body = _register(client, username, "secret123")
    assert body["username"] == username
    assert "id" in body


def test_register_duplicate_username(client: TestClient) -> None:
    username = _unique_user()
    _register(client, username, "secret123")
    r = client.post("/api/v1/users", json={"username": username, "password": "otherpass"})
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"].lower()


# --- Auth ---


def test_login_returns_jwt(client: TestClient, registered_user: tuple[str, str]) -> None:
    username, password = registered_user
    r = client.post(
        "/api/v1/login",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    assert len(r.json()["access_token"]) > 20


def test_login_invalid_credentials(client: TestClient) -> None:
    r = client.post(
        "/api/v1/login",
        data={"username": "nope_user_xyz", "password": "wrong"},
    )
    assert r.status_code == 401


def test_refresh_token(client: TestClient, registered_user: tuple[str, str]) -> None:
    username, password = registered_user
    token = _login_token(client, username, password)
    r = client.post("/api/v1/refresh", json={"refresh_token": token})
    assert r.status_code == 200
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"] != token


# --- Predict ---


def test_predict_requires_authentication(client: TestClient) -> None:
    r = client.post("/api/v1/predict", json=_valid_prediction_body())
    assert r.status_code == 401


@patch("src.serving.api.predict.load_ticker_scalers")
@patch("src.serving.api.predict.model")
def test_predict_success(
    mock_model: MagicMock,
    mock_scalers: MagicMock,
    client: TestClient,
    bearer_token: str,
) -> None:
    feat = MagicMock()
    feat.transform = lambda x: np.zeros((30, 9))
    targ = MagicMock()
    targ.inverse_transform = lambda x: np.array([[199.99]])
    mock_scalers.return_value = (feat, targ)
    mock_model.predict = MagicMock(return_value=np.array([[[0.0]]]))

    r = client.post(
        "/api/v1/predict",
        json=_valid_prediction_body("AAPL"),
        headers=_auth_headers(bearer_token),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ticker"] == "AAPL"
    assert data["predicted_price"] == 199.99


@patch("src.serving.api.predict.model", None)
def test_predict_model_not_loaded(client: TestClient, bearer_token: str) -> None:
    r = client.post(
        "/api/v1/predict",
        json=_valid_prediction_body(),
        headers=_auth_headers(bearer_token),
    )
    assert r.status_code == 500
    assert "não inicializado" in r.json()["detail"]


@patch("src.serving.api.predict.Path.exists")
def test_load_ticker_scalers_not_found(mock_exists: MagicMock):
    # Simula que o arquivo do scaler não existe
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError, match="Scalers para INEXISTENTE não encontrados"):
        load_ticker_scalers("INEXISTENTE")

@patch("src.serving.api.predict.joblib.load")
@patch("src.serving.api.predict.Path.exists")
def test_load_ticker_scalers_success(mock_exists: MagicMock, mock_load: MagicMock):
    mock_exists.return_value = True
    mock_load.side_effect = ["scaler_feat", "scaler_targ"]
    
    s1, s2 = load_ticker_scalers("AAPL")
    assert s1 == "scaler_feat"
    assert s2 == "scaler_targ"


@patch("src.serving.api.predict.load_ticker_scalers")
@patch("src.serving.api.predict.model")
def test_predict_invalid_payload_shape(
    mock_model: MagicMock,
    mock_scalers: MagicMock,
    client: TestClient,
    bearer_token: str,
) -> None:
    feat = MagicMock()
    feat.transform = lambda x: np.zeros((30, 9))
    mock_scalers.return_value = (feat, MagicMock())
    mock_model.predict = MagicMock(return_value=np.array([[[0.0]]]))

    r = client.post(
        "/api/v1/predict",
        json={"ticker": "AAPL", "data": [[1.0, 2.0, 3.0, 4.0, 5.0]]},
        headers=_auth_headers(bearer_token),
    )
    assert r.status_code == 400
    assert "30 dias" in r.json()["detail"]

@patch("src.serving.api.predict.load_ticker_scalers")
@patch("src.serving.api.predict.model")
def test_predict_internal_error_catch_all(
    mock_model: MagicMock,
    mock_scalers: MagicMock,
    client: TestClient,
    bearer_token: str,
) -> None:
    # Simula um erro inesperado durante a predição
    mock_scalers.return_value = (MagicMock(), MagicMock())
    mock_model.predict.side_effect = Exception("Erro inesperado no TensorFlow")

    r = client.post(
        "/api/v1/predict",
        json=_valid_prediction_body(),
        headers=_auth_headers(bearer_token),
    )
    assert r.status_code == 500
    assert "Erro interno" in r.json()["detail"]


@pytest.mark.parametrize(
    "path",
    ["/api/v1/users", "/api/v1/login", "/api/v1/predict"],
)
def test_openapi_lists_routes(client: TestClient, path: str) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json().get("paths", {})
    assert path in paths
