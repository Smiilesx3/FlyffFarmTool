import ctypes
from dataclasses import dataclass

import cv2
import mss
import numpy as np
import win32gui

from utils.logger import logger


@dataclass
class WindowInfo:
    hwnd: int
    title: str

    # Position der tatsächlichen Client-Area auf dem Desktop.
    client_left: int
    client_top: int

    # Größe der tatsächlichen Client-Area.
    width: int
    height: int


class WindowCapture:
    def __init__(self, title_contains: str = "Flyff"):
        self.title_contains = title_contains.lower()

        self.hwnd: int | None = None
        self.sct = mss.mss()

        self._last_logged_hwnd: int | None = None

        self._enable_dpi_awareness()

    @staticmethod
    def _enable_dpi_awareness():
        """
        Verhindert möglichst, dass Windows-DPI-Skalierung unsere
        Fensterkoordinaten verfälscht.
        """
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass

        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    def find_window(self) -> WindowInfo | None:
        matches: list[tuple[int, str]] = []

        def enum_callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            title = win32gui.GetWindowText(hwnd)

            if not title:
                return

            if self.title_contains in title.lower():
                matches.append((hwnd, title))

        win32gui.EnumWindows(enum_callback, None)

        if not matches:
            if self.hwnd is not None:
                logger.warning("Flyff-Fenster wurde verloren.")

            self.hwnd = None
            self._last_logged_hwnd = None
            return None

        hwnd, title = matches[0]
        self.hwnd = hwnd

        try:
            client_left, client_top, client_right, client_bottom = (
                win32gui.GetClientRect(hwnd)
            )

            screen_left, screen_top = win32gui.ClientToScreen(
                hwnd,
                (client_left, client_top),
            )

            screen_right, screen_bottom = win32gui.ClientToScreen(
                hwnd,
                (client_right, client_bottom),
            )

        except Exception:
            logger.exception(
                "Client-Area des Flyff-Fensters konnte nicht bestimmt werden."
            )
            return None

        width = screen_right - screen_left
        height = screen_bottom - screen_top

        if width <= 0 or height <= 0:
            return None

        if self._last_logged_hwnd != hwnd:
            logger.info(
                "Flyff-Fenster gefunden | Titel='%s' | Client=%sx%s | Position=%s,%s",
                title,
                width,
                height,
                screen_left,
                screen_top,
            )

            self._last_logged_hwnd = hwnd

        return WindowInfo(
            hwnd=hwnd,
            title=title,
            client_left=screen_left,
            client_top=screen_top,
            width=width,
            height=height,
        )

    def capture(self) -> tuple[np.ndarray, WindowInfo] | None:
        window = self.find_window()

        if window is None:
            return None

        monitor = {
            "left": window.client_left,
            "top": window.client_top,
            "width": window.width,
            "height": window.height,
        }

        try:
            screenshot = np.array(self.sct.grab(monitor))
        except Exception:
            logger.exception(
                "Screenshot der Flyff-Client-Area fehlgeschlagen."
            )
            return None

        frame = cv2.cvtColor(
            screenshot,
            cv2.COLOR_BGRA2BGR,
        )

        return frame, window

    def client_to_screen(
            self,
            x: int,
            y: int,
            window: WindowInfo,
    ) -> tuple[int, int]:
        """
        Wandelt eine Position innerhalb des Flyff-Bildes in eine
        absolute Windows-Bildschirmposition um.

        Beispiel:
            Monster im Flyff-Bild: (800, 350)
            Flyff beginnt Desktop:  (100, 70)

            Ergebnis:               (900, 420)
        """
        screen_x = window.client_left + x
        screen_y = window.client_top + y

        return screen_x, screen_y

    def close(self):
        self.sct.close()