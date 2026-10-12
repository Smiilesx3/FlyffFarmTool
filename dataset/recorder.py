import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from config.settings import settings
from utils.logger import logger
from vision.vision_engine import VisionSnapshot


class DatasetRecorder:
    def __init__(self):
        self.config = settings.dataset

        self.recording = False

        self.session_directory: Path | None = None
        self.image_directory: Path | None = None
        self.metadata_directory: Path | None = None

        self.last_capture_time = 0.0
        self.image_count = 0

    # ---------------------------------------------------------
    # Recording control
    # ---------------------------------------------------------

    def start(self):
        if self.recording:
            return

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        self.session_directory = (
                self.config.output_directory
                / "recordings"
                / timestamp
        )

        self.image_directory = (
                self.session_directory
                / "images"
        )

        self.metadata_directory = (
                self.session_directory
                / "metadata"
        )

        self.image_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.metadata_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.image_count = 0
        self.last_capture_time = 0.0
        self.recording = True

        logger.info(
            "Dataset Recording gestartet | %s",
            self.session_directory,
        )

    def stop(self):
        if not self.recording:
            return

        logger.info(
            "Dataset Recording beendet | "
            "Bilder=%s | Session=%s",
            self.image_count,
            self.session_directory,
        )

        self.recording = False

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update(
            self,
            frame: np.ndarray,
            snapshot: VisionSnapshot,
    ):
        if not self.recording:
            return

        now = time.monotonic()

        elapsed = (
                now - self.last_capture_time
        )

        if (
                elapsed
                < self.config.capture_interval
        ):
            return

        self.last_capture_time = now

        self._save_sample(
            frame,
            snapshot,
        )

    # ---------------------------------------------------------
    # Save sample
    # ---------------------------------------------------------

    def _save_sample(
            self,
            frame: np.ndarray,
            snapshot: VisionSnapshot,
    ):
        if (
                self.image_directory is None
                or self.metadata_directory is None
        ):
            return

        self.image_count += 1

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        sample_name = (
            f"frame_{timestamp}_{self.image_count:06d}"
        )

        image_path = (
                self.image_directory
                / f"{sample_name}.jpg"
        )

        metadata_path = (
                self.metadata_directory
                / f"{sample_name}.json"
        )

        # -----------------------------------------------------
        # RAW FRAME speichern
        # -----------------------------------------------------

        cv2.imwrite(
            str(image_path),
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                self.config.jpeg_quality,
            ],
        )

        # -----------------------------------------------------
        # Metadaten
        # -----------------------------------------------------

        height, width = frame.shape[:2]

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "image": image_path.name,
            "width": width,
            "height": height,
            "target": {
                "present": (
                    snapshot.target.target_present
                ),
                "hp_pixel_count": (
                    snapshot.target.hp_pixel_count
                ),
            },
            "detections": [
                {
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "x": detection.x,
                    "y": detection.y,
                    "width": detection.width,
                    "height": detection.height,
                }
                for detection in snapshot.monsters
            ],
        }

        with metadata_path.open(
                "w",
                encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                indent=2,
                ensure_ascii=False,
            )

        logger.debug(
            "Dataset Sample gespeichert | %s",
            image_path.name,
        )