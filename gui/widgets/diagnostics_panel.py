from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QVBoxLayout,
)


class DiagnosticsPanel(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName(
            "panel"
        )

        title = QLabel(
            "DIAGNOSTICS"
        )

        title.setObjectName(
            "sectionTitle"
        )

        self.window_value = QLabel(
            "NOT FOUND"
        )

        self.resolution_value = QLabel(
            "-"
        )

        self.target_value = QLabel(
            "NO"
        )

        self.hp_pixels_value = QLabel(
            "0"
        )

        self.hp_threshold_value = QLabel(
            "-"
        )

        self.foreground_value = QLabel(
            "-"
        )

        self.model_value = QLabel(
            "NOT LOADED"
        )

        self.detections_value = QLabel(
            "0"
        )

        grid = QGridLayout()

        self._add_row(
            grid,
            0,
            "Flyff window",
            self.window_value,
        )

        self._add_row(
            grid,
            1,
            "Resolution",
            self.resolution_value,
        )

        self._add_row(
            grid,
            2,
            "Target",
            self.target_value,
        )

        self._add_row(
            grid,
            3,
            "HP pixels",
            self.hp_pixels_value,
        )

        self._add_row(
            grid,
            4,
            "HP threshold",
            self.hp_threshold_value,
        )

        self._add_row(
            grid,
            5,
            "Flyff foreground",
            self.foreground_value,
        )

        self._add_row(
            grid,
            6,
            "Monster model",
            self.model_value,
        )

        self._add_row(
            grid,
            7,
            "Detections",
            self.detections_value,
        )

        layout = QVBoxLayout(
            self
        )

        layout.addWidget(
            title
        )

        layout.addLayout(
            grid
        )

    @staticmethod
    def _add_row(
            layout: QGridLayout,
            row: int,
            title: str,
            value_widget: QLabel,
    ):
        title_label = QLabel(
            title
        )

        title_label.setObjectName(
            "muted"
        )

        layout.addWidget(
            title_label,
            row,
            0,
        )

        layout.addWidget(
            value_widget,
            row,
            1,
        )

    def set_window_detected(
            self,
            detected: bool,
    ):
        self.window_value.setText(
            "FOUND"
            if detected
            else "NOT FOUND"
        )

    def set_resolution(
            self,
            width: int | None,
            height: int | None,
    ):
        if (
                width is None
                or height is None
        ):
            self.resolution_value.setText(
                "-"
            )
            return

        self.resolution_value.setText(
            f"{width} × {height}"
        )

    def set_target(
            self,
            present: bool,
            hp_pixels: int,
            threshold: int,
    ):
        self.target_value.setText(
            "YES"
            if present
            else "NO"
        )

        self.hp_pixels_value.setText(
            str(hp_pixels)
        )

        self.hp_threshold_value.setText(
            str(threshold)
        )

    def set_foreground(
            self,
            foreground: bool | None,
    ):
        if foreground is None:
            text = "-"
        else:
            text = (
                "YES"
                if foreground
                else "NO"
            )

        self.foreground_value.setText(
            text
        )

    def set_model_loaded(
            self,
            loaded: bool,
    ):
        self.model_value.setText(
            "LOADED"
            if loaded
            else "NOT LOADED"
        )

    def set_detection_count(
            self,
            count: int,
    ):
        self.detections_value.setText(
            str(count)
        )