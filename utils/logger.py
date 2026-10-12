import logging
from datetime import datetime

from utils.app_paths import (
    LOG_DIRECTORY,
)


def setup_logger() -> logging.Logger:
    LOG_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    log_file = (
            LOG_DIRECTORY
            / f"flyff_farm_tool_{timestamp}.log"
    )

    logger = logging.getLogger(
        "FlyffFarmTool"
    )

    logger.setLevel(
        logging.DEBUG
    )

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | "
        "%(levelname)-8s | "
        "%(name)s | "
        "%(message)s"
    )

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )

    file_handler.setLevel(
        logging.DEBUG
    )

    file_handler.setFormatter(
        formatter
    )

    console_handler = logging.StreamHandler()

    console_handler.setLevel(
        logging.INFO
    )

    console_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        file_handler
    )

    logger.addHandler(
        console_handler
    )

    return logger


logger = setup_logger()