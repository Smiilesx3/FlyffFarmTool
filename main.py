import sys

from PySide6.QtWidgets import QApplication

from config.settings_manager import settings_manager
from gui.main_window import MainWindow
from utils.app_paths import (
    APP_DIRECTORY,
    create_runtime_directories,
)
from utils.logger import logger


def main():
    create_runtime_directories()

    logger.info(
        "========================================"
    )

    logger.info(
        "Flyff Farm Tool wird gestartet"
    )

    logger.info(
        "========================================"
    )

    logger.info(
        "Application Directory | %s",
        APP_DIRECTORY,
    )

    settings_manager.load()

    app = QApplication(
        sys.argv
    )

    window = MainWindow()

    window.show()

    exit_code = app.exec()

    logger.info(
        "Flyff Farm Tool wurde beendet."
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()