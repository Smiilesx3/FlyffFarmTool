from dataclasses import dataclass, field

from utils.app_paths import (
    DATASET_DIRECTORY,
    DEBUG_DIRECTORY,
    LOG_DIRECTORY,
)


@dataclass
class CaptureSettings:
    window_title_contains: str = "Mocomochi FlyFF"
    capture_fps: int = 10


@dataclass
class CombatSettings:
    attack_key: str = "f2"

    target_acquire_timeout: float = 1.5
    kill_timeout: float = 8.0

    post_kill_delay: float = 0.25


@dataclass
class TargetDetectionSettings:
    roi_left: float = 0.25
    roi_top: float = 0.00
    roi_right: float = 0.75
    roi_bottom: float = 0.18

    min_hp_pixels: int = 100
    show_roi: bool = True


@dataclass
class TargetingSettings:
    minimum_confidence: float = 0.55

    allowed_monsters: set[str] = field(
        default_factory=lambda: {
            "ghost_forgotten_king"
        }
    )


@dataclass
class SearchSettings:
    camera_search_enabled: bool = True

    # Kamera wird über die rechte Pfeiltaste gesteuert.
    camera_rotation_key: str = "right"

    # Kurze Stabilisierung, nachdem die Kamera gestoppt wurde.
    camera_settle_delay: float = 0.25


@dataclass
class InputSettings:
    enabled: bool = False

    click_delay: float = 0.05


@dataclass
class SafetySettings:
    start_stop_hotkey: str = "f8"
    emergency_stop_hotkey: str = "f10"

    require_flyff_foreground: bool = True

    pause_on_window_loss: bool = True


@dataclass
class DatasetSettings:
    output_directory = DATASET_DIRECTORY

    capture_interval: float = 0.5
    jpeg_quality: int = 95


@dataclass
class DebugSettings:
    enabled: bool = True
    save_screenshots: bool = True

    debug_directory = DEBUG_DIRECTORY
    log_directory = LOG_DIRECTORY


@dataclass
class AppSettings:
    capture: CaptureSettings = field(
        default_factory=CaptureSettings
    )

    combat: CombatSettings = field(
        default_factory=CombatSettings
    )

    target_detection: TargetDetectionSettings = field(
        default_factory=TargetDetectionSettings
    )

    targeting: TargetingSettings = field(
        default_factory=TargetingSettings
    )

    search: SearchSettings = field(
        default_factory=SearchSettings
    )

    input: InputSettings = field(
        default_factory=InputSettings
    )

    safety: SafetySettings = field(
        default_factory=SafetySettings
    )

    dataset: DatasetSettings = field(
        default_factory=DatasetSettings
    )

    debug: DebugSettings = field(
        default_factory=DebugSettings
    )


settings = AppSettings()