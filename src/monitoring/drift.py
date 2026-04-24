from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pandas as pd
import mlflow
from scipy.stats import ks_2samp

from src.common.logging_setup import setup_logging
from src.monitoring.metrics import DRIFT_SHARE_GAUGE

logger = setup_logging(__name__)

# Evidently muito instável nas versões mais novas, gerando vários problemas de imports.


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
            "drift_detected": int(drift_detected),
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


def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de dados não encontrado: {path}")

    required_cols = ["Open", "High", "Low", "Close", "Volume"]

    def _is_number(value: str) -> bool:
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    rows: list[list[float]] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.reader(csv_file)
        for row in reader:
            if not row:
                continue

            # Ignora cabeçalhos possíveis: Date,Open,... ou Open,High,...
            first = row[0].strip().lower()
            if first in {"date", "open"}:
                continue

            # Formato B (requisições): Open,High,Low,Close,Volume,(meta...)
            if len(row) >= 5 and _is_number(row[0]):
                values = row[0:5]
            # Formato A (referência): Date,Open,High,Low,Close,Volume
            elif len(row) >= 6 and _is_number(row[1]):
                values = row[1:6]
            else:
                continue

            if all(_is_number(v) for v in values):
                rows.append([float(v) for v in values])

    if not rows:
        raise ValueError(f"Nenhuma linha válida encontrada no arquivo: {path}")

    return pd.DataFrame(rows, columns=required_cols)


BASE_DIR = Path(__file__).resolve().parents[2]
REFERENCE_PATH = BASE_DIR / "data/raw/stock_data.csv"
CURRENT_DATA_PATH = BASE_DIR / "data/monitoring/current_requests.csv"


def main(
    reference_path: Path | str = REFERENCE_PATH,
    current_path: Path | str = CURRENT_DATA_PATH,
    model_name: str = "stock_lstm_v1",
) -> dict[str, Any]:
    reference_df = load_data(Path(reference_path))
    current_df = load_data(Path(current_path))
    return run_drift_analysis(reference_df, current_df, model_name=model_name)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Executa análise de drift de dados e registra métricas Prometheus e MLflow.")
    parser.add_argument("--reference", default=str(REFERENCE_PATH), help="Caminho do dataset de referência")
    parser.add_argument("--current", default=str(CURRENT_DATA_PATH), help="Caminho do dataset atual")
    parser.add_argument("--model-name", default="stock_lstm_v1", help="Nome do modelo para métricas")
    args = parser.parse_args()

    try:
        result = main(args.reference, args.current, args.model_name)
        print("Drift analysis completed:", result)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        raise SystemExit(1)