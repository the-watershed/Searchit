"""
UploadPage: Handles image upload, annotation, and OpenAI analysis.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QTextEdit, QListWidget, QListWidgetItem, QSplitter, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QSize
from db import DB
from openai_client import analyze_image
import os


class UploadPage(QWidget):
    def upload_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not paths:
            self.log_box.append("[INFO] No images selected.")
            return
        for path in paths:
            if path not in self.image_paths:
                self.image_paths.append(path)
                # Add thumbnail
                from PyQt5.QtGui import QIcon
                pixmap = QPixmap(path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item = QListWidgetItem()
                item.setIcon(QIcon(pixmap))
                item.setToolTip(path)
                self.thumbnails_list.addItem(item)
                # Add annotation box
                anno = QTextEdit()
                anno.setPlaceholderText(f"Annotation for {os.path.basename(path)}")
                self.annotation_boxes.append(anno)
                self.annos_layout.addWidget(anno)
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.image_paths = []  # List of image paths for this item
        self.annotation_boxes = []  # List of annotation QTextEdit widgets
        self.init_ui()


    def init_ui(self):
        import json, os
        main_layout = QHBoxLayout()
        # Left: Upload/Analyze controls
        left_layout = QVBoxLayout()
        self.upload_btn = QPushButton("Upload Image(s)")
        self.upload_btn.clicked.connect(self.upload_images)
        left_layout.addWidget(self.upload_btn)
        self.analyze_btn = QPushButton("Analyze with OpenAI")
        self.analyze_btn.clicked.connect(self.analyze)
        left_layout.addWidget(self.analyze_btn)
        self.save_btn = QPushButton("Save to Catalog")
        self.save_btn.clicked.connect(self.save)
        self.save_btn.setEnabled(False)
        left_layout.addWidget(self.save_btn)
        # Logging box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(120)
        left_layout.addWidget(QLabel("Log:"))
        left_layout.addWidget(self.log_box)
        left_layout.addStretch()

        # Warn if no OpenAI key
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        key_missing = True
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                try:
                    config = json.load(f)
                    if config.get("openai_api_key", "").strip():
                        key_missing = False
                except Exception:
                    pass
        if key_missing:
            self.log_box.append("[WARNING] No OpenAI API key set. Research functions are offline until a key is entered in Settings.")

        # Right: Thumbnails and annotation boxes
        right_layout = QVBoxLayout()
        self.thumbnails_list = QListWidget()
        self.thumbnails_list.setViewMode(QListWidget.IconMode)
        self.thumbnails_list.setIconSize(QSize(128, 128))
        self.thumbnails_list.setResizeMode(QListWidget.Adjust)
        self.thumbnails_list.setSpacing(10)
        self.thumbnails_list.setMaximumHeight(160)
        right_layout.addWidget(QLabel("Uploaded Images:"))
        right_layout.addWidget(self.thumbnails_list)
        self.annos_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Annotations (one per image):"))
        self.annos_widget = QWidget()
        self.annos_widget.setLayout(self.annos_layout)
        right_layout.addWidget(self.annos_widget)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)
    def analyze(self):
        if not self.image_paths:
            self.log_box.append("[ERROR] Upload at least one image first.")
            return
        self.log_box.append("[INFO] Starting OpenAI analysis...")
        annotations = [anno.toPlainText() for anno in self.annotation_boxes]
        combined_notes = "\n".join(annotations)
        results = []
        for path, note in zip(self.image_paths, annotations):
            self.log_box.append(f"[INFO] Analyzing {os.path.basename(path)}...")
            result = analyze_image(path, combined_notes)
            results.append(result)
            self.log_box.append(f"[RESULT] {os.path.basename(path)}: {result}")
        self.log_box.append("\n---\n".join(results))
        self.save_btn.setEnabled(True)


    def save(self):
        if not self.image_paths:
            self.log_box.append("[ERROR] Upload at least one image first.")
            return
        annotations = [anno.toPlainText() for anno in self.annotation_boxes]
        combined_notes = "\n".join(annotations)
        openai_result = self.log_box.toPlainText()
        item_id = self.db.add_item(self.image_paths[0], combined_notes, openai_result)
        for path, note in zip(self.image_paths[1:], annotations[1:]):
            self.db.add_revision(item_id, note, "")
        self.log_box.append(f"[INFO] Saved item #{item_id} to catalog.")
        # Reset for next item
        self.image_paths = []
        self.thumbnails_list.clear()
        for anno in self.annotation_boxes:
            anno.deleteLater()
        self.annotation_boxes = []
        self.save_btn.setEnabled(False)
