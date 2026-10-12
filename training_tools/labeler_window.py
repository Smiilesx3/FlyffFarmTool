from pathlib import Path

from PySide6.QtCore import (
    QPoint,
    QRect,
    Qt,
)
from PySide6.QtGui import (
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from training_tools.dataset_labeler import (
    BoundingBox,
    DatasetLabeler,
)


class ImageCanvas(QLabel):
    def __init__(self):
        super().__init__()

        self.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.setMinimumSize(
            900,
            550,
        )

        self.original_pixmap: QPixmap | None = None
        self.display_pixmap: QPixmap | None = None

        self.boxes: list[BoundingBox] = []

        self.drag_start: QPoint | None = None
        self.drag_end: QPoint | None = None

        self.image_width = 0
        self.image_height = 0

        self.scale_factor = 1.0

        self.image_offset_x = 0
        self.image_offset_y = 0

        self.on_box_created = None

    # ---------------------------------------------------------
    # Image
    # ---------------------------------------------------------

    def set_image(
            self,
            image,
            boxes: list[BoundingBox],
    ):
        height, width, channels = (
            image.shape
        )

        self.image_width = width
        self.image_height = height

        bytes_per_line = (
                channels * width
        )

        rgb_image = image[
            :,
            :,
            ::-1
        ].copy()

        qimage = QImage(
            rgb_image.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        self.original_pixmap = (
            QPixmap.fromImage(
                qimage
            )
        )

        self.boxes = boxes

        self._rebuild_display()

    def _rebuild_display(self):
        if self.original_pixmap is None:
            return

        available_width = max(
            self.width(),
            1,
        )

        available_height = max(
            self.height(),
            1,
        )

        scaled = (
            self.original_pixmap.scaled(
                available_width,
                available_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

        self.display_pixmap = scaled

        self.scale_factor = (
                scaled.width()
                / self.image_width
        )

        self.image_offset_x = (
                                      self.width()
                                      - scaled.width()
                              ) // 2

        self.image_offset_y = (
                                      self.height()
                                      - scaled.height()
                              ) // 2

        self.update()

    # ---------------------------------------------------------
    # Painting
    # ---------------------------------------------------------

    def paintEvent(
            self,
            event,
    ):
        super().paintEvent(
            event
        )

        if self.display_pixmap is None:
            return

        painter = QPainter(
            self
        )

        painter.drawPixmap(
            self.image_offset_x,
            self.image_offset_y,
            self.display_pixmap,
        )

        pen = QPen()
        pen.setWidth(2)

        painter.setPen(
            pen
        )

        for box in self.boxes:
            rect = self._image_box_to_widget(
                box
            )

            painter.drawRect(
                rect
            )

        if (
                self.drag_start is not None
                and self.drag_end is not None
        ):
            painter.drawRect(
                QRect(
                    self.drag_start,
                    self.drag_end,
                ).normalized()
            )

        painter.end()

    # ---------------------------------------------------------
    # Mouse
    # ---------------------------------------------------------

    def mousePressEvent(
            self,
            event: QMouseEvent,
    ):
        if (
                event.button()
                != Qt.MouseButton.LeftButton
        ):
            return

        if not self._point_inside_image(
                event.position().toPoint()
        ):
            return

        self.drag_start = (
            event.position().toPoint()
        )

        self.drag_end = (
            self.drag_start
        )

        self.update()

    def mouseMoveEvent(
            self,
            event: QMouseEvent,
    ):
        if self.drag_start is None:
            return

        self.drag_end = (
            event.position().toPoint()
        )

        self.update()

    def mouseReleaseEvent(
            self,
            event: QMouseEvent,
    ):
        if (
                event.button()
                != Qt.MouseButton.LeftButton
        ):
            return

        if (
                self.drag_start is None
                or self.drag_end is None
        ):
            return

        start = self._widget_to_image(
            self.drag_start
        )

        end = self._widget_to_image(
            self.drag_end
        )

        self.drag_start = None
        self.drag_end = None

        if (
                start is None
                or end is None
        ):
            self.update()
            return

        box = BoundingBox(
            x1=start[0],
            y1=start[1],
            x2=end[0],
            y2=end[1],
        )

        if self.on_box_created:
            self.on_box_created(
                box
            )

        self.update()

    # ---------------------------------------------------------
    # Coordinates
    # ---------------------------------------------------------

    def _widget_to_image(
            self,
            point: QPoint,
    ) -> tuple[int, int] | None:

        if not self._point_inside_image(
                point
        ):
            return None

        x = int(
            (
                    point.x()
                    - self.image_offset_x
            )
            / self.scale_factor
        )

        y = int(
            (
                    point.y()
                    - self.image_offset_y
            )
            / self.scale_factor
        )

        x = max(
            0,
            min(
                self.image_width - 1,
                x,
                ),
        )

        y = max(
            0,
            min(
                self.image_height - 1,
                y,
                ),
        )

        return x, y

    def _image_box_to_widget(
            self,
            box: BoundingBox,
    ) -> QRect:

        x = int(
            box.x1
            * self.scale_factor
            + self.image_offset_x
        )

        y = int(
            box.y1
            * self.scale_factor
            + self.image_offset_y
        )

        width = int(
            (
                    box.x2
                    - box.x1
            )
            * self.scale_factor
        )

        height = int(
            (
                    box.y2
                    - box.y1
            )
            * self.scale_factor
        )

        return QRect(
            x,
            y,
            width,
            height,
        )

    def _point_inside_image(
            self,
            point: QPoint,
    ) -> bool:

        if self.display_pixmap is None:
            return False

        return (
                self.image_offset_x
                <= point.x()
                <= (
                        self.image_offset_x
                        + self.display_pixmap.width()
                )
                and
                self.image_offset_y
                <= point.y()
                <= (
                        self.image_offset_y
                        + self.display_pixmap.height()
                )
        )

    # ---------------------------------------------------------
    # Resize
    # ---------------------------------------------------------

    def resizeEvent(
            self,
            event,
    ):
        super().resizeEvent(
            event
        )

        self._rebuild_display()


class LabelerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Flyff Dataset Labeler"
        )

        self.resize(
            1300,
            850,
        )

        self.labeler = (
            DatasetLabeler()
        )

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        self.status_label = QLabel(
            "Choose an image folder to begin."
        )

        self.class_label = QLabel(
            "Class: Ghost of the Forgotten King"
        )

        # ---------------------------------------------------------
        # Canvas
        # ---------------------------------------------------------

        self.canvas = ImageCanvas()

        self.canvas.on_box_created = (
            self.add_box
        )

        # ---------------------------------------------------------
        # Buttons
        # ---------------------------------------------------------

        self.open_button = QPushButton(
            "Open Image Folder"
        )

        self.undo_button = QPushButton(
            "Undo Last Box"
        )

        self.clear_button = QPushButton(
            "Clear Boxes"
        )

        self.previous_button = QPushButton(
            "Previous"
        )

        self.skip_button = QPushButton(
            "Skip"
        )

        self.save_next_button = QPushButton(
            "Save & Next"
        )

        self.open_button.clicked.connect(
            self.open_directory
        )

        self.undo_button.clicked.connect(
            self.undo_box
        )

        self.clear_button.clicked.connect(
            self.clear_boxes
        )

        self.previous_button.clicked.connect(
            self.previous_image
        )

        self.skip_button.clicked.connect(
            self.skip_image
        )

        self.save_next_button.clicked.connect(
            self.save_and_next
        )

        # ---------------------------------------------------------
        # Layout
        # ---------------------------------------------------------

        top_layout = QHBoxLayout()

        top_layout.addWidget(
            self.open_button
        )

        top_layout.addWidget(
            self.class_label
        )

        top_layout.addStretch()

        edit_layout = QHBoxLayout()

        edit_layout.addWidget(
            self.undo_button
        )

        edit_layout.addWidget(
            self.clear_button
        )

        edit_layout.addStretch()

        navigation_layout = QHBoxLayout()

        navigation_layout.addWidget(
            self.previous_button
        )

        navigation_layout.addWidget(
            self.skip_button
        )

        navigation_layout.addWidget(
            self.save_next_button
        )

        main_layout = QVBoxLayout()

        main_layout.addLayout(
            top_layout
        )

        main_layout.addWidget(
            self.status_label
        )

        main_layout.addWidget(
            self.canvas,
            1,
        )

        main_layout.addLayout(
            edit_layout
        )

        main_layout.addLayout(
            navigation_layout
        )

        central_widget = QWidget()

        central_widget.setLayout(
            main_layout
        )

        self.setCentralWidget(
            central_widget
        )

        self._update_buttons()

    # ---------------------------------------------------------
    # Directory
    # ---------------------------------------------------------

    def open_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Flyff Image Folder",
        )

        if not directory:
            return

        self.labeler.load_directory(
            Path(directory)
        )

        self.show_current_image()

    # ---------------------------------------------------------
    # Image
    # ---------------------------------------------------------

    def show_current_image(self):
        image = (
            self.labeler.load_current_image()
        )

        if image is None:
            self.status_label.setText(
                "No image available."
            )

            self.canvas.clear()

            self._update_buttons()
            return

        self.canvas.set_image(
            image,
            self.labeler.boxes,
        )

        self.status_label.setText(
            f"Image "
            f"{self.labeler.current_index + 1}"
            f" / "
            f"{self.labeler.total_images}"
            f"    |    "
            f"Boxes: {len(self.labeler.boxes)}"
        )

        self._update_buttons()

    # ---------------------------------------------------------
    # Boxes
    # ---------------------------------------------------------

    def add_box(
            self,
            box: BoundingBox,
    ):
        self.labeler.add_box(
            box
        )

        self.show_current_image()

    def undo_box(self):
        self.labeler.undo_last_box()

        self.show_current_image()

    def clear_boxes(self):
        self.labeler.clear_boxes()

        self.show_current_image()

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    def save_and_next(self):
        self.labeler.save_current()

        if not self.labeler.next_image():
            self.status_label.setText(
                "Dataset complete."
            )

            self._update_buttons()
            return

        self.show_current_image()

    def skip_image(self):
        if not self.labeler.next_image():
            self.status_label.setText(
                "Dataset complete."
            )

            self._update_buttons()
            return

        self.show_current_image()

    def previous_image(self):
        if self.labeler.previous_image():
            self.show_current_image()

    # ---------------------------------------------------------
    # Button states
    # ---------------------------------------------------------

    def _update_buttons(self):
        has_images = (
                self.labeler.total_images > 0
        )

        self.undo_button.setEnabled(
            has_images
            and bool(
                self.labeler.boxes
            )
        )

        self.clear_button.setEnabled(
            has_images
            and bool(
                self.labeler.boxes
            )
        )

        self.previous_button.setEnabled(
            has_images
            and self.labeler.current_index > 0
        )

        self.skip_button.setEnabled(
            has_images
        )

        self.save_next_button.setEnabled(
            has_images
        )