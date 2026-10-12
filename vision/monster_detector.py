from dataclasses import dataclass

import cv2
import numpy as np
from ultralytics import YOLO

from utils.app_paths import MONSTER_MODEL_PATH
from utils.logger import logger


@dataclass
class MonsterDetection:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    class_name: str

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2

    @property
    def center(self) -> tuple[int, int]:
        return (
            self.center_x,
            self.center_y,
        )

    @property
    def click_point(self) -> tuple[int, int]:
        """
        Klickpunkt leicht unterhalb der geometrischen Mitte.
        """

        click_x = self.center_x

        click_y = int(
            self.y
            + self.height * 0.62
        )

        return (
            click_x,
            click_y,
        )


class MonsterDetector:
    def __init__(self):
        self.enabled = True

        self.model = None
        self.model_loaded = False

        self.inference_failed = False
        self.inference_error: str | None = None

        self.inference_confidence = 0.25

        self._load_model()

    # ---------------------------------------------------------
    # Model
    # ---------------------------------------------------------

    def _load_model(self):
        if not MONSTER_MODEL_PATH.exists():
            logger.warning(
                "Monster-Modell nicht gefunden | %s",
                MONSTER_MODEL_PATH,
            )
            return

        try:
            self.model = YOLO(
                str(MONSTER_MODEL_PATH)
            )

            self.model_loaded = True

            logger.info(
                "Monster-Modell geladen | %s",
                MONSTER_MODEL_PATH,
            )

        except Exception as exc:
            self.model = None
            self.model_loaded = False
            self.inference_failed = True
            self.inference_error = str(exc)

            logger.exception(
                "Monster-Modell konnte nicht geladen werden."
            )

    # ---------------------------------------------------------
    # Detection
    # ---------------------------------------------------------

    def detect(
            self,
            frame: np.ndarray,
    ) -> list[MonsterDetection]:

        if not self.enabled:
            return []

        if not self.model_loaded:
            return []

        if self.model is None:
            return []

        # Nach einem schweren Runtime-Fehler nicht bei jedem
        # Frame erneut versuchen und das Log fluten.
        if self.inference_failed:
            return []

        if frame is None or frame.size == 0:
            return []

        try:
            results = self.model.predict(
                source=frame,
                imgsz=640,
                conf=self.inference_confidence,
                device="cpu",
                verbose=False,
            )

        except Exception as exc:
            self.inference_failed = True
            self.inference_error = str(exc)

            logger.exception(
                "Monster Detection deaktiviert, "
                "weil die YOLO-Inferenz fehlgeschlagen ist."
            )

            return []

        if not results:
            return []

        result = results[0]

        detections: list[
            MonsterDetection
        ] = []

        if result.boxes is None:
            return detections

        names = result.names

        for box in result.boxes:
            xyxy = (
                box.xyxy[0]
                .cpu()
                .tolist()
            )

            x1, y1, x2, y2 = xyxy

            class_id = int(
                box.cls[0].item()
            )

            confidence = float(
                box.conf[0].item()
            )

            class_name = names.get(
                class_id,
                str(class_id),
            )

            x = max(
                0,
                int(x1),
            )

            y = max(
                0,
                int(y1),
            )

            width = max(
                1,
                int(x2 - x1),
            )

            height = max(
                1,
                int(y2 - y1),
            )

            detections.append(
                MonsterDetection(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    confidence=confidence,
                    class_name=class_name,
                )
            )

        return detections

    # ---------------------------------------------------------
    # Debug overlay
    # ---------------------------------------------------------

    @staticmethod
    def draw_debug_overlay(
            frame: np.ndarray,
            detections: list[MonsterDetection],
    ) -> np.ndarray:

        output = frame.copy()

        for detection in detections:
            x1 = detection.x
            y1 = detection.y

            x2 = (
                    detection.x
                    + detection.width
            )

            y2 = (
                    detection.y
                    + detection.height
            )

            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                1,
            )

            click_x, click_y = (
                detection.click_point
            )

            cv2.circle(
                output,
                (click_x, click_y),
                2,
                (0, 0, 255),
                -1,
            )

            label = (
                f"{detection.confidence:.0%}"
            )

            font_scale = 0.32
            thickness = 1

            text_size, _ = (
                cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    thickness,
                )
            )

            text_width, text_height = (
                text_size
            )

            text_x = x1

            text_y = max(
                text_height + 2,
                y1 - 3,
                )

            cv2.rectangle(
                output,
                (
                    text_x,
                    text_y - text_height - 2,
                ),
                (
                    text_x + text_width + 3,
                    text_y + 2,
                ),
                (0, 0, 0),
                -1,
            )

            cv2.putText(
                output,
                label,
                (
                    text_x + 1,
                    text_y,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA,
            )

        return output