import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from config.settings import settings
from utils.logger import logger
from vision.vision_engine import VisionSnapshot


class DiagnosticsManager:
    def __init__(self):
        self.enabled = settings.debug.enabled

        self.session_directory: Path | None = None
        self.screenshot_directory: Path | None = None
        self.session_file: Path | None = None

        self.event_count = 0

        self._start_session()

    def _start_session(self):
        if not self.enabled:
            return

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        self.session_directory = (
                settings.debug.debug_directory
                / timestamp
        )

        self.screenshot_directory = (
                self.session_directory
                / "screenshots"
        )

        self.screenshot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.session_file = (
                self.session_directory
                / "session.json"
        )

        self._write_session_file()

        logger.info(
            "Diagnostics Session gestartet | %s",
            self.session_directory,
        )

    def capture_event(
            self,
            event_name: str,
            frame: np.ndarray | None = None,
            snapshot: VisionSnapshot | None = None,
            details: dict | None = None,
    ):
        if not self.enabled:
            return

        self.event_count += 1

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        event_data = {
            "event_number": self.event_count,
            "event": event_name,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
        }

        if snapshot is not None:
            event_data["target"] = {
                "present": snapshot.target.target_present,
                "hp_pixel_count": snapshot.target.hp_pixel_count,
            }

            event_data["detections"] = [
                {
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "x": detection.x,
                    "y": detection.y,
                    "width": detection.width,
                    "height": detection.height,
                }
                for detection in snapshot.monsters
            ]

        if (
                frame is not None
                and settings.debug.save_screenshots
                and self.screenshot_directory is not None
        ):
            safe_event_name = self._sanitize_name(
                event_name
            )

            filename = (
                f"{timestamp}_{safe_event_name}.jpg"
            )

            image_path = (
                    self.screenshot_directory
                    / filename
            )

            success = cv2.imwrite(
                str(image_path),
                frame,
                [
                    cv2.IMWRITE_JPEG_QUALITY,
                    95,
                ],
            )

            if success:
                event_data["screenshot"] = filename
            else:
                logger.warning(
                    "Diagnostics Screenshot konnte "
                    "nicht gespeichert werden | %s",
                    image_path,
                )

        self._append_event(
            event_data
        )

        logger.info(
            "DIAGNOSTIC | %s",
            event_name,
        )

    def _append_event(
            self,
            event_data: dict,
    ):
        if self.session_file is None:
            return

        data = self._read_session_file()

        data["events"].append(
            event_data
        )

        data["event_count"] = (
            self.event_count
        )

        try:
            with self.session_file.open(
                    "w",
                    encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except OSError:
            logger.exception(
                "Diagnostics Session-Datei konnte "
                "nicht geschrieben werden."
            )

    def _write_session_file(self):
        if self.session_file is None:
            return

        data = {
            "started_at": datetime.now().isoformat(),
            "event_count": 0,
            "events": [],
        }

        try:
            with self.session_file.open(
                    "w",
                    encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except OSError:
            logger.exception(
                "Diagnostics Session konnte "
                "nicht angelegt werden."
            )

    def _read_session_file(
            self,
    ) -> dict:
        if (
                self.session_file is None
                or not self.session_file.exists()
        ):
            return {
                "events": [],
                "event_count": 0,
            }

        try:
            with self.session_file.open(
                    "r",
                    encoding="utf-8",
            ) as file:
                return json.load(
                    file
                )

        except (
                OSError,
                json.JSONDecodeError,
        ):
            logger.exception(
                "Diagnostics Session konnte "
                "nicht gelesen werden."
            )

            return {
                "events": [],
                "event_count": 0,
            }

    @staticmethod
    def _sanitize_name(
            value: str,
    ) -> str:
        allowed = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789_-"
        )

        sanitized = "".join(
            character
            if character in allowed
            else "_"
            for character in value
        )

        return sanitized[:80]