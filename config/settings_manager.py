import json

from config.settings import settings
from utils.app_paths import CONFIG_DIRECTORY
from utils.logger import logger


class SettingsManager:
    def __init__(self):
        self.config_directory = (
            CONFIG_DIRECTORY
        )

        self.config_file = (
                self.config_directory
                / "user_settings.json"
        )

    def load(self):
        if not self.config_file.exists():
            logger.info(
                "Keine user_settings.json vorhanden. "
                "Verwende Standardeinstellungen."
            )
            return

        try:
            with self.config_file.open(
                    "r",
                    encoding="utf-8",
            ) as file:
                data = json.load(
                    file
                )

            self._apply(
                data
            )

            logger.info(
                "Benutzereinstellungen geladen | %s",
                self.config_file,
            )

        except (
                OSError,
                json.JSONDecodeError,
                TypeError,
                ValueError,
        ):
            logger.exception(
                "Benutzereinstellungen konnten "
                "nicht geladen werden. "
                "Standardeinstellungen bleiben aktiv."
            )

    def save(self):
        self.config_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        data = {
            "combat": {
                "attack_key": (
                    settings.combat.attack_key
                ),
            },
            "targeting": {
                "minimum_confidence": (
                    settings.targeting.minimum_confidence
                ),
                "allowed_monsters": sorted(
                    settings.targeting.allowed_monsters
                ),
            },
            "search": {
                "camera_search_enabled": (
                    settings.search.camera_search_enabled
                ),
            },
            "input": {
                # Absichtlich niemals dauerhaft aktiv.
                "enabled": False,
            },
            "dataset": {
                "capture_interval": (
                    settings.dataset.capture_interval
                ),
            },
        }

        try:
            with self.config_file.open(
                    "w",
                    encoding="utf-8",
            ) as file:
                json.dump(
                    data,
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            logger.info(
                "Benutzereinstellungen gespeichert | %s",
                self.config_file,
            )

        except OSError:
            logger.exception(
                "Benutzereinstellungen konnten "
                "nicht gespeichert werden."
            )

    @staticmethod
    def _apply(
            data: dict,
    ):
        combat = data.get(
            "combat",
            {},
        )

        attack_key = combat.get(
            "attack_key"
        )

        if isinstance(
                attack_key,
                str,
        ):
            settings.combat.attack_key = (
                attack_key.lower()
            )

        targeting = data.get(
            "targeting",
            {},
        )

        confidence = targeting.get(
            "minimum_confidence"
        )

        if isinstance(
                confidence,
                (int, float),
        ):
            settings.targeting.minimum_confidence = max(
                0.10,
                min(
                    1.00,
                    float(confidence),
                ),
            )

        allowed_monsters = targeting.get(
            "allowed_monsters"
        )

        if (
                isinstance(
                    allowed_monsters,
                    list,
                )
                and all(
            isinstance(
                item,
                str,
            )
            for item in allowed_monsters
        )
        ):
            settings.targeting.allowed_monsters = set(
                allowed_monsters
            )

        search = data.get(
            "search",
            {},
        )

        camera_search = search.get(
            "camera_search_enabled"
        )

        if isinstance(
                camera_search,
                bool,
        ):
            settings.search.camera_search_enabled = (
                camera_search
            )

        dataset = data.get(
            "dataset",
            {},
        )

        capture_interval = dataset.get(
            "capture_interval"
        )

        if isinstance(
                capture_interval,
                (int, float),
        ):
            settings.dataset.capture_interval = max(
                0.1,
                min(
                    5.0,
                    float(capture_interval),
                ),
            )

        # Echte Inputs sind nach JEDEM Neustart aus.
        settings.input.enabled = False


settings_manager = SettingsManager()