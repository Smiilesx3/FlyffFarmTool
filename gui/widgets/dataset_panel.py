from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from config.settings import settings


class DatasetPanel(QFrame):
    recording_requested = Signal()
    interval_changed = Signal(float)

    def __init__(self):
        super().__init__()

        self.setObjectName("panel")

        self.recording = False

        # ---------------------------------------------------------
        # Widgets
        # ---------------------------------------------------------

        title = QLabel("DATASET RECORDING")
        title.setObjectName("sectionTitle")

        description = QLabel(
            "Collect clean Flyff frames for monster training."
        )
        description.setObjectName("muted")

        self.status_label = QLabel(
            "OFF"
        )

        self.image_count_label = QLabel(
            "0"
        )

        self.interval_spin = QSpinBox()

        self.interval_spin.setRange(
            100,
            5000,
        )

        self.interval_spin.setSingleStep(
            100
        )

        self.interval_spin.setSuffix(
            " ms"
        )

        self.interval_spin.setValue(
            int(
                settings.dataset.capture_interval
                * 1000
            )
        )

        self.record_button = QPushButton(
            "Start Recording"
        )

        self.record_button.setObjectName(
            "primaryButton"
        )

        # ---------------------------------------------------------
        # Signals
        # ---------------------------------------------------------

        self.record_button.clicked.connect(
            self.recording_requested.emit
        )

        self.interval_spin.valueChanged.connect(
            self._on_interval_changed
        )

        # ---------------------------------------------------------
        # Layout
        # ---------------------------------------------------------

        layout = QVBoxLayout(self)

        layout.addWidget(title)
        layout.addWidget(description)

        status_row = QHBoxLayout()

        status_row.addWidget(
            QLabel("Status")
        )

        status_row.addStretch()

        status_row.addWidget(
            self.status_label
        )

        layout.addLayout(
            status_row
        )

        images_row = QHBoxLayout()

        images_row.addWidget(
            QLabel("Images captured")
        )

        images_row.addStretch()

        images_row.addWidget(
            self.image_count_label
        )

        layout.addLayout(
            images_row
        )

        interval_row = QHBoxLayout()

        interval_row.addWidget(
            QLabel("Capture interval")
        )

        interval_row.addStretch()

        interval_row.addWidget(
            self.interval_spin
        )

        layout.addLayout(
            interval_row
        )

        layout.addWidget(
            self.record_button
        )

    def _on_interval_changed(
            self,
            milliseconds: int,
    ):
        seconds = milliseconds / 1000.0

        self.interval_changed.emit(
            seconds
        )

    def set_recording(
            self,
            recording: bool,
    ):
        self.recording = recording

        if recording:
            self.status_label.setText(
                "RECORDING"
            )

            self.record_button.setText(
                "Stop Recording"
            )

        else:
            self.status_label.setText(
                "OFF"
            )

            self.record_button.setText(
                "Start Recording"
            )

    def set_image_count(
            self,
            count: int,
    ):
        self.image_count_label.setText(
            str(count)
        )