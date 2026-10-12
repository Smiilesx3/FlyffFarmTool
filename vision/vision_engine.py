from dataclasses import dataclass

import numpy as np

from vision.monster_detector import (
    MonsterDetection,
    MonsterDetector,
)
from vision.target_detector import (
    TargetDetection,
    TargetDetector,
)


@dataclass
class VisionSnapshot:
    monsters: list[MonsterDetection]
    target: TargetDetection


class VisionEngine:
    def __init__(
            self,
            monster_detector: MonsterDetector,
            target_detector: TargetDetector,
    ):
        self.monster_detector = monster_detector
        self.target_detector = target_detector

    def analyze(
            self,
            frame: np.ndarray,
    ) -> VisionSnapshot:

        monsters = self.monster_detector.detect(
            frame
        )

        target = self.target_detector.detect(
            frame
        )

        return VisionSnapshot(
            monsters=monsters,
            target=target,
        )