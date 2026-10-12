from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from config.settings import settings


class FarmingPanel(QFrame):
    start_requested = Signal()
    pause_requested = Signal()
    stop_requested = Signal()

    emergency_requested = Signal()
    emergency_reset_requested = Signal()

    input_enabled_changed = Signal(bool)
    attack_key_changed = Signal(str)
    confidence_changed = Signal(float)
    camera_search_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        self.setObjectName("panel")

        # ---------------------------------------------------------
        # Title
        # ---------------------------------------------------------

        title = QLabel("FARMING")
        title.setObjectName("sectionTitle")

        # ---------------------------------------------------------
        # Monster selection
        # ---------------------------------------------------------

        monster_label = QLabel(
            "Target monster"
        )

        self.monster_combo = QComboBox()

        # Solange noch kein trainiertes Modell geladen ist,
        # kennen wir nur unsere geplante erste Klasse.
        self.monster_combo.addItem(
            "Ghost of the Forgotten King",
            "ghost_forgotten_king",
        )

        # Falls aus den gespeicherten Einstellungen bereits
        # ein Monster bekannt ist, versuchen wir es auszuwählen.
        if settings.targeting.allowed_monsters:
            selected_monster = next(
                iter(
                    settings.targeting.allowed_monsters
                )
            )

            monster_index = (
                self.monster_combo.findData(
                    selected_monster
                )
            )

            if monster_index >= 0:
                self.monster_combo.setCurrentIndex(
                    monster_index
                )

        # ---------------------------------------------------------
        # Confidence
        # ---------------------------------------------------------

        confidence_label = QLabel(
            "Minimum confidence"
        )

        self.confidence_spin = QDoubleSpinBox()

        self.confidence_spin.setRange(
            0.10,
            1.00,
        )

        self.confidence_spin.setSingleStep(
            0.05
        )

        self.confidence_spin.setDecimals(
            2
        )

        self.confidence_spin.setValue(
            settings.targeting.minimum_confidence
        )

        # ---------------------------------------------------------
        # Attack key
        # ---------------------------------------------------------

        attack_label = QLabel(
            "Attack key"
        )

        self.attack_combo = QComboBox()

        for key in (
                "F1",
                "F2",
                "F3",
                "F4",
                "F5",
                "F6",
                "F7",
                "F8",
                "F9",
        ):
            self.attack_combo.addItem(
                key,
                key.lower(),
            )

        current_attack_index = (
            self.attack_combo.findData(
                settings.combat.attack_key.lower()
            )
        )

        if current_attack_index >= 0:
            self.attack_combo.setCurrentIndex(
                current_attack_index
            )

        # ---------------------------------------------------------
        # Options
        # ---------------------------------------------------------

        self.camera_checkbox = QCheckBox(
            "Automatic camera search"
        )

        self.camera_checkbox.setChecked(
            settings.search.camera_search_enabled
        )

        self.input_checkbox = QCheckBox(
            "Enable real game input"
        )

        # settings_manager erzwingt beim Programmstart False.
        self.input_checkbox.setChecked(
            settings.input.enabled
        )

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------

        self.start_button = QPushButton(
            "START FARMING"
        )

        self.start_button.setObjectName(
            "primaryButton"
        )

        self.pause_button = QPushButton(
            "Pause"
        )

        self.stop_button = QPushButton(
            "Stop"
        )

        self.emergency_button = QPushButton(
            "EMERGENCY STOP"
        )

        self.emergency_button.setObjectName(
            "dangerButton"
        )

        self.reset_emergency_button = QPushButton(
            "Reset Emergency Stop"
        )

        self.reset_emergency_button.setObjectName(
            "resetButton"
        )

        # Im normalen Zustand gibt es nichts zurückzusetzen.
        self.reset_emergency_button.setEnabled(
            False
        )

        # ---------------------------------------------------------
        # Signals
        # ---------------------------------------------------------

        self.start_button.clicked.connect(
            self.start_requested.emit
        )

        self.pause_button.clicked.connect(
            self.pause_requested.emit
        )

        self.stop_button.clicked.connect(
            self.stop_requested.emit
        )

        self.emergency_button.clicked.connect(
            self.emergency_requested.emit
        )

        self.reset_emergency_button.clicked.connect(
            self.emergency_reset_requested.emit
        )

        self.input_checkbox.toggled.connect(
            self.input_enabled_changed.emit
        )

        self.camera_checkbox.toggled.connect(
            self.camera_search_changed.emit
        )

        self.attack_combo.currentIndexChanged.connect(
            self._emit_attack_key
        )

        self.confidence_spin.valueChanged.connect(
            self.confidence_changed.emit
        )

        # ---------------------------------------------------------
        # Layout
        # ---------------------------------------------------------

        layout = QVBoxLayout(self)

        layout.addWidget(
            title
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            monster_label
        )

        layout.addWidget(
            self.monster_combo
        )

        layout.addSpacing(
            8
        )

        confidence_row = QHBoxLayout()

        confidence_row.addWidget(
            confidence_label
        )

        confidence_row.addStretch()

        confidence_row.addWidget(
            self.confidence_spin
        )

        layout.addLayout(
            confidence_row
        )

        attack_row = QHBoxLayout()

        attack_row.addWidget(
            attack_label
        )

        attack_row.addStretch()

        attack_row.addWidget(
            self.attack_combo
        )

        layout.addLayout(
            attack_row
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            self.camera_checkbox
        )

        layout.addWidget(
            self.input_checkbox
        )

        layout.addSpacing(
            12
        )

        layout.addWidget(
            self.start_button
        )

        normal_buttons = QHBoxLayout()

        normal_buttons.addWidget(
            self.pause_button
        )

        normal_buttons.addWidget(
            self.stop_button
        )

        layout.addLayout(
            normal_buttons
        )

        layout.addSpacing(
            8
        )

        layout.addWidget(
            self.emergency_button
        )

        layout.addWidget(
            self.reset_emergency_button
        )

        layout.addStretch()

    def _emit_attack_key(self):
        key = self.attack_combo.currentData()

        if key:
            self.attack_key_changed.emit(
                key
            )

    def set_paused(
            self,
            paused: bool,
    ):
        self.pause_button.setText(
            "Resume"
            if paused
            else "Pause"
        )

    def set_emergency_active(
            self,
            active: bool,
    ):
        self.reset_emergency_button.setEnabled(
            active
        )

        self.start_button.setEnabled(
            not active
        )

        self.pause_button.setEnabled(
            not active
        )