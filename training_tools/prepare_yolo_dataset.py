import random
import shutil
from pathlib import Path


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

TRAIN_RATIO = 0.80
RANDOM_SEED = 42

CLASS_NAMES = [
    "ghost_forgotten_king",
]


def find_image_for_label(
        images_directory: Path,
        stem: str,
) -> Path | None:

    for extension in IMAGE_EXTENSIONS:
        candidate = (
                images_directory
                / f"{stem}{extension}"
        )

        if candidate.exists():
            return candidate

    return None


def prepare_dataset(
        source_directory: Path,
):
    source_images = (
            source_directory
            / "images"
    )

    source_labels = (
            source_directory
            / "labels"
    )

    if not source_images.exists():
        raise FileNotFoundError(
            f"Images-Ordner fehlt: {source_images}"
        )

    if not source_labels.exists():
        raise FileNotFoundError(
            f"Labels-Ordner fehlt: {source_labels}"
        )

    output_directory = (
            source_directory
            / "prepared"
    )

    train_images = (
            output_directory
            / "images"
            / "train"
    )

    val_images = (
            output_directory
            / "images"
            / "val"
    )

    train_labels = (
            output_directory
            / "labels"
            / "train"
    )

    val_labels = (
            output_directory
            / "labels"
            / "val"
    )

    # ---------------------------------------------------------
    # Alten prepared-Ordner entfernen
    # ---------------------------------------------------------

    if output_directory.exists():
        shutil.rmtree(
            output_directory
        )

    for directory in (
            train_images,
            val_images,
            train_labels,
            val_labels,
    ):
        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ---------------------------------------------------------
    # Gültige Bild/Label-Paare finden
    # ---------------------------------------------------------

    pairs: list[
        tuple[Path, Path]
    ] = []

    label_files = sorted(
        source_labels.glob(
            "*.txt"
        )
    )

    for label_path in label_files:
        image_path = find_image_for_label(
            source_images,
            label_path.stem,
        )

        if image_path is None:
            print(
                "WARNUNG: Kein Bild für Label:",
                label_path.name,
            )
            continue

        pairs.append(
            (
                image_path,
                label_path,
            )
        )

    if not pairs:
        raise RuntimeError(
            "Keine gültigen Bild/Label-Paare gefunden."
        )

    # ---------------------------------------------------------
    # Reproduzierbar mischen
    # ---------------------------------------------------------

    random.seed(
        RANDOM_SEED
    )

    random.shuffle(
        pairs
    )

    # ---------------------------------------------------------
    # 80 / 20 Split
    # ---------------------------------------------------------

    split_index = int(
        len(pairs)
        * TRAIN_RATIO
    )

    # Sicherstellen, dass beide Bereiche Daten enthalten.
    split_index = max(
        1,
        min(
            len(pairs) - 1,
            split_index,
            ),
    )

    train_pairs = (
        pairs[:split_index]
    )

    val_pairs = (
        pairs[split_index:]
    )

    # ---------------------------------------------------------
    # Dateien kopieren
    # ---------------------------------------------------------

    copy_pairs(
        train_pairs,
        train_images,
        train_labels,
    )

    copy_pairs(
        val_pairs,
        val_images,
        val_labels,
    )

    # ---------------------------------------------------------
    # dataset.yaml
    # ---------------------------------------------------------

    yaml_path = (
            output_directory
            / "dataset.yaml"
    )

    yaml_content = (
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "\n"
        "names:\n"
    )

    for class_id, class_name in enumerate(
            CLASS_NAMES
    ):
        yaml_content += (
            f"  {class_id}: "
            f"{class_name}\n"
        )

    yaml_path.write_text(
        yaml_content,
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Statistik
    # ---------------------------------------------------------

    print()
    print(
        "======================================"
    )

    print(
        "Flyff YOLO Dataset vorbereitet"
    )

    print(
        "======================================"
    )

    print(
        f"Gesamt:     {len(pairs)}"
    )

    print(
        f"Training:   {len(train_pairs)}"
    )

    print(
        f"Validation: {len(val_pairs)}"
    )

    print()

    print(
        f"Output: {output_directory}"
    )

    print()

    print(
        "Klassen:"
    )

    for class_id, class_name in enumerate(
            CLASS_NAMES
    ):
        print(
            f"  {class_id}: {class_name}"
        )


def copy_pairs(
        pairs: list[
            tuple[Path, Path]
        ],
        image_destination: Path,
        label_destination: Path,
):
    for image_path, label_path in pairs:
        shutil.copy2(
            image_path,
            image_destination
            / image_path.name,
            )

        shutil.copy2(
            label_path,
            label_destination
            / label_path.name,
            )


if __name__ == "__main__":
    print(
        "Flyff YOLO Dataset Preparation"
    )

    print()

    source = input(
        "Pfad zum yolo_dataset Ordner: "
    ).strip()

    source_directory = Path(
        source.strip('"')
    ).expanduser().resolve()

    prepare_dataset(
        source_directory
    )