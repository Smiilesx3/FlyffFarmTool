from pathlib import Path

from ultralytics import YOLO


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
}


def main():
    print()
    print("Flyff Monster Model Test")
    print("========================")
    print()

    model_input = input(
        "Pfad zu best.pt: "
    ).strip()

    image_input = input(
        "Pfad zum Ordner mit Testbildern: "
    ).strip()

    model_path = Path(
        model_input.strip('"')
    ).expanduser().resolve()

    image_directory = Path(
        image_input.strip('"')
    ).expanduser().resolve()

    if not model_path.exists():
        print()
        print(
            f"FEHLER: Modell nicht gefunden: {model_path}"
        )
        return

    if not image_directory.exists():
        print()
        print(
            f"FEHLER: Bilderordner nicht gefunden: "
            f"{image_directory}"
        )
        return

    image_paths = sorted(
        path
        for path in image_directory.iterdir()
        if (
                path.is_file()
                and path.suffix.lower()
                in SUPPORTED_EXTENSIONS
        )
    )

    if not image_paths:
        print()
        print(
            "FEHLER: Keine unterstützten Bilder gefunden."
        )
        return

    output_directory = (
            image_directory.parent
            / "model_test_results"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(f"Modell: {model_path}")
    print(f"Testbilder: {len(image_paths)}")
    print(f"Output: {output_directory}")
    print()

    model = YOLO(
        str(model_path)
    )

    total_detections = 0

    for index, image_path in enumerate(
            image_paths,
            start=1,
    ):
        results = model.predict(
            source=str(image_path),
            imgsz=640,
            conf=0.25,
            device="cpu",
            verbose=False,
        )

        result = results[0]

        detection_count = len(
            result.boxes
        )

        total_detections += (
            detection_count
        )

        plotted_image = (
            result.plot()
        )

        output_path = (
                output_directory
                / image_path.name
        )

        import cv2

        cv2.imwrite(
            str(output_path),
            plotted_image,
        )

        confidences = []

        if result.boxes is not None:
            for box in result.boxes:
                confidence = float(
                    box.conf[0].item()
                )

                confidences.append(
                    confidence
                )

        if confidences:
            confidence_text = ", ".join(
                f"{value:.2f}"
                for value in confidences
            )
        else:
            confidence_text = "-"

        print(
            f"[{index:03d}/{len(image_paths):03d}] "
            f"{image_path.name} | "
            f"Ghosts: {detection_count} | "
            f"Confidence: {confidence_text}"
        )

    print()
    print("========================")
    print("Test abgeschlossen")
    print("========================")
    print()
    print(
        f"Bilder:      {len(image_paths)}"
    )
    print(
        f"Detections:  {total_detections}"
    )
    print()
    print(
        f"Ergebnisse: {output_directory}"
    )


if __name__ == "__main__":
    main()