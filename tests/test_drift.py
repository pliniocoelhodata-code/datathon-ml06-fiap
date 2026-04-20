import numpy as np
import pandas as pd
import pytest
from faker import Faker

from src.monitoring.drift import (
    drift_report_to_dict,
    run_drift_analysis,
    share_of_drifted_columns,
)


@pytest.fixture
def faker_seed() -> None:
    Faker.seed(42)
    np.random.seed(42)


def _synthetic_frames(faker: Faker) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Referência estável vs. atual com leve mudança de distribuição (drift detectável)."""
    n_ref, n_cur = 200, 200
    ref = pd.DataFrame(
        {
            "feature_a": np.random.normal(0.0, 1.0, n_ref),
            "feature_b": np.random.uniform(0, 10, n_ref),
            "label": [faker.word() for _ in range(n_ref)],
        }
    )
    cur = pd.DataFrame(
        {
            "feature_a": np.random.normal(1.5, 1.2, n_cur),
            "feature_b": np.random.uniform(2, 12, n_cur),
            "label": [faker.word() for _ in range(n_cur)],
        }
    )
    return ref, cur


def test_drift_report_dict_in_memory(faker_seed: None) -> None:
    faker = Faker()
    reference, current = _synthetic_frames(faker)

    report = run_drift_analysis(reference, current)
    data = drift_report_to_dict(report)

    # ✅ novo formato
    assert "share_of_drifted_columns" in data
    assert "columns" in data
    assert "total_columns" in data

    share = share_of_drifted_columns(data)

    assert share is not None
    assert 0.0 <= share <= 1.0
    assert data["total_columns"] > 0


def test_drift_share_matches_zero(faker_seed: None) -> None:
    """Sem drift: datasets idênticos devem retornar share = 0"""
    faker = Faker()
    reference, _ = _synthetic_frames(faker)

    report = run_drift_analysis(reference, reference.copy())
    drift_result = drift_report_to_dict(report)

    share = share_of_drifted_columns(drift_result)

    assert share == 0.0


def test_drift_detected(faker_seed: None) -> None:
    """Com drift: deve detectar pelo menos alguma diferença"""
    faker = Faker()
    reference, current = _synthetic_frames(faker)

    report = run_drift_analysis(reference, current)
    drift_result = drift_report_to_dict(report)

    share = share_of_drifted_columns(drift_result)

    assert share is not None
    assert share > 0.0