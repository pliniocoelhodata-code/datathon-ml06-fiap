from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report
from prometheus_client import Gauge

from src.monitoring.logging_config import setup_logging
logger = setup_logging(__name__)

# Gauge para monitorar a proporção de colunas com drift no Grafana
DRIFT_SHARE_GAUGE = Gauge(
    "model_drift_share", 
    "Proporção de colunas que apresentaram drift (0.0 a 1.0)",
    ["model_name"]
)

def run_drift_analysis(
    reference_data: pd.DataFrame,
    current_data: pd.DataFrame,
    model_name: str = "stock_lstm_v1"
) -> Report:
    """
    Compara o conjunto de referência ao atual e atualiza métricas no Prometheus.
    """
    logger.info("Iniciando análise de drift", extra={"model": model_name, "layer": "monitoring"})
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=reference_data, current_data=current_data)
    
    drift_dict = report.as_dict()
    share = _extract_drift_share(drift_dict)
    
    if share is not None:
        DRIFT_SHARE_GAUGE.labels(model_name=model_name).set(share)
        logger.info(
            "Análise de drift concluída", 
            extra={
                "model": model_name, 
                "drift_share": share,
                "status": "critical" if share > 0.2 else "normal"
            }
        )
    
    return report

def _extract_drift_share(drift_dict: dict[str, Any]) -> float | None:
    """Função interna robusta para extrair o valor do drift."""
    for metric in drift_dict.get("metrics", []):
        result = metric.get("result")
        if isinstance(result, dict) and "share_of_drifted_columns" in result:
            return float(result["share_of_drifted_columns"])
    return None

def save_drift_report_html(report: Report, path: str | Path) -> Path:
    """Grava o relatório em HTML e loga o evento para auditoria."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    report.save_html(str(out))
    
    logger.info("Relatório HTML de drift exportado", extra={"path": str(out)})
    return out

def save_drift_report_json(report: Report, path: str | Path) -> Path:
    """Serializa as_dict() e loga o caminho do artefato."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # TODO: Implementar upload para Bucket S3/GCS aqui conforme seu comentário
    with out.open("w", encoding="utf-8") as f:
        json.dump(report.as_dict(), f, indent=2, ensure_ascii=False)
    
    logger.info("Metadados de drift salvos em JSON", extra={"path": str(out)})
    return out