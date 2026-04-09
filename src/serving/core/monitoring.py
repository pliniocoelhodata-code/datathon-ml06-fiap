"""
Módulo de monitoramento com Sentry e métricas de performance.
"""
import os
import sentry_sdk
import logging

logger = logging.getLogger(__name__)


def init_sentry():
    """
    Inicializa o Sentry SDK para monitoramento de erros e performance.
    """

    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logger.warning("SENTRY_DSN não configurado; usando DSN básico embutido para configuração simples.")

    try:
        sentry_sdk.init(
            dsn=sentry_dsn,
            send_default_pii=True,
            enable_logs=True,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
        )
        logger.info("Sentry inicializado (configuração básica).")
    except Exception:
        logger.exception("Falha ao inicializar o Sentry.")
