import math
import time
from enum import Enum, auto

from capture.window_capture import WindowInfo
from config.settings import settings
from input_control.game_input import InputController
from utils.logger import logger
from vision.monster_detector import MonsterDetection
from vision.vision_engine import VisionSnapshot


class BotState(Enum):
    IDLE = auto()
    SEARCHING = auto()
    SETTLING_CAMERA = auto()
    PIPELINE = auto()
    PAUSED = auto()
    EMERGENCY_STOP = auto()


class BotController:
    """
    Continuous Targeting Controller.

    V0.10.1:
    - Kein eigener Angriff/F2.
    - Flyff F-Tool übernimmt den Kampf.
    - YOLO läuft kontinuierlich.
    - Nahe Monster werden bevorzugt.
    - Große Bounding Boxes werden bevorzugt.
    - Monstergruppen erhalten einen kleinen Dichtebonus.
    """

    def __init__(
            self,
            input_controller: InputController,
    ):
        self.input_controller = input_controller

        self.state = BotState.IDLE
        self.state_started_at = time.monotonic()

        self.current_target: MonsterDetection | None = None

        self.last_target_click_time = 0.0

        # Noch bewusst konservativ.
        self.target_switch_interval = 1.50

        # Schutz gegen direktes Wiederanklicken
        # derselben Detection.
        self.same_target_radius = 120

        # Wenn kurzzeitig keine Detection vorhanden ist,
        # nicht sofort die Kamera drehen.
        self.no_target_timeout = 0.50

        self.no_target_since: float | None = None

        self.total_kills = 0
        self.total_target_clicks = 0

        # -----------------------------------------------------
        # Target Scoring
        # -----------------------------------------------------

        # Wie weit um einen Kandidaten herum nach weiteren
        # Ghosts für den Dichtebonus gesucht wird.
        self.density_radius = 350

        # Maximaler Dichtebonus.
        #
        # Dichte soll helfen, aber niemals einen weit entfernten
        # Ghost allein wegen einer großen Gruppe gewinnen lassen.
        self.max_density_neighbors = 5

        # Gewichtung des Dichtebonus.
        self.density_weight = 0.15

        # Gewichtung der Nähe zur Spielerposition.
        self.player_distance_weight = 0.35

        # Gewichtung der Bounding-Box-Größe.
        #
        # Das ist unser stärkstes Signal:
        # großer Ghost im Bild -> wahrscheinlich näher.
        self.box_size_weight = 0.50

    # =========================================================
    # Public control
    # =========================================================

    def start(self):
        if self.state == BotState.EMERGENCY_STOP:
            logger.warning(
                "Bot kann nicht gestartet werden: "
                "Emergency Stop ist aktiv."
            )
            return

        logger.info(
            "Bot gestartet | "
            "Continuous Proximity Targeting"
        )

        self.current_target = None
        self.last_target_click_time = 0.0
        self.no_target_since = None

        self._change_state(
            BotState.SEARCHING
        )

    def pause(self):
        if self.state in {
            BotState.IDLE,
            BotState.PAUSED,
            BotState.EMERGENCY_STOP,
        }:
            return

        self.input_controller.release_all_inputs()

        logger.info(
            "Bot pausiert."
        )

        self._change_state(
            BotState.PAUSED
        )

    def resume(self):
        if self.state != BotState.PAUSED:
            return

        logger.info(
            "Bot fortgesetzt."
        )

        self.current_target = None
        self.no_target_since = None

        self._change_state(
            BotState.SEARCHING
        )

    def stop(self):
        self.input_controller.release_all_inputs()

        self.current_target = None
        self.no_target_since = None

        logger.info(
            "Bot gestoppt."
        )

        self._change_state(
            BotState.IDLE
        )

    def emergency_stop(self):
        logger.critical(
            "Bot Emergency Stop."
        )

        self.input_controller.emergency_stop()

        self.current_target = None
        self.no_target_since = None

        self._change_state(
            BotState.EMERGENCY_STOP
        )

    def reset_emergency_stop(self):
        if self.state != BotState.EMERGENCY_STOP:
            return

        self.input_controller.reset_emergency_stop()

        self.current_target = None
        self.no_target_since = None

        logger.info(
            "Bot Emergency Stop zurueckgesetzt."
        )

        self._change_state(
            BotState.IDLE
        )

    # =========================================================
    # Main update
    # =========================================================

    def update(
            self,
            snapshot: VisionSnapshot,
            window: WindowInfo,
            frame_width: int,
            frame_height: int,
    ):
        if self.state in {
            BotState.IDLE,
            BotState.PAUSED,
            BotState.EMERGENCY_STOP,
        }:
            return

        if self.state == BotState.SEARCHING:
            self._handle_searching(
                snapshot,
                window,
            )

        elif self.state == BotState.SETTLING_CAMERA:
            self._handle_settling_camera(
                snapshot,
                window,
                frame_width,
                frame_height,
            )

        elif self.state == BotState.PIPELINE:
            self._handle_pipeline(
                snapshot,
                window,
                frame_width,
                frame_height,
            )

    # =========================================================
    # SEARCHING
    # =========================================================

    def _handle_searching(
            self,
            snapshot: VisionSnapshot,
            window: WindowInfo,
    ):
        candidates = self._filter_candidates(
            snapshot.monsters
        )

        if candidates:
            self.input_controller.stop_camera_rotation()

            self.no_target_since = None

            self._change_state(
                BotState.SETTLING_CAMERA
            )

            return

        self.current_target = None

        if not settings.search.camera_search_enabled:
            self.input_controller.stop_camera_rotation()
            return

        self.input_controller.start_camera_rotation(
            window
        )

    # =========================================================
    # CAMERA SETTLE
    # =========================================================

    def _handle_settling_camera(
            self,
            snapshot: VisionSnapshot,
            window: WindowInfo,
            frame_width: int,
            frame_height: int,
    ):
        if (
                self._state_elapsed()
                < settings.search.camera_settle_delay
        ):
            return

        candidates = self._filter_candidates(
            snapshot.monsters
        )

        if not candidates:
            logger.info(
                "Kein Monster nach Kamerastopp sichtbar."
            )

            self.current_target = None

            self._change_state(
                BotState.SEARCHING
            )

            return

        target = self._select_best_target(
            candidates=candidates,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        if not self._click_target(
                target,
                window,
        ):
            self.current_target = None

            self._change_state(
                BotState.SEARCHING
            )

            return

        self.current_target = target
        self.no_target_since = None

        self._change_state(
            BotState.PIPELINE
        )

    # =========================================================
    # CONTINUOUS TARGET PIPELINE
    # =========================================================

    def _handle_pipeline(
            self,
            snapshot: VisionSnapshot,
            window: WindowInfo,
            frame_width: int,
            frame_height: int,
    ):
        candidates = self._filter_candidates(
            snapshot.monsters
        )

        # -----------------------------------------------------
        # Keine Monster sichtbar
        # -----------------------------------------------------

        if not candidates:
            if self.no_target_since is None:
                self.no_target_since = time.monotonic()
                return

            no_target_duration = (
                    time.monotonic()
                    - self.no_target_since
            )

            if (
                    no_target_duration
                    >= self.no_target_timeout
            ):
                logger.info(
                    "Pipeline hat keine sichtbaren "
                    "Ghosts mehr | SEARCHING"
                )

                self.current_target = None
                self.no_target_since = None

                self._change_state(
                    BotState.SEARCHING
                )

            return

        self.no_target_since = None

        # -----------------------------------------------------
        # Mindestzeit zwischen zwei Klicks
        # -----------------------------------------------------

        elapsed_since_click = (
                time.monotonic()
                - self.last_target_click_time
        )

        if (
                elapsed_since_click
                < self.target_switch_interval
        ):
            return

        # -----------------------------------------------------
        # Aktuelles Target möglichst herausfiltern
        # -----------------------------------------------------

        next_candidates = (
            self._remove_current_target(
                candidates
            )
        )

        if not next_candidates:
            return

        # -----------------------------------------------------
        # Neuen Kandidaten anhand Nähe + Größe + Dichte wählen
        # -----------------------------------------------------

        next_target = self._select_best_target(
            candidates=next_candidates,
            frame_width=frame_width,
            frame_height=frame_height,
        )

        previous_target = (
            self.current_target
        )

        if self._click_target(
                next_target,
                window,
        ):
            self.current_target = next_target

            logger.info(
                "PIPELINE | Target vorausgewaehlt | "
                "previous=%s | next=%s | "
                "conf=%.2f | area=%s",
                (
                    previous_target.center
                    if previous_target
                    else None
                ),
                next_target.center,
                next_target.confidence,
                (
                        next_target.width
                        * next_target.height
                ),
            )

    # =========================================================
    # Target click
    # =========================================================

    def _click_target(
            self,
            target: MonsterDetection,
            window: WindowInfo,
    ) -> bool:

        click_x, click_y = (
            target.click_point
        )

        logger.info(
            "Target click geplant | "
            "class=%s | "
            "confidence=%.2f | "
            "box=(%s,%s,%s,%s) | "
            "area=%s | "
            "click=(%s,%s)",
            target.class_name,
            target.confidence,
            target.x,
            target.y,
            target.width,
            target.height,
            (
                    target.width
                    * target.height
            ),
            click_x,
            click_y,
        )

        click_sent = (
            self.input_controller.click_client_position(
                click_x,
                click_y,
                window,
            )
        )

        if not click_sent:
            logger.warning(
                "Target-Klick wurde nicht gesendet."
            )

            return False

        self.last_target_click_time = (
            time.monotonic()
        )

        self.total_target_clicks += 1

        logger.info(
            "Target angeklickt | "
            "Pipeline clicks=%s",
            self.total_target_clicks,
        )

        return True

    # =========================================================
    # Candidate filtering
    # =========================================================

    @staticmethod
    def _filter_candidates(
            detections: list[MonsterDetection],
    ) -> list[MonsterDetection]:

        return [
            detection
            for detection in detections
            if (
                    detection.class_name
                    in settings.targeting.allowed_monsters
                    and detection.confidence
                    >= settings.targeting.minimum_confidence
            )
        ]

    # =========================================================
    # Current target filtering
    # =========================================================

    def _remove_current_target(
            self,
            candidates: list[MonsterDetection],
    ) -> list[MonsterDetection]:

        if self.current_target is None:
            return candidates

        current_x, current_y = (
            self.current_target.center
        )

        radius_squared = (
                self.same_target_radius
                * self.same_target_radius
        )

        result: list[
            MonsterDetection
        ] = []

        for candidate in candidates:
            candidate_x, candidate_y = (
                candidate.center
            )

            dx = candidate_x - current_x
            dy = candidate_y - current_y

            distance_squared = (
                    dx * dx
                    + dy * dy
            )

            if (
                    distance_squared
                    <= radius_squared
            ):
                continue

            result.append(
                candidate
            )

        return result

    # =========================================================
    # Target scoring
    # =========================================================

    def _select_best_target(
            self,
            candidates: list[MonsterDetection],
            frame_width: int,
            frame_height: int,
    ) -> MonsterDetection:
        """
        Hoeherer Score = besseres Farmziel.

        Bewertung:

        50 % Bounding-Box-Groesse
            Groesser im Bild -> wahrscheinlich naeher.

        35 % Entfernung zur ungefaehren Spielerposition.

        15 % lokale Ghost-Dichte.

        Confidence wird hier NICHT als Distanzsignal verwendet.
        Sie wurde bereits beim Candidate Filtering geprueft.
        """

        if len(candidates) == 1:
            return candidates[0]

        player_x = (
                frame_width / 2.0
        )

        player_y = (
                frame_height * 0.62
        )

        frame_area = max(
            1.0,
            float(
                frame_width
                * frame_height
            ),
        )

        max_player_distance = math.sqrt(
            frame_width * frame_width
            + frame_height * frame_height
        )

        scored_candidates: list[
            tuple[
                float,
                MonsterDetection,
            ]
        ] = []

        for candidate in candidates:
            center_x, center_y = (
                candidate.center
            )

            # -------------------------------------------------
            # 1. Bounding Box Size
            # -------------------------------------------------

            box_area = (
                    candidate.width
                    * candidate.height
            )

            box_area_ratio = (
                    box_area
                    / frame_area
            )

            # Kleine YOLO-Boxen unterscheiden sich teilweise
            # nur minimal.
            #
            # sqrt macht den Wert etwas brauchbarer, ohne
            # gigantische Boxen komplett dominieren zu lassen.
            box_size_score = min(
                1.0,
                math.sqrt(
                    box_area_ratio
                    * 40.0
                ),
            )

            # -------------------------------------------------
            # 2. Entfernung zur Spielerposition
            # -------------------------------------------------

            dx = (
                    center_x
                    - player_x
            )

            dy = (
                    center_y
                    - player_y
            )

            player_distance = math.sqrt(
                dx * dx
                + dy * dy
            )

            normalized_distance = min(
                1.0,
                player_distance
                / max_player_distance,
                )

            player_proximity_score = (
                    1.0
                    - normalized_distance
            )

            # -------------------------------------------------
            # 3. Lokale Ghost-Dichte
            # -------------------------------------------------

            neighbor_count = (
                self._count_neighbors(
                    candidate,
                    candidates,
                )
            )

            density_score = min(
                1.0,
                (
                        neighbor_count
                        / self.max_density_neighbors
                ),
            )

            # -------------------------------------------------
            # Gesamt
            # -------------------------------------------------

            total_score = (
                    box_size_score
                    * self.box_size_weight
                    + player_proximity_score
                    * self.player_distance_weight
                    + density_score
                    * self.density_weight
            )

            scored_candidates.append(
                (
                    total_score,
                    candidate,
                )
            )

        scored_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_target = (
            scored_candidates[0]
        )

        logger.info(
            "TARGET SCORE | "
            "best=(%s,%s) | "
            "area=%s | "
            "confidence=%.2f | "
            "neighbors=%s | "
            "score=%.3f",
            best_target.center_x,
            best_target.center_y,
            (
                    best_target.width
                    * best_target.height
            ),
            best_target.confidence,
            self._count_neighbors(
                best_target,
                candidates,
            ),
            best_score,
        )

        return best_target

    # =========================================================
    # Density
    # =========================================================

    def _count_neighbors(
            self,
            target: MonsterDetection,
            candidates: list[MonsterDetection],
    ) -> int:

        target_x, target_y = (
            target.center
        )

        radius_squared = (
                self.density_radius
                * self.density_radius
        )

        neighbors = 0

        for candidate in candidates:
            if candidate is target:
                continue

            candidate_x, candidate_y = (
                candidate.center
            )

            dx = (
                    candidate_x
                    - target_x
            )

            dy = (
                    candidate_y
                    - target_y
            )

            distance_squared = (
                    dx * dx
                    + dy * dy
            )

            if (
                    distance_squared
                    <= radius_squared
            ):
                neighbors += 1

        return neighbors

    # =========================================================
    # State helpers
    # =========================================================

    def _change_state(
            self,
            new_state: BotState,
    ):
        if self.state == new_state:
            return

        logger.info(
            "STATE | %s -> %s",
            self.state.name,
            new_state.name,
        )

        self.state = new_state
        self.state_started_at = (
            time.monotonic()
        )

    def _state_elapsed(
            self,
    ) -> float:

        return (
                time.monotonic()
                - self.state_started_at
        )