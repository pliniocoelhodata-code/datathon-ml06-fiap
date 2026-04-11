import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(module_name: str) -> logging.Logger:
    """Configura o logging estruturado para qualquer camada do projeto."""
    logger = logging.getLogger(module_name)

    if not logger.handlers:
        log_handler = logging.StreamHandler(sys.stdout)

        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp"},
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
