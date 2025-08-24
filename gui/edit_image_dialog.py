"""
EditImageDialog: Simple dialog to preview an image and edit its annotation and optional label.
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QHBoxLayout, QComboBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class EditImageDialog(QDialog):
    def __init__(self, parent, image_path: str, annotation_text: str = "", label_options=None, initial_label: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Image")
        self.resize(700, 520)
        self._label_value = initial_label
        self._has_label = bool(label_options)

        lay = QVBoxLayout(self)
        # Preview
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        pm = QPixmap(image_path)
        if not pm.isNull():
            self.image_label.setPixmap(pm.scaled(480, 360, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.image_label.setText(image_path)
        lay.addWidget(self.image_label)

        # Optional label combo
        self.label_combo = None
        if label_options:
            row = QHBoxLayout()
            row.addWidget(QLabel("Label:"))
            self.label_combo = QComboBox()
            self.label_combo.addItems(list(label_options))
            if initial_label:
                idx = self.label_combo.findText(initial_label)
                if idx >= 0:
                    self.label_combo.setCurrentIndex(idx)
            row.addWidget(self.label_combo)
            row.addStretch(1)
            lay.addLayout(row)

        # Annotation editor
        self.edit = QTextEdit()
        self.edit.setPlainText(annotation_text or "")
        lay.addWidget(self.edit)

        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        lay.addWidget(btns)

    def get_values(self):
        lbl = None
        if self.label_combo is not None:
            lbl = self.label_combo.currentText()
        return lbl, self.edit.toPlainText()
