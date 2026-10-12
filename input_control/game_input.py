import time

import win32gui

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController

from capture.window_capture import WindowInfo
from config.settings import settings
from utils.logger import logger


class InputController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()

        self.input_config = settings.input
        self.safety_config = settings.safety
        self.combat_config = settings.combat
        self.search_config = settings.search

        self.emergency_stopped = False

        self.camera_rotation_active = False
        self.camera_rotation_key = None

    # ---------------------------------------------------------
    # Safety
    # ---------------------------------------------------------

    @staticmethod
    def is_flyff_foreground(
            window: WindowInfo,
    ) -> bool:
        try:
            foreground_hwnd = (
                win32gui.GetForegroundWindow()
            )

            return (
                    foreground_hwnd
                    == window.hwnd
            )

        except Exception:
            logger.exception(
                "Vordergrundfenster konnte "
                "nicht geprüft werden."
            )
            return False

    def can_send_input(
            self,
            window: WindowInfo,
    ) -> bool:

        if self.emergency_stopped:
            return False

        if not self.input_config.enabled:
            return False

        if (
                self.safety_config.require_flyff_foreground
                and not self.is_flyff_foreground(window)
        ):
            return False

        return True

    # ---------------------------------------------------------
    # Mouse
    # ---------------------------------------------------------

    def click_client_position(
            self,
            x: int,
            y: int,
            window: WindowInfo,
    ) -> bool:

        screen_x = (
                window.client_left + x
        )

        screen_y = (
                window.client_top + y
        )

        logger.info(
            "Target click | Client=(%s,%s) | "
            "Screen=(%s,%s)",
            x,
            y,
            screen_x,
            screen_y,
        )

        if not self.can_send_input(
                window
        ):
            return False

        try:
            self.mouse.position = (
                screen_x,
                screen_y,
            )

            time.sleep(
                self.input_config.click_delay
            )

            if not self.can_send_input(
                    window
            ):
                return False

            self.mouse.click(
                Button.left,
                1,
            )

            return True

        except Exception:
            logger.exception(
                "Linksklick konnte nicht "
                "gesendet werden."
            )

            return False

    # ---------------------------------------------------------
    # Attack
    # ---------------------------------------------------------

    def press_attack_key(
            self,
            window: WindowInfo,
    ) -> bool:

        key_name = (
            self.combat_config.attack_key
        )

        if not self.can_send_input(
                window
        ):
            return False

        key = self._resolve_key(
            key_name
        )

        if key is None:
            logger.error(
                "Unbekannte Taste: %s",
                key_name,
            )
            return False

        try:
            if not self.can_send_input(
                    window
            ):
                return False

            self.keyboard.press(
                key
            )

            time.sleep(
                0.03
            )

            self.keyboard.release(
                key
            )

            logger.info(
                "Attack-Key gesendet: %s",
                key_name,
            )

            return True

        except Exception:
            try:
                self.keyboard.release(
                    key
                )
            except Exception:
                pass

            logger.exception(
                "Attack-Key konnte nicht "
                "gesendet werden."
            )

            return False

    # ---------------------------------------------------------
    # Camera
    # ---------------------------------------------------------

    def start_camera_rotation(
            self,
            window: WindowInfo,
    ) -> bool:

        if self.camera_rotation_active:
            return True

        if not self.can_send_input(
                window
        ):
            return False

        key = self._resolve_key(
            self.search_config.camera_rotation_key
        )

        if key is None:
            logger.error(
                "Ungültige Kamera-Taste: %s",
                self.search_config.camera_rotation_key,
            )
            return False

        try:
            self.keyboard.press(
                key
            )

            self.camera_rotation_key = key
            self.camera_rotation_active = True

            logger.info(
                "Kamerarotation gestartet | key=%s",
                self.search_config.camera_rotation_key,
            )

            return True

        except Exception:
            logger.exception(
                "Kamerarotation konnte "
                "nicht gestartet werden."
            )

            return False

    def stop_camera_rotation(
            self,
    ):
        if not self.camera_rotation_active:
            return

        try:
            if self.camera_rotation_key is not None:
                self.keyboard.release(
                    self.camera_rotation_key
                )

        except Exception:
            logger.exception(
                "Kamera-Taste konnte nicht "
                "freigegeben werden."
            )

        finally:
            self.camera_rotation_key = None
            self.camera_rotation_active = False

            logger.info(
                "Kamerarotation gestoppt."
            )

    # ---------------------------------------------------------
    # Emergency Stop
    # ---------------------------------------------------------

    def emergency_stop(self):
        self.emergency_stopped = True

        self.release_all_inputs()

        logger.critical(
            "EMERGENCY STOP aktiviert."
        )

    def reset_emergency_stop(self):
        self.emergency_stopped = False

        logger.info(
            "Emergency Stop zurückgesetzt."
        )

    # ---------------------------------------------------------
    # Cleanup
    # ---------------------------------------------------------

    def release_all_inputs(self):
        self.stop_camera_rotation()

        try:
            self.mouse.release(
                Button.left
            )
        except Exception:
            pass

        try:
            self.mouse.release(
                Button.right
            )
        except Exception:
            pass

        # Sicherheitshalber alle für uns relevanten
        # Pfeiltasten freigeben.
        for key in (
                Key.left,
                Key.right,
                Key.up,
                Key.down,
        ):
            try:
                self.keyboard.release(
                    key
                )
            except Exception:
                pass

    # ---------------------------------------------------------
    # Key resolver
    # ---------------------------------------------------------

    @staticmethod
    def _resolve_key(
            key_name: str,
    ):
        normalized = (
            key_name
            .strip()
            .lower()
        )

        special_keys = {
            "f1": Key.f1,
            "f2": Key.f2,
            "f3": Key.f3,
            "f4": Key.f4,
            "f5": Key.f5,
            "f6": Key.f6,
            "f7": Key.f7,
            "f8": Key.f8,
            "f9": Key.f9,
            "f10": Key.f10,
            "f11": Key.f11,
            "f12": Key.f12,

            "left": Key.left,
            "right": Key.right,
            "up": Key.up,
            "down": Key.down,

            "space": Key.space,
            "enter": Key.enter,
            "esc": Key.esc,
        }

        if normalized in special_keys:
            return special_keys[
                normalized
            ]

        if len(normalized) == 1:
            return normalized

        return None