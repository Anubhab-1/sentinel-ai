import logging
import os

from pythonjsonlogger import jsonlogger


def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logger = logging.getLogger()
    logger.setLevel(log_level)

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
