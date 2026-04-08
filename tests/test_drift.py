import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from faker import Faker

from src.monitoring.drift import (
    drift_report_to_dict,
    run_drift_analysis,
    save_drift_report_html,
    save_drift_report_json,
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


def test_drift_report_json_and_html(tmp_path: Path, faker_seed: None) -> None:
    faker = Faker()
    reference, current = _synthetic_frames(faker)

    report = run_drift_analysis(reference, current)

    json_path = tmp_path / "drift.json"
    html_path = tmp_path / "drift.html"
    save_drift_report_json(report, json_path)
    save_drift_report_html(report, html_path)

    assert json_path.is_file()
    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert len(data["metrics"]) >= 1

    share = share_of_drifted_columns(data)
    assert share is not None
    assert 0.0 <= share <= 1.0

    assert html_path.is_file()
    html = html_path.read_text(encoding="utf-8")
    assert len(html) > 100
    assert "html" in html.lower() or "<!doctype" in html.lower() or "<html" in html.lower()


def test_drift_share_matches_metrics_zero(faker_seed: None) -> None:
    """Compatível com o acesso direto metrics[0] quando existe resultado de drift."""
    faker = Faker()
    reference, _ = _synthetic_frames(faker)
    report = run_drift_analysis(reference, reference.copy())

    drift_result = drift_report_to_dict(report)
    direct = drift_result["metrics"][0]["result"].get("share_of_drifted_columns")
    via_helper = share_of_drifted_columns(drift_result)
    assert direct == via_helper
