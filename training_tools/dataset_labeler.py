import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2


@dataclass
class BoundingBox:
    x1: int
    y1: int
    x2: int
    y2: int

    def normalized(
            self,
            image_width: int,
            image_height: int,
    ) -> tuple[float, float, float, float]:
        width = self.x2 - self.x1
        height = self.y2 - self.y1

        center_x = self.x1 + width / 2
        center_y = self.y1 + height / 2

        return (
            center_x / image_width,
            center_y / image_height,
            width / image_width,
            height / image_height,
        )


class DatasetLabeler:
    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
    }

    CLASS_ID = 0
    CLASS_NAME = "ghost_forgotten_king"

    def __init__(self):
        self.source_directory: Path | None = None
        self.output_directory: Path | None = None

        self.image_paths: list[Path] = []

        self.current_index = 0

        self.boxes: list[BoundingBox] = []

    # ---------------------------------------------------------
    # Dataset loading
    # ---------------------------------------------------------

    def load_directory(
            self,
            directory: Path,
    ):
        self.source_directory = directory

        self.image_paths = sorted(
            path
            for path in directory.iterdir()
            if (
                    path.is_file()
                    and path.suffix.lower()
                    in self.SUPPORTED_EXTENSIONS
            )
        )

        self.current_index = 0
        self.boxes = []

        self.output_directory = (
                directory.parent
                / "yolo_dataset"
        )

        self._create_output_structure()

    # ---------------------------------------------------------
    # Output structure
    # ---------------------------------------------------------

    def _create_output_structure(self):
        if self.output_directory is None:
            return

        directories = (
            self.output_directory / "images",
            self.output_directory / "labels",
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

    # ---------------------------------------------------------
    # Current image
    # ---------------------------------------------------------

    @property
    def current_image_path(
            self,
    ) -> Path | None:
        if not self.image_paths:
            return None

        if self.current_index >= len(
                self.image_paths
        ):
            return None

        return self.image_paths[
            self.current_index
        ]

    @property
    def total_images(
            self,
    ) -> int:
        return len(
            self.image_paths
        )

    def load_current_image(self):
        path = self.current_image_path

        if path is None:
            return None

        return cv2.imread(
            str(path)
        )

    # ---------------------------------------------------------
    # Boxes
    # ---------------------------------------------------------

    def add_box(
            self,
            box: BoundingBox,
    ):
        x1 = min(
            box.x1,
            box.x2,
        )

        y1 = min(
            box.y1,
            box.y2,
        )

        x2 = max(
            box.x1,
            box.x2,
        )

        y2 = max(
            box.y1,
            box.y2,
        )

        # Versehentliche Mini-Klicks ignorieren.
        if (
                x2 - x1 < 5
                or y2 - y1 < 5
        ):
            return

        self.boxes.append(
            BoundingBox(
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
            )
        )

    def undo_last_box(self):
        if self.boxes:
            self.boxes.pop()

    def clear_boxes(self):
        self.boxes.clear()

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    def save_current(
            self,
    ):
        image_path = (
            self.current_image_path
        )

        if (
                image_path is None
                or self.output_directory is None
        ):
            return

        image = cv2.imread(
            str(image_path)
        )

        if image is None:
            return

        image_height, image_width = (
            image.shape[:2]
        )

        output_image = (
                self.output_directory
                / "images"
                / image_path.name
        )

        output_label = (
                self.output_directory
                / "labels"
                / f"{image_path.stem}.txt"
        )

        shutil.copy2(
            image_path,
            output_image,
        )

        lines = []

        for box in self.boxes:
            (
                center_x,
                center_y,
                width,
                height,
            ) = box.normalized(
                image_width,
                image_height,
            )

            lines.append(
                f"{self.CLASS_ID} "
                f"{center_x:.6f} "
                f"{center_y:.6f} "
                f"{width:.6f} "
                f"{height:.6f}"
            )

        output_label.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def next_image(
            self,
    ) -> bool:
        if (
                self.current_index + 1
                >= len(self.image_paths)
        ):
            return False

        self.current_index += 1
        self.boxes = []

        return True

    def previous_image(
            self,
    ) -> bool:
        if self.current_index <= 0:
            return False

        self.current_index -= 1
        self.boxes = []

        return True