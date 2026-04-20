from __future__ import annotations

from typing import Any

import pandas as pd
from scipy.stats import ks_2samp
from prometheus_client import Gauge

from src.common.logging_setup import setup_logging

logger = setup_logging(__name__)

# Evidently muito instável nas versões mais novas, gerando vários problemas de imports. 
DRIFT_SHARE_GAUGE = Gauge(
    "model_drift_share",
    "Proporção de colunas que apresentaram drift (0.0 a 1.0)",
    ["model_name"]
)


def run_drift_analysis(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    model_name: str = "stock_lstm_v1"
) -> dict[str, Any]:
    """
    Detecta drift comparando distribuições entre datasets.
    Retorna um dicionário no formato semelhante ao Evidently.
    """

    drift_results = _calculate_drift(reference_data, current_data)
    share = drift_results["share_of_drifted_columns"]

    DRIFT_SHARE_GAUGE.labels(model_name=model_name).set(share)

    logger.info(
        "Análise de drift concluída",
        extra={
            "model": model_name,
            "drift_share": share,
            "status": "critical" if share > 0.2 else "normal",
            "event": "drift_analysis_complete",
        },
    )

    return drift_results


def _calculate_drift(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    p_value_threshold: float = 0.05
) -> dict[str, Any]:
    """
    Calcula drift por coluna usando KS test.
    """

    drifted_columns = 0
    total_columns = 0
    column_results = {}

    for col in reference.columns:
        if col not in current.columns:
            continue

        ref_col = reference[col].dropna()
        cur_col = current[col].dropna()

        # só analisa colunas numéricas
        if not pd.api.types.is_numeric_dtype(ref_col):
            continue

        if len(ref_col) == 0 or len(cur_col) == 0:
            continue

        stat, p_value = ks_2samp(ref_col, cur_col)

        drift_detected = p_value < p_value_threshold

        column_results[col] = {
            "p_value": float(p_value),
            "drift_detected": drift_detected,
        }

        total_columns += 1
        if drift_detected:
            drifted_columns += 1

    share = drifted_columns / total_columns if total_columns > 0 else 0.0

    return {
        "share_of_drifted_columns": share,
        "drifted_columns": drifted_columns,
        "total_columns": total_columns,
        "columns": column_results,
    }


def drift_report_to_dict(report: dict[str, Any]) -> dict[str, Any]:
    return report


def share_of_drifted_columns(drift_dict: dict[str, Any]) -> float | None:
    return drift_dict.get("share_of_drifted_columns")