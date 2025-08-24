"""
EditItemDialog: Full-featured popup editor for catalog items.
- Edits core fields (title, brand, maker, description, condition, notes, provenance_notes, prc_low/med/hi).
- Manages images (add/remove/rotate) with history logging.
- Shows revision history (notes-only), field changes, and image history.
"""
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QSplitter,
    QWidget,
)
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt, QSize
import os
from db import DB


class EditItemDialog(QDialog):
    def __init__(self, parent, item_id: int):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Catalog Item #{item_id}")
        self.db = DB()
        self.item_id = item_id
        self.item = self.db.get_item(item_id) or {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: edit form
        left = QWidget()
        form = QFormLayout(left)

        self.title_edit = QLineEdit(self.item.get('title', ''))
        self.brand_edit = QLineEdit(self.item.get('brand', ''))
        self.maker_edit = QLineEdit(self.item.get('maker', ''))
        self.description_edit = QTextEdit(self.item.get('description', ''))
        self.condition_edit = QLineEdit(self.item.get('condition', ''))
        self.provenance_notes_edit = QTextEdit(self.item.get('provenance_notes', ''))
        self.notes_edit = QTextEdit(self.item.get('notes', ''))

        # Price range fields (editable)
        pr_low = self.item.get('prc_low')
        pr_med = self.item.get('prc_med')
        pr_hi = self.item.get('prc_hi')
        if pr_low in (None, '') and pr_med in (None, '') and pr_hi in (None, ''):
            pr_low, pr_med, pr_hi = self.db.get_price_range(self.item_id)
        self.prc_low_edit = QLineEdit('' if pr_low in (None, '') else str(pr_low))
        self.prc_med_edit = QLineEdit('' if pr_med in (None, '') else str(pr_med))
        self.prc_hi_edit = QLineEdit('' if pr_hi in (None, '') else str(pr_hi))

        # Form rows
        form.addRow(QLabel("Title:"), self.title_edit)
        form.addRow(QLabel("Brand:"), self.brand_edit)
        form.addRow(QLabel("Maker:"), self.maker_edit)
        form.addRow(QLabel("Description:"), self.description_edit)
        form.addRow(QLabel("Condition:"), self.condition_edit)
        form.addRow(QLabel("Price Low:"), self.prc_low_edit)
        form.addRow(QLabel("Price Med:"), self.prc_med_edit)
        form.addRow(QLabel("Price High:"), self.prc_hi_edit)
        form.addRow(QLabel("Provenance Notes:"), self.provenance_notes_edit)
        form.addRow(QLabel("Notes:"), self.notes_edit)

        # Right: images and histories
        right = QWidget()
        right_layout = QVBoxLayout(right)

        # Images panel
        self.img_list = QListWidget()
        self.img_list.setViewMode(QListWidget.IconMode)
        self.img_list.setIconSize(QSize(128, 128))
        self.img_list.setResizeMode(QListWidget.Adjust)
        self.img_list.setSpacing(10)
        self._reload_images()
        img_btns = QHBoxLayout()
        add_img_btn = QPushButton("Add")
        remove_img_btn = QPushButton("Remove")
        rotate_img_btn = QPushButton("Rotate 90°")
        img_btns.addWidget(add_img_btn)
        img_btns.addWidget(remove_img_btn)
        img_btns.addWidget(rotate_img_btn)

        add_img_btn.clicked.connect(self._add_image)
        remove_img_btn.clicked.connect(self._remove_selected_image)
        rotate_img_btn.clicked.connect(self._rotate_selected_image)

        right_layout.addWidget(QLabel("Images"))
        right_layout.addWidget(self.img_list)
        right_layout.addLayout(img_btns)

        # Histories
        self.revision_view = QTextEdit()
        self.revision_view.setReadOnly(True)
        self.change_view = QTextEdit()
        self.change_view.setReadOnly(True)
        self.image_history_view = QTextEdit()
        self.image_history_view.setReadOnly(True)
        self._reload_histories()

        right_layout.addWidget(QLabel("Revisions (notes)"))
        right_layout.addWidget(self.revision_view)
        right_layout.addWidget(QLabel("Field Changes"))
        right_layout.addWidget(self.change_view)
        right_layout.addWidget(QLabel("Image History"))
        right_layout.addWidget(self.image_history_view)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([600, 600])

        # Save/Cancel
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def _reload_images(self):
        self.img_list.clear()
        for img_path in self.db.get_images(self.item_id):
            if img_path and os.path.exists(img_path):
                pixmap = QPixmap(img_path).scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                item_widget = QListWidgetItem()
                item_widget.setIcon(QIcon(pixmap))
                item_widget.setToolTip(img_path)
                self.img_list.addItem(item_widget)

    def _reload_histories(self):
        # Revisions
        revs = self.db.get_revision_history(self.item_id)
        self.revision_view.setPlainText(
            "\n".join([f"{t}: notes='{n}'" for (n, t) in revs])
        )
        # Field changes
        changes = self.db.get_item_changes(self.item_id)
        self.change_view.setPlainText(
            "\n".join([f"{t}: {f} — '{ov}' -> '{nv}'" for (f, ov, nv, t) in changes])
        )
        # Image history if table exists
        try:
            c = self.db.conn.cursor()
            c.execute(
                "SELECT image_path, action, meta, timestamp FROM image_history WHERE item_id=? ORDER BY timestamp DESC",
                (self.item_id,),
            )
            rows = c.fetchall()
        except Exception:
            rows = []
        self.image_history_view.setPlainText(
            "\n".join([f"{t}: {action} {os.path.basename(path)} {meta}" for (path, action, meta, t) in rows])
        )

    def _add_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Add Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.db.add_image(self.item_id, file_path)
            self.db.record_image_action(self.item_id, file_path, "add")
            self._reload_images()
            self._reload_histories()

    def _remove_selected_image(self):
        row = self.img_list.currentRow()
        if row < 0:
            return
        images = self.db.get_images(self.item_id)
        if 0 <= row < len(images):
            img_path = images[row]
            c = self.db.conn.cursor()
            c.execute("DELETE FROM images WHERE item_id=? AND image_path=?", (self.item_id, img_path))
            self.db.conn.commit()
            self.db.record_image_action(self.item_id, img_path, "remove")
            self._reload_images()
            self._reload_histories()

    def _rotate_selected_image(self):
        row = self.img_list.currentRow()
        if row < 0:
            return
        images = self.db.get_images(self.item_id)
        if 0 <= row < len(images):
            img_path = images[row]
            if img_path and os.path.exists(img_path):
                try:
                    from PIL import Image
                    im = Image.open(img_path)
                    im = im.rotate(90, expand=True)
                    im.save(img_path)
                    self.db.record_image_action(self.item_id, img_path, "rotate", meta="90")
                    self._reload_images()
                    self._reload_histories()
                except Exception as e:
                    print(f"[ERROR] Could not rotate image: {e}")

    def _save(self):
        # Compare and update fields with change logging
        c = self.db.conn.cursor()
        current = self.db.get_item(self.item_id) or {}
        updates = {
            'title': self.title_edit.text(),
            'brand': self.brand_edit.text(),
            'maker': self.maker_edit.text(),
            'description': self.description_edit.toPlainText(),
            'condition': self.condition_edit.text(),
            'provenance_notes': self.provenance_notes_edit.toPlainText(),
            'notes': self.notes_edit.toPlainText(),
            'prc_low': self.prc_low_edit.text().strip(),
            'prc_med': self.prc_med_edit.text().strip(),
            'prc_hi': self.prc_hi_edit.text().strip(),
        }
        # Normalize number fields
        def _to_num(s):
            if s is None or s == '':
                return None
            try:
                return float(str(s).replace(',', ''))
            except Exception:
                return None
        num_updates = {
            'prc_low': _to_num(updates['prc_low']),
            'prc_med': _to_num(updates['prc_med']),
            'prc_hi': _to_num(updates['prc_hi']),
        }
        # Change logging
        for field, new_val in {**updates, **num_updates}.items():
            old_val = current.get(field, '')
            if (old_val or '') != (new_val or ''):
                try:
                    self.db.record_change(self.item_id, field, old_val, new_val)
                except Exception:
                    pass
        # Persist
        c.execute(
            """
            UPDATE items SET title=?, brand=?, maker=?, description=?, condition=?, provenance_notes=?, notes=?,
                            prc_low=?, prc_med=?, prc_hi=?
            WHERE id=?
            """,
            (
                updates['title'], updates['brand'], updates['maker'], updates['description'],
                updates['condition'], updates['provenance_notes'], updates['notes'],
                num_updates['prc_low'], num_updates['prc_med'], num_updates['prc_hi'],
                self.item_id,
            ),
        )
        self.db.conn.commit()
        # Record a revision entry for notes-only snapshot
        self.db.add_revision(self.item_id, updates['notes'])
        self.accept()

    # Quick save shortcut (Ctrl+S)
    def keyPressEvent(self, event):
        try:
            if event.modifiers() & Qt.ControlModifier and event.key() == ord('S'):
                self._save()
                return
        except Exception:
            pass
        super().keyPressEvent(event)
