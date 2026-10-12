import sys
from pathlib import Path


def get_app_directory() -> Path:
    """
    Verzeichnis für beschreibbare Runtime-Daten.

    Entwicklung:
        Projektverzeichnis

    PyInstaller:
        Verzeichnis der FlyffFarmTool.exe
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_resource_directory() -> Path:
    """
    Verzeichnis für mit PyInstaller gebündelte Ressourcen.

    Im Entwicklungsmodus entspricht es dem Projektverzeichnis.
    """

    if getattr(sys, "frozen", False):
        meipass = getattr(
            sys,
            "_MEIPASS",
            None,
        )

        if meipass:
            return Path(meipass).resolve()

        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


APP_DIRECTORY = get_app_directory()
RESOURCE_DIRECTORY = get_resource_directory()

CONFIG_DIRECTORY = APP_DIRECTORY / "config"
LOG_DIRECTORY = APP_DIRECTORY / "logs"
DEBUG_DIRECTORY = APP_DIRECTORY / "debug"

DATA_DIRECTORY = APP_DIRECTORY / "data"
DATASET_DIRECTORY = DATA_DIRECTORY / "datasets"

MODEL_DIRECTORY = RESOURCE_DIRECTORY / "models"

MONSTER_MODEL_PATH = (
        MODEL_DIRECTORY
        / "flyff_monsters.pt"
)


def create_runtime_directories():
    directories = (
        CONFIG_DIRECTORY,
        LOG_DIRECTORY,
        DEBUG_DIRECTORY,
        DATA_DIRECTORY,
        DATASET_DIRECTORY,
    )

    for directory in directories:
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )