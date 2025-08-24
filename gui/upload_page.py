"""
UploadPage: Handles image upload, annotation, OCR, OpenAI analysis, and saving to DB.
"""

import os
import sys
import json
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTextEdit,
    QSplitter,
    QSizePolicy,
    QGridLayout,
    QGroupBox,
    QDialog,
    QDialogButtonBox,
    QCheckBox,
    QScrollArea,
    QHBoxLayout,
    QComboBox,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from db import DB
from .edit_image_dialog import EditImageDialog
from .utils import run_in_thread


class UploadPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.image_paths = []
        self.annotation_boxes = []
        self.rows = []  # list of dicts: {path, thumb, anno, label, container}
        self.ocr_hints = {}  # path -> text
        self._stdout = None
        self._stderr = None
        # Cached AI analysis result and the image set it corresponds to
        self._last_ai_json = None  # exact JSON string from the last analyze() call, if any
        self._last_ai_images = tuple()  # tuple of image paths used to produce _last_ai_json
        self.init_ui()

    def init_ui(self):
        # Left: controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()

        self.upload_btn = QPushButton("Add Image(s)")
        self.upload_btn.clicked.connect(self.upload_images)
        left_layout.addWidget(self.upload_btn)

        self.clear_btn = QPushButton("Clear All Images")
        self.clear_btn.clicked.connect(self.clear_images)
        left_layout.addWidget(self.clear_btn)

        self.ocr_btn = QPushButton("Scan with OCR for Branding/Maker's Marks")
        self.ocr_btn.clicked.connect(self.scan_with_ocr)
        btn_height = self.upload_btn.sizeHint().height()
        self.ocr_btn.setFixedHeight(btn_height)
        left_layout.addWidget(self.ocr_btn)

        self.analyze_btn = QPushButton("Analyze with OpenAI")
        self.analyze_btn.clicked.connect(self.analyze)
        left_layout.addWidget(self.analyze_btn)

        self.save_btn = QPushButton("Save to Catalog")
        self.save_btn.clicked.connect(self.save)
        self.save_btn.setEnabled(False)
        left_layout.addWidget(self.save_btn)

        # Logging box (fills remaining left column height)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        left_layout.addWidget(QLabel("Log:"))
        left_layout.addWidget(self.log_box, 1)
        left_widget.setLayout(left_layout)

        # Right: thumbnails and annotations
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Uploaded Images and Annotations:"))
        self.images_annos_grid = QGridLayout()
        self.images_annos_grid.setSpacing(12)
        self.images_annos_grid.setColumnStretch(0, 1)
        self.images_annos_grid.setColumnStretch(1, 1)
        self.images_annos_group = QGroupBox()
        self.images_annos_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.images_annos_group.setLayout(self.images_annos_grid)
        right_layout.addWidget(self.images_annos_group, 1)
        right_widget.setLayout(right_layout)

        # Splitter (fills whole page)
        self.splitter = QSplitter()
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setSizes([300, 900])
        try:
            self.splitter.setStretchFactor(0, 0)
            self.splitter.setStretchFactor(1, 1)
            self.splitter.setChildrenCollapsible(False)
        except Exception:
            pass
        layout = QVBoxLayout()
        layout.addWidget(self.splitter)
        self.setLayout(layout)

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

    def upload_images(self):
        # Append new images to the existing list/grid; do not clear existing
        from PyQt5.QtCore import QSettings
        settings = QSettings("JUREKA", "ProvenanceToyShop")
        last_dir = settings.value("last_upload_dir", "")
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", last_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not paths:
            self.log_box.append("[INFO] No images selected.")
            return
        settings.setValue("last_upload_dir", os.path.dirname(paths[0]))
        for path in paths:
            if not any(r['path'] == path for r in self.rows):
                self._add_row(path)
        # Image set changed; invalidate previous AI result
        self._invalidate_ai_cache()
        self._rebuild_grid_from_rows()
        self._sync_lists()
        if self.image_paths:
            self.save_btn.setEnabled(True)

    def clear_images(self):
        # Remove all widgets from the grid and reset lists
        while self.images_annos_grid.count():
            it = self.images_annos_grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
        for r in self.rows:
            try:
                r['anno'].deleteLater()
                r['thumb'].deleteLater()
                r['container'].deleteLater()
            except Exception:
                pass
        self.rows = []
        self.annotation_boxes = []
        self.image_paths = []
        self._invalidate_ai_cache()
        self.save_btn.setEnabled(False)
        self.log_box.append("[INFO] Cleared all selected images and annotations.")

    def scan_with_ocr(self):
        """Run OCR on uploaded images in a background thread, then prompt to apply."""
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            self.log_box.append("[ERROR] pytesseract and Pillow are required for OCR. Please install them.")
            return
        if not self.image_paths:
            self.log_box.append("[ERROR] Upload at least one image before scanning with OCR.")
            return
        self.log_box.append("[INFO] Scanning images with OCR (background)...")

        def _work(paths):
            out = []
            for path in paths:
                branding_text = ""
                ok_default = False
                try:
                    text = pytesseract.image_to_string(Image.open(path))
                    lines = [line.strip() for line in text.splitlines() if line.strip()]
                    branding_lines = [line for line in lines if 2 < len(line) < 40 and any(c.isupper() for c in line)]
                    branding_text = '\n'.join(branding_lines) if branding_lines else text.strip()
                    ok_default = bool(branding_text)
                except Exception as e:
                    # Collect error as empty text but log on UI later
                    branding_text = f""
                out.append((path, branding_text, ok_default))
            return out

        def _on_result(ocr_results):
            dlg = OcrReviewDialog(ocr_results, parent=self)
            if dlg.exec_() == QDialog.Accepted:
                applied = 0
                for path, apply_it, text in dlg.get_results():
                    try:
                        idx = self.image_paths.index(path)
                    except ValueError:
                        continue
                    if apply_it and idx < len(self.annotation_boxes):
                        self.annotation_boxes[idx].setPlainText(text)
                        self.ocr_hints[path] = text
                        applied += 1
                self.log_box.append(f"[INFO] Applied OCR to {applied} image(s).")
            else:
                self.log_box.append("[INFO] OCR results discarded by user.")

        run_in_thread(_work, list(self.image_paths), on_result=_on_result)

    def analyze(self):
        self._sync_lists()
        if not self.image_paths:
            self.log_box.append("[ERROR] Upload at least one image first.")
            return
        self.log_box.append("[INFO] Starting OpenAI analysis (background)...")
        annotations = [anno.toPlainText() for anno in self.annotation_boxes]
        # Build per-image captions and OCR hints
        captions = []
        ocrs = []
        for r in self.rows:
            label_text = r['label'].currentText() if r.get('label') else ''
            captions.append(f"{label_text}: {os.path.basename(r['path'])}" if label_text else os.path.basename(r['path']))
            ocrs.append(self.ocr_hints.get(r['path'], ""))
        from openai_client import analyze_images
        analyze_images.log_box = self.log_box  # Ensure log_box is set for debug output
        try:
            analyze_images.meta = {"captions": captions, "ocr_hints": ocrs}
        except Exception:
            pass
        self.log_box.append("[INFO] Sending all images and annotations to AI for unified analysis...")

        def _work(paths, annos):
            return analyze_images(paths, annos)

        def _on_result(result):
            # Keep raw JSON if possible for DB mapping
            self._last_ai_json = None
            try:
                parsed = json.loads(result)
                self._last_ai_json = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                self._last_ai_json = None
            # Bind the cached result to the current image set
            self._last_ai_images = tuple(self.image_paths)
            self.log_box.append(f"[RESULT] {result}")
            self.save_btn.setEnabled(True)

        run_in_thread(_work, list(self.image_paths), annotations, on_result=_on_result)

    def save(self):
        if not self.image_paths:
            self.log_box.append("[ERROR] Upload at least one image first.")
            return
        annotations = [anno.toPlainText() for anno in self.annotation_boxes]
        combined_notes = "\n".join(annotations)
        # Use cached JSON only if it matches the current image set; otherwise skip to avoid stale data
        if self._last_ai_json and tuple(self.image_paths) == self._last_ai_images:
            openai_result = self._last_ai_json
        else:
            openai_result = ""
            if not self._last_ai_json:
                self.log_box.append("[WARN] No AI analysis found for this set; saving without structured fields.")
            else:
                self.log_box.append("[WARN] Images changed since analysis; saving without structured fields. Re-run Analyze for mapped fields.")
        # Save the item (legacy image_path for compatibility, but all images go in images table)
        item_id = self.db.add_item(self.image_paths[0], combined_notes, openai_result)
        for path, annotation in zip(self.image_paths, annotations):
            self.db.add_image(item_id, path, annotation)
        for note in annotations[1:]:
            self.db.add_revision(item_id, note)
        self.log_box.append(f"[INFO] Saved item #{item_id} to catalog with {len(self.image_paths)} images.")
        # Reset UI
        self.clear_images()

    # --- Internal: invalidate AI cache on image set changes ---
    def _invalidate_ai_cache(self):
        self._last_ai_json = None
        self._last_ai_images = tuple()

    def closeEvent(self, event):
        # Restore stdout/stderr
        if self._stdout is not None:
            sys.stdout = self._stdout
        if self._stderr is not None:
            sys.stderr = self._stderr
        super().closeEvent(event)

    def get_splitter_sizes(self):
        if hasattr(self, 'splitter') and self.splitter is not None:
            return self.splitter.sizes()
        return []

    def set_splitter_sizes(self, sizes):
        self.splitter.setSizes(sizes)

    # --- Internal helpers for rows/grid management ---
    def _sync_lists(self):
        self.image_paths = [r['path'] for r in self.rows]
        self.annotation_boxes = [r['anno'] for r in self.rows]

    def _add_row(self, path):
        pixmap = QPixmap(path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_label = QLabel(); img_label.setPixmap(pixmap); img_label.setToolTip(path)
        img_label.setContextMenuPolicy(Qt.CustomContextMenu)
        anno = QTextEdit(); anno.setPlaceholderText(f"Annotation for {os.path.basename(path)}")
        # Controls: label combo + up/down/remove
        row_container = QWidget()
        vbox = QVBoxLayout(row_container); vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(anno)
        ctrl = QHBoxLayout()
        label = QComboBox(); label.addItems([
            "Front", "Back", "Underside", "Mark/Stamp", "Label/Box", "Serial/Patent", "Detail", "Other"
        ])
        btn_up = QPushButton("Up"); btn_down = QPushButton("Down"); btn_rm = QPushButton("Remove")
        ctrl.addWidget(QLabel("Label:")); ctrl.addWidget(label); ctrl.addStretch(1)
        ctrl.addWidget(btn_up); ctrl.addWidget(btn_down); ctrl.addWidget(btn_rm)
        vbox.addLayout(ctrl)
        row = {"path": path, "thumb": img_label, "anno": anno, "label": label, "container": row_container}
        self.rows.append(row)

        def _find_index():
            for i, r in enumerate(self.rows):
                if r['path'] == path:
                    return i
            return -1

        def move(delta):
            i = _find_index()
            j = i + delta
            if i < 0 or j < 0 or j >= len(self.rows):
                return
            self.rows[i], self.rows[j] = self.rows[j], self.rows[i]
            self._rebuild_grid_from_rows(); self._sync_lists(); self._invalidate_ai_cache()

        btn_up.clicked.connect(lambda: move(-1))
        btn_down.clicked.connect(lambda: move(1))
        def remove():
            i = _find_index()
            if i < 0:
                return
            r = self.rows.pop(i)
            try:
                r['anno'].deleteLater(); r['thumb'].deleteLater(); r['container'].deleteLater()
            except Exception:
                pass
            self._rebuild_grid_from_rows(); self._sync_lists(); self._invalidate_ai_cache()
            if not self.rows:
                self.save_btn.setEnabled(False)
        btn_rm.clicked.connect(remove)

        # Context menu on image thumbnail
        def _on_thumb_menu(pos):
            from PyQt5.QtWidgets import QMenu, QFileDialog
            menu = QMenu(self)
            act_edit = menu.addAction("Edit…")
            act_replace = menu.addAction("Replace…")
            act_remove = menu.addAction("Remove")
            action = menu.exec_(img_label.mapToGlobal(pos))
            if action == act_edit:
                # Offer label options
                label_options = [
                    "Front", "Back", "Underside", "Mark/Stamp", "Label/Box", "Serial/Patent", "Detail", "Other"
                ]
                dlg = EditImageDialog(self, path, anno.toPlainText(), label_options, label.currentText())
                if dlg.exec_():
                    new_label, new_text = dlg.get_values()
                    if new_label is not None:
                        idx = label.findText(new_label)
                        if idx >= 0:
                            label.setCurrentIndex(idx)
                    anno.setPlainText(new_text)
            elif action == act_replace:
                new_path, _ = QFileDialog.getOpenFileName(self, "Choose Replacement Image", os.path.dirname(path), "Images (*.png *.jpg *.jpeg *.bmp)")
                if new_path:
                    # Update row path and thumbnail
                    row["path"] = new_path
                    pm2 = QPixmap(new_path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_label.setPixmap(pm2)
                    img_label.setToolTip(new_path)
                    self._sync_lists(); self._invalidate_ai_cache()
            elif action == act_remove:
                remove()

        img_label.customContextMenuRequested.connect(_on_thumb_menu)

    def _rebuild_grid_from_rows(self):
        # Clear grid
        while self.images_annos_grid.count():
            it = self.images_annos_grid.takeAt(0)
            w = it.widget()
            if w:
                w.setParent(None)
        # Re-add in order
        for idx, r in enumerate(self.rows):
            self.images_annos_grid.addWidget(r['thumb'], idx, 0)
            self.images_annos_grid.addWidget(r['container'], idx, 1)


class OcrReviewDialog(QDialog):
    """Dialog to review OCR text per image and approve/reject before applying."""
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Review OCR Results")
        self.resize(900, 600)
        self._entries = []  # list of dicts: {path, edit, check}

        main_layout = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)

        for path, text, ok_default in results:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            # thumbnail
            thumb_label = QLabel()
            try:
                pm = QPixmap(path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                thumb_label.setPixmap(pm)
            except Exception:
                thumb_label.setText(os.path.basename(path))
            row_layout.addWidget(thumb_label)

            # text + checkbox
            right_box = QVBoxLayout()
            edit = QTextEdit()
            edit.setPlainText(text)
            check = QCheckBox(f"Apply to: {os.path.basename(path)}")
            check.setChecked(bool(ok_default))
            right_box.addWidget(edit)
            right_box.addWidget(check)
            row_layout.addLayout(right_box)

            vbox.addWidget(row)
            self._entries.append({"path": path, "edit": edit, "check": check})

        vbox.addStretch(1)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Select All / None controls
        sel_layout = QHBoxLayout()
        btn_all = QPushButton("Select All"); btn_none = QPushButton("Select None")
        sel_layout.addWidget(btn_all); sel_layout.addWidget(btn_none); sel_layout.addStretch(1)
        main_layout.addLayout(sel_layout)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        main_layout.addWidget(btns)

        def _set_all(val: bool):
            for e in self._entries:
                try:
                    e["check"].setChecked(val)
                except Exception:
                    pass
        btn_all.clicked.connect(lambda: _set_all(True))
        btn_none.clicked.connect(lambda: _set_all(False))

    def get_results(self):
        out = []
        for entry in self._entries:
            out.append((entry["path"], entry["check"].isChecked(), entry["edit"].toPlainText()))
        return out
