from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class StatusPanel(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("panel")

        self.bot_status_value = QLabel("IDLE")
        self.bot_status_value.setObjectName("statusReady")

        self.input_status_value = QLabel("OFF")
        self.flyff_status_value = QLabel("Not detected")

        self.kill_count_value = QLabel("0")
        self.monster_count_value = QLabel("0")

        layout = QVBoxLayout(self)

        title = QLabel("STATUS")
        title.setObjectName("sectionTitle")

        layout.addWidget(title)

        row_one = QHBoxLayout()
        row_one.addWidget(QLabel("Bot"))
        row_one.addStretch()
        row_one.addWidget(self.bot_status_value)

        row_two = QHBoxLayout()
        row_two.addWidget(QLabel("Game Input"))
        row_two.addStretch()
        row_two.addWidget(self.input_status_value)

        row_three = QHBoxLayout()
        row_three.addWidget(QLabel("Flyff"))
        row_three.addStretch()
        row_three.addWidget(self.flyff_status_value)

        row_four = QHBoxLayout()
        row_four.addWidget(QLabel("Detected monsters"))
        row_four.addStretch()
        row_four.addWidget(self.monster_count_value)

        row_five = QHBoxLayout()
        row_five.addWidget(QLabel("Kills"))
        row_five.addStretch()
        row_five.addWidget(self.kill_count_value)

        layout.addLayout(row_one)
        layout.addLayout(row_two)
        layout.addLayout(row_three)
        layout.addLayout(row_four)
        layout.addLayout(row_five)

    def set_bot_status(
            self,
            status: str,
    ):
        self.bot_status_value.setText(status)

        if status == "EMERGENCY_STOP":
            self.bot_status_value.setObjectName(
                "statusEmergency"
            )

        elif status in {
            "PAUSED",
            "ROTATING_CAMERA",
        }:
            self.bot_status_value.setObjectName(
                "statusWarning"
            )

        else:
            self.bot_status_value.setObjectName(
                "statusReady"
            )

        self.bot_status_value.style().unpolish(
            self.bot_status_value
        )

        self.bot_status_value.style().polish(
            self.bot_status_value
        )

    def set_input_enabled(
            self,
            enabled: bool,
    ):
        self.input_status_value.setText(
            "ON" if enabled else "OFF"
        )

    def set_flyff_detected(
            self,
            detected: bool,
    ):
        self.flyff_status_value.setText(
            "Connected"
            if detected
            else "Not detected"
        )

    def set_monster_count(
            self,
            count: int,
    ):
        self.monster_count_value.setText(
            str(count)
        )

    def set_kill_count(
            self,
            count: int,
    ):
        self.kill_count_value.setText(
            str(count)
        )