from collections.abc import Callable

from pynput import keyboard

from config.settings import settings
from utils.logger import logger


class HotkeyManager:
    def __init__(
            self,
            on_start_stop: Callable[[], None],
            on_emergency_stop: Callable[[], None],
    ):
        self.on_start_stop = on_start_stop
        self.on_emergency_stop = on_emergency_stop

        self.listener: keyboard.Listener | None = None

        self.start_stop_key = self._resolve_key(
            settings.safety.start_stop_hotkey
        )

        self.emergency_key = self._resolve_key(
            settings.safety.emergency_stop_hotkey
        )

    def start(self):
        if self.listener is not None:
            return

        self.listener = keyboard.Listener(
            on_press=self._on_press
        )

        self.listener.start()

        logger.info(
            "Globale Hotkeys gestartet | Start/Stop=%s | Emergency=%s",
            settings.safety.start_stop_hotkey.upper(),
            settings.safety.emergency_stop_hotkey.upper(),
        )

    def stop(self):
        if self.listener is None:
            return

        self.listener.stop()
        self.listener = None

        logger.info(
            "Globale Hotkeys beendet."
        )

    def _on_press(self, key):
        try:
            if key == self.emergency_key:
                logger.warning(
                    "Emergency-Hotkey gedrückt."
                )

                self.on_emergency_stop()
                return

            if key == self.start_stop_key:
                logger.info(
                    "Start/Stop-Hotkey gedrückt."
                )

                self.on_start_stop()

        except Exception:
            logger.exception(
                "Fehler bei Verarbeitung eines globalen Hotkeys."
            )

    @staticmethod
    def _resolve_key(
            key_name: str,
    ):
        normalized = key_name.strip().lower()

        special_keys = {
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
        }

        key = special_keys.get(normalized)

        if key is None:
            raise ValueError(
                f"Nicht unterstützter Hotkey: {key_name}"
            )

        return key