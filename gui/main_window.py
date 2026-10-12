import cv2

from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from bot.controller import BotController, BotState
from capture.window_capture import WindowCapture
from config.settings import settings
from config.settings_manager import settings_manager
from dataset.recorder import DatasetRecorder
from diagnostics.manager import DiagnosticsManager
from gui.styles import APP_STYLE
from gui.widgets.dataset_panel import DatasetPanel
from gui.widgets.diagnostics_panel import DiagnosticsPanel
from gui.widgets.farming_panel import FarmingPanel
from gui.widgets.status_panel import StatusPanel
from input_control.game_input import InputController
from input_control.hotkey_manager import HotkeyManager
from utils.logger import logger
from vision.monster_detector import MonsterDetector
from vision.target_detector import TargetDetector
from vision.vision_engine import VisionEngine


class HotkeySignals(QObject):
    start_stop = Signal()
    emergency_stop = Signal()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Flyff Farm Tool - V0.8 Test"
        )

        self.resize(
            1450,
            900,
        )

        self.setStyleSheet(
            APP_STYLE
        )

        # ---------------------------------------------------------
        # Services
        # ---------------------------------------------------------

        self.window_capture = WindowCapture(
            settings.capture.window_title_contains
        )

        self.monster_detector = MonsterDetector()
        self.target_detector = TargetDetector()

        self.vision_engine = VisionEngine(
            monster_detector=self.monster_detector,
            target_detector=self.target_detector,
        )

        self.input_controller = InputController()

        self.bot_controller = BotController(
            input_controller=self.input_controller,
        )

        self.dataset_recorder = DatasetRecorder()

        self.diagnostics_manager = (
            DiagnosticsManager()
        )

        # ---------------------------------------------------------
        # Runtime state
        # ---------------------------------------------------------

        self.last_target_present = False

        self.last_bot_state = (
            self.bot_controller.state
        )

        self.flyff_was_detected = False

        # ---------------------------------------------------------
        # Hotkeys
        # ---------------------------------------------------------

        self.hotkey_signals = HotkeySignals()

        self.hotkey_signals.start_stop.connect(
            self.handle_start_stop_hotkey
        )

        self.hotkey_signals.emergency_stop.connect(
            self.emergency_stop
        )

        self.hotkey_manager = HotkeyManager(
            on_start_stop=(
                self.hotkey_signals.start_stop.emit
            ),
            on_emergency_stop=(
                self.hotkey_signals.emergency_stop.emit
            ),
        )

        self.hotkey_manager.start()

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        title_label = QLabel(
            "Flyff Farm Tool"
        )

        title_label.setObjectName(
            "appTitle"
        )

        subtitle_label = QLabel(
            "V0.8 Private Test Build"
        )

        subtitle_label.setObjectName(
            "muted"
        )

        header_layout = QVBoxLayout()

        header_layout.addWidget(
            title_label
        )

        header_layout.addWidget(
            subtitle_label
        )

        # ---------------------------------------------------------
        # Preview
        # ---------------------------------------------------------

        self.preview_label = QLabel(
            "Waiting for Flyff..."
        )

        self.preview_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.preview_label.setMinimumSize(
            760,
            500,
        )

        self.preview_label.setStyleSheet(
            """
            QLabel {
                background-color: #171a16;
                color: #9ca396;
                border-radius: 12px;
            }
            """
        )

        # ---------------------------------------------------------
        # Panels
        # ---------------------------------------------------------

        self.farming_panel = FarmingPanel()
        self.status_panel = StatusPanel()
        self.dataset_panel = DatasetPanel()
        self.diagnostics_panel = DiagnosticsPanel()

        self.farming_panel.setMinimumWidth(
            340
        )

        self.status_panel.setMinimumWidth(
            340
        )

        # ---------------------------------------------------------
        # Farming signals
        # ---------------------------------------------------------

        self.farming_panel.start_requested.connect(
            self.start_bot
        )

        self.farming_panel.pause_requested.connect(
            self.pause_or_resume_bot
        )

        self.farming_panel.stop_requested.connect(
            self.stop_bot
        )

        self.farming_panel.emergency_requested.connect(
            self.emergency_stop
        )

        self.farming_panel.emergency_reset_requested.connect(
            self.reset_emergency_stop
        )

        self.farming_panel.input_enabled_changed.connect(
            self.set_input_enabled
        )

        self.farming_panel.attack_key_changed.connect(
            self.set_attack_key
        )

        self.farming_panel.confidence_changed.connect(
            self.set_confidence
        )

        self.farming_panel.camera_search_changed.connect(
            self.set_camera_search
        )

        # ---------------------------------------------------------
        # Dataset signals
        # ---------------------------------------------------------

        self.dataset_panel.recording_requested.connect(
            self.toggle_dataset_recording
        )

        self.dataset_panel.interval_changed.connect(
            self.set_dataset_interval
        )

        # ---------------------------------------------------------
        # Layout
        # ---------------------------------------------------------

        right_layout = QVBoxLayout()

        right_layout.addWidget(
            self.status_panel
        )

        right_layout.addWidget(
            self.diagnostics_panel
        )

        right_layout.addWidget(
            self.farming_panel,
            1,
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(
            14
        )

        content_layout.addWidget(
            self.preview_label,
            1,
        )

        content_layout.addLayout(
            right_layout
        )

        hotkey_label = QLabel(
            "F8  Start / Pause     •     "
            "F10  Emergency Stop"
        )

        hotkey_label.setObjectName(
            "muted"
        )

        central_widget = QWidget()

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            18,
            18,
            18,
            14,
        )

        main_layout.setSpacing(
            14
        )

        main_layout.addLayout(
            header_layout
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        main_layout.addWidget(
            self.dataset_panel
        )

        main_layout.addWidget(
            hotkey_label
        )

        self.setCentralWidget(
            central_widget
        )

        # ---------------------------------------------------------
        # Status bar
        # ---------------------------------------------------------

        self.status_bar = QStatusBar()

        self.setStatusBar(
            self.status_bar
        )

        self.status_bar.showMessage(
            "Ready"
        )

        # ---------------------------------------------------------
        # Timer
        # ---------------------------------------------------------

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.update_application
        )

        interval_ms = int(
            1000
            / settings.capture.capture_fps
        )

        self.timer.start(
            interval_ms
        )

        # ---------------------------------------------------------
        # Initial GUI state
        # ---------------------------------------------------------

        self._update_general_status()
        self._update_dataset_panel()

        self.diagnostics_panel.set_target(
            False,
            0,
            settings.target_detection.min_hp_pixels,
        )

        self.diagnostics_panel.set_model_loaded(
            self.monster_detector.model_loaded
        )

        logger.info(
            "GUI initialisiert."
        )

    # ---------------------------------------------------------
    # Main update
    # ---------------------------------------------------------

    def update_application(self):
        self._update_general_status()

        result = self.window_capture.capture()

        if result is None:
            self._handle_flyff_not_detected()
            return

        frame, window = result

        # ---------------------------------------------------------
        # Flyff found / restored
        # ---------------------------------------------------------

        if not self.flyff_was_detected:
            logger.info(
                "Flyff Client verfügbar."
            )

            self.diagnostics_manager.capture_event(
                event_name="flyff_detected",
                details={
                    "title": window.title,
                    "width": window.width,
                    "height": window.height,
                },
            )

        self.flyff_was_detected = True

        self.status_panel.set_flyff_detected(
            True
        )

        self.diagnostics_panel.set_window_detected(
            True
        )

        self.diagnostics_panel.set_resolution(
            window.width,
            window.height,
        )

        foreground = (
            self.input_controller.is_flyff_foreground(
                window
            )
        )

        self.diagnostics_panel.set_foreground(
            foreground
        )

        # ---------------------------------------------------------
        # Vision
        # ---------------------------------------------------------

        snapshot = self.vision_engine.analyze(
            frame
        )

        self.diagnostics_panel.set_target(
            snapshot.target.target_present,
            snapshot.target.hp_pixel_count,
            settings.target_detection.min_hp_pixels,
        )

        self.diagnostics_panel.set_detection_count(
            len(snapshot.monsters)
        )

        # ---------------------------------------------------------
        # Target transition diagnostics
        # ---------------------------------------------------------

        if (
                snapshot.target.target_present
                and not self.last_target_present
        ):
            self.diagnostics_manager.capture_event(
                event_name="target_detected",
                frame=frame,
                snapshot=snapshot,
            )

        elif (
                not snapshot.target.target_present
                and self.last_target_present
        ):
            self.diagnostics_manager.capture_event(
                event_name="target_disappeared",
                frame=frame,
                snapshot=snapshot,
            )

        self.last_target_present = (
            snapshot.target.target_present
        )

        # ---------------------------------------------------------
        # Dataset
        # ---------------------------------------------------------

        self.dataset_recorder.update(
            frame=frame,
            snapshot=snapshot,
        )

        # ---------------------------------------------------------
        # Bot
        # ---------------------------------------------------------

        height, width = (
            frame.shape[:2]
        )

        self.bot_controller.update(
            snapshot=snapshot,
            window=window,
            frame_width=width,
            frame_height=height,
        )

        # ---------------------------------------------------------
        # Bot state diagnostics
        # ---------------------------------------------------------

        current_state = (
            self.bot_controller.state
        )

        if current_state != self.last_bot_state:
            self._handle_bot_state_change(
                previous_state=self.last_bot_state,
                current_state=current_state,
                frame=frame,
                snapshot=snapshot,
            )

            self.last_bot_state = (
                current_state
            )

        # ---------------------------------------------------------
        # Debug overlay
        # ---------------------------------------------------------

        debug_frame = (
            self.monster_detector.draw_debug_overlay(
                frame,
                snapshot.monsters,
            )
        )

        debug_frame = (
            self.target_detector.draw_debug_overlay(
                debug_frame,
                snapshot.target,
            )
        )

        self._show_frame(
            debug_frame
        )

        # ---------------------------------------------------------
        # Status
        # ---------------------------------------------------------

        self.status_panel.set_monster_count(
            len(snapshot.monsters)
        )

        self.status_panel.set_kill_count(
            self.bot_controller.total_kills
        )

        target_text = (
            "YES"
            if snapshot.target.target_present
            else "NO"
        )

        self.status_bar.showMessage(
            f"Target: {target_text} | "
            f"HP pixels: "
            f"{snapshot.target.hp_pixel_count}"
        )

        self._update_general_status()
        self._update_dataset_panel()

    # ---------------------------------------------------------
    # Flyff window loss
    # ---------------------------------------------------------

    def _handle_flyff_not_detected(self):
        self.status_panel.set_flyff_detected(
            False
        )

        self.status_panel.set_monster_count(
            0
        )

        self.preview_label.clear()

        self.preview_label.setText(
            "Waiting for Flyff..."
        )

        self.diagnostics_panel.set_window_detected(
            False
        )

        self.diagnostics_panel.set_resolution(
            None,
            None,
        )

        self.diagnostics_panel.set_foreground(
            None
        )

        self.diagnostics_panel.set_detection_count(
            0
        )

        # Ein vorher vorhandenes Target ist nun nicht
        # mehr sinnvoll interpretierbar.
        self.last_target_present = False

        if self.flyff_was_detected:
            logger.warning(
                "Flyff Client verloren."
            )

            self.diagnostics_manager.capture_event(
                event_name="flyff_lost"
            )

            self.flyff_was_detected = False

        # -----------------------------------------------------
        # Safety:
        # Laufenden Bot automatisch pausieren.
        # -----------------------------------------------------

        if (
                settings.safety.pause_on_window_loss
                and self.bot_controller.state not in {
            BotState.IDLE,
            BotState.PAUSED,
            BotState.EMERGENCY_STOP,
        }
        ):
            logger.warning(
                "Bot wird pausiert, weil "
                "Flyff nicht mehr verfügbar ist."
            )

            self.input_controller.release_all_inputs()

            self.bot_controller.pause()

            self.farming_panel.set_paused(
                True
            )

        self._update_general_status()
        self._update_dataset_panel()

    # ---------------------------------------------------------
    # Diagnostics events
    # ---------------------------------------------------------

    def _handle_bot_state_change(
            self,
            previous_state: BotState,
            current_state: BotState,
            frame,
            snapshot,
    ):
        interesting_states = {
            BotState.TARGETING,
            BotState.ATTACKING,
            BotState.WAITING_FOR_KILL,
            BotState.ROTATING_CAMERA,
            BotState.EMERGENCY_STOP,
        }

        if current_state not in interesting_states:
            return

        self.diagnostics_manager.capture_event(
            event_name=(
                f"state_{current_state.name.lower()}"
            ),
            frame=frame,
            snapshot=snapshot,
            details={
                "previous_state": (
                    previous_state.name
                ),
                "current_state": (
                    current_state.name
                ),
            },
        )

    # ---------------------------------------------------------
    # Preview
    # ---------------------------------------------------------

    def _show_frame(
            self,
            frame,
    ):
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB,
        )

        height, width, channels = (
            rgb_frame.shape
        )

        bytes_per_line = (
                channels * width
        )

        image = QImage(
            rgb_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(
            image
        )

        pixmap = pixmap.scaled(
            self.preview_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.preview_label.setPixmap(
            pixmap
        )

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------

    def set_input_enabled(
            self,
            enabled: bool,
    ):
        settings.input.enabled = (
            enabled
        )

        logger.info(
            "Game Input: %s",
            "ON" if enabled else "OFF",
        )

        self._update_general_status()

    def set_attack_key(
            self,
            key: str,
    ):
        settings.combat.attack_key = (
            key.lower()
        )

        logger.info(
            "Attack Key geändert: %s",
            key.upper(),
        )

    def set_confidence(
            self,
            value: float,
    ):
        settings.targeting.minimum_confidence = (
            value
        )

        logger.info(
            "Minimum Confidence geändert: %.2f",
            value,
        )

    def set_camera_search(
            self,
            enabled: bool,
    ):
        settings.search.camera_search_enabled = (
            enabled
        )

        logger.info(
            "Automatic Camera Search: %s",
            "ON" if enabled else "OFF",
        )

    def set_dataset_interval(
            self,
            seconds: float,
    ):
        settings.dataset.capture_interval = (
            seconds
        )

        logger.info(
            "Dataset Interval geändert: %.2fs",
            seconds,
        )

    # ---------------------------------------------------------
    # Bot
    # ---------------------------------------------------------

    def start_bot(self):
        selected_monster = (
            self.farming_panel
            .monster_combo
            .currentData()
        )

        if selected_monster:
            settings.targeting.allowed_monsters = {
                selected_monster
            }

        self.bot_controller.start()

        self.farming_panel.set_paused(
            False
        )

        self._update_general_status()

    def pause_or_resume_bot(self):
        if (
                self.bot_controller.state
                == BotState.PAUSED
        ):
            self.bot_controller.resume()

            self.farming_panel.set_paused(
                False
            )

        elif self.bot_controller.state not in {
            BotState.IDLE,
            BotState.EMERGENCY_STOP,
        }:
            self.bot_controller.pause()

            self.input_controller.release_all_inputs()

            self.farming_panel.set_paused(
                True
            )

        self._update_general_status()

    def stop_bot(self):
        self.input_controller.release_all_inputs()

        self.bot_controller.stop()

        self.farming_panel.set_paused(
            False
        )

        self._update_general_status()

    def emergency_stop(self):
        self.bot_controller.emergency_stop()

        self.farming_panel.set_paused(
            False
        )

        self._update_general_status()

    def reset_emergency_stop(self):
        self.bot_controller.reset_emergency_stop()

        self.farming_panel.set_paused(
            False
        )

        self._update_general_status()

    # ---------------------------------------------------------
    # Hotkeys
    # ---------------------------------------------------------

    def handle_start_stop_hotkey(self):
        state = (
            self.bot_controller.state
        )

        if state == BotState.EMERGENCY_STOP:
            logger.warning(
                "F8 ignoriert: "
                "Emergency Stop aktiv."
            )
            return

        if state == BotState.IDLE:
            self.start_bot()
            return

        self.pause_or_resume_bot()

    # ---------------------------------------------------------
    # Dataset
    # ---------------------------------------------------------

    def toggle_dataset_recording(self):
        if self.dataset_recorder.recording:
            self.dataset_recorder.stop()

        else:
            self.dataset_recorder.start()

        self._update_dataset_panel()

    def _update_dataset_panel(self):
        self.dataset_panel.set_recording(
            self.dataset_recorder.recording
        )

        self.dataset_panel.set_image_count(
            self.dataset_recorder.image_count
        )

    # ---------------------------------------------------------
    # General status
    # ---------------------------------------------------------

    def _update_general_status(self):
        state = (
            self.bot_controller.state
        )

        self.status_panel.set_bot_status(
            state.name
        )

        self.status_panel.set_input_enabled(
            settings.input.enabled
        )

        emergency_active = (
                state
                == BotState.EMERGENCY_STOP
        )

        self.farming_panel.set_emergency_active(
            emergency_active
        )

    # ---------------------------------------------------------
    # Close
    # ---------------------------------------------------------

    def closeEvent(
            self,
            event,
    ):
        logger.info(
            "Anwendung wird beendet."
        )

        settings_manager.save()

        self.hotkey_manager.stop()

        self.dataset_recorder.stop()

        self.input_controller.release_all_inputs()

        self.bot_controller.stop()

        self.timer.stop()

        self.window_capture.close()

        event.accept()