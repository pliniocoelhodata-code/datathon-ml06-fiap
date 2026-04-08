from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

# TODO: add report to bucket - use image storage
def run_drift_analysis(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
) -> Report:
    """
    Compara o conjunto de referência ao atual e calcula métricas de drift.

    Exemplo de leitura do resultado (estrutura típica do ``as_dict()``):

        drift_result = report.as_dict()
        drift_share = drift_result["metrics"][0]["result"]["share_of_drifted_columns"]
    """
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference_data, current_data=current_data)
    return report


def drift_report_to_dict(report: Report) -> dict[str, Any]:
    """Retorna o relatório Evidently como dicionário (equivalente a export JSON)."""
    return report.as_dict()


def share_of_drifted_columns(drift_dict: dict[str, Any]) -> float | None:
    """
    Extrai ``share_of_drifted_columns`` do dict retornado por ``Report.as_dict()``,
    sem depender da posição fixa em ``metrics[0]``.
    """
    for metric in drift_dict.get("metrics", []):
        result = metric.get("result")
        if isinstance(result, dict) and "share_of_drifted_columns" in result:
            val = result["share_of_drifted_columns"]
            return float(val) if val is not None else None
    return None


def save_drift_report_html(report: Report, path: str | Path) -> Path:
    """Grava o relatório em HTML no caminho indicado."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    report.save_html(str(out))
    return out


def save_drift_report_json(report: Report, path: str | Path) -> Path:
    """Serializa ``as_dict()`` para um arquivo JSON (UTF-8)."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(report.as_dict(), f, indent=2, ensure_ascii=False)
    return out
