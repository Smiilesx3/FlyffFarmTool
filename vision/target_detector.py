from dataclasses import dataclass

import cv2
import numpy as np

from config.settings import settings


@dataclass
class TargetDetection:
    target_present: bool

    hp_pixel_count: int

    roi_x: int
    roi_y: int
    roi_width: int
    roi_height: int


class TargetDetector:
    """
    Erkennt, ob aktuell ein Target in Flyff ausgewählt ist.

    In der ersten Version wird bewusst kein OCR verwendet.
    Stattdessen suchen wir innerhalb eines definierten Bereichs
    nach der charakteristischen HP-Farbe der Target-Anzeige.
    """

    def __init__(self):
        self.config = settings.target_detection

    def detect(
            self,
            frame: np.ndarray,
    ) -> TargetDetection:

        height, width = frame.shape[:2]

        # ---------------------------------------------------------
        # Relative ROI -> Pixelkoordinaten
        # ---------------------------------------------------------

        x1 = int(width * self.config.roi_left)
        y1 = int(height * self.config.roi_top)

        x2 = int(width * self.config.roi_right)
        y2 = int(height * self.config.roi_bottom)

        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return TargetDetection(
                target_present=False,
                hp_pixel_count=0,
                roi_x=x1,
                roi_y=y1,
                roi_width=x2 - x1,
                roi_height=y2 - y1,
            )

        # ---------------------------------------------------------
        # BGR -> HSV
        # ---------------------------------------------------------

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV,
        )

        # ---------------------------------------------------------
        # HP-Farbe erkennen
        #
        # Wir beginnen relativ großzügig.
        # Diese Werte werden später mit echten Debug-Screenshots
        # angepasst.
        # ---------------------------------------------------------

        lower_hp = np.array(
            [35, 70, 50],
            dtype=np.uint8,
        )

        upper_hp = np.array(
            [95, 255, 255],
            dtype=np.uint8,
        )

        mask = cv2.inRange(
            hsv,
            lower_hp,
            upper_hp,
        )

        hp_pixel_count = int(
            cv2.countNonZero(mask)
        )

        target_present = (
                hp_pixel_count
                >= self.config.min_hp_pixels
        )

        return TargetDetection(
            target_present=target_present,
            hp_pixel_count=hp_pixel_count,
            roi_x=x1,
            roi_y=y1,
            roi_width=x2 - x1,
            roi_height=y2 - y1,
        )

    def draw_debug_overlay(
            self,
            frame: np.ndarray,
            detection: TargetDetection,
    ) -> np.ndarray:

        output = frame.copy()

        if not self.config.show_roi:
            return output

        x1 = detection.roi_x
        y1 = detection.roi_y

        x2 = x1 + detection.roi_width
        y2 = y1 + detection.roi_height

        color = (
            (0, 255, 0)
            if detection.target_present
            else (0, 165, 255)
        )

        cv2.rectangle(
            output,
            (x1, y1),
            (x2, y2),
            color,
            2,
        )

        if detection.target_present:
            status = "TARGET: YES"
        else:
            status = "TARGET: NO"

        label = (
            f"{status} | "
            f"HP pixels: {detection.hp_pixel_count}"
        )

        cv2.putText(
            output,
            label,
            (x1 + 5, y1 + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

        return output