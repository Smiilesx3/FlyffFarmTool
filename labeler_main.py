import sys

from PySide6.QtWidgets import QApplication

from gui.styles import APP_STYLE
from training_tools.labeler_window import LabelerWindow


def main():
    app = QApplication(
        sys.argv
    )

    app.setStyleSheet(
        APP_STYLE
    )

    window = LabelerWindow()

    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()