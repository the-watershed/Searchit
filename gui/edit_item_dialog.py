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
    QTabWidget,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QScrollArea,
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

        # Left: tabbed edit form for better organization
        left = QWidget()
        left_layout = QVBoxLayout(left)
        
        # Create tab widget for organizing fields
        tabs = QTabWidget()
        
        # Basic Information Tab
        basic_tab = QWidget()
        basic_form = QFormLayout(basic_tab)
        
        self.title_edit = QLineEdit(self.item.get('title', ''))
        self.brand_edit = QLineEdit(self.item.get('brand', ''))
        self.maker_edit = QLineEdit(self.item.get('maker', ''))
        self.description_edit = QTextEdit(self.item.get('description', ''))
        self.description_edit.setMaximumHeight(80)
        
        basic_form.addRow(QLabel("Title:"), self.title_edit)
        basic_form.addRow(QLabel("Brand:"), self.brand_edit)
        basic_form.addRow(QLabel("Maker:"), self.maker_edit)
        basic_form.addRow(QLabel("Description:"), self.description_edit)
        
        tabs.addTab(basic_tab, "Basic Info")
        
        # Catalog Details Tab
        catalog_tab = QWidget()
        catalog_form = QFormLayout(catalog_tab)
        
        # Create scroll area for catalog form
        catalog_scroll = QScrollArea()
        catalog_scroll.setWidgetResizable(True)
        catalog_scroll_widget = QWidget()
        catalog_scroll_layout = QFormLayout(catalog_scroll_widget)
        
        self.category_edit = QLineEdit(self.item.get('category', ''))
        self.subcategory_edit = QLineEdit(self.item.get('subcategory', ''))
        self.era_period_edit = QLineEdit(self.item.get('era_period', ''))
        self.material_edit = QLineEdit(self.item.get('material', ''))
        self.dimensions_edit = QLineEdit(self.item.get('dimensions', ''))
        self.weight_edit = QLineEdit(self.item.get('weight', ''))
        self.color_scheme_edit = QLineEdit(self.item.get('color_scheme', ''))
        
        # Rarity dropdown
        self.rarity_combo = QComboBox()
        rarity_options = ["", "Common", "Uncommon", "Rare", "Very Rare", "Unique"]
        self.rarity_combo.addItems(rarity_options)
        current_rarity = self.item.get('rarity', '')
        if current_rarity in rarity_options:
            self.rarity_combo.setCurrentText(current_rarity)
        
        # Authentication dropdown
        self.auth_combo = QComboBox()
        auth_options = ["", "Authenticated", "Certificate of Authenticity", "Unsigned", "Questionable"]
        self.auth_combo.addItems(auth_options)
        current_auth = self.item.get('authentication', '')
        if current_auth in auth_options:
            self.auth_combo.setCurrentText(current_auth)
        
        # Condition dropdown
        self.condition_combo = QComboBox()
        condition_options = ["", "Mint", "Near Mint", "Excellent", "Very Good", "Good", "Fair", "Poor"]
        self.condition_combo.addItems(condition_options)
        current_condition = self.item.get('condition', '')
        if current_condition in condition_options:
            self.condition_combo.setCurrentText(current_condition)
        else:
            self.condition_combo.setCurrentText("")
        
        # Status dropdown
        self.status_combo = QComboBox()
        status_options = ["Available", "Sold", "On Hold", "Damaged", "Under Restoration", "Reserved"]
        self.status_combo.addItems(status_options)
        current_status = self.item.get('status', 'Available')
        if current_status in status_options:
            self.status_combo.setCurrentText(current_status)
        
        self.location_edit = QLineEdit(self.item.get('location_stored', ''))
        self.tags_edit = QLineEdit(self.item.get('tags', ''))
        
        # Checkboxes
        self.public_display_check = QCheckBox()
        self.public_display_check.setChecked(bool(self.item.get('public_display', True)))
        self.featured_item_check = QCheckBox()
        self.featured_item_check.setChecked(bool(self.item.get('featured_item', False)))
        
        catalog_scroll_layout.addRow(QLabel("Category:"), self.category_edit)
        catalog_scroll_layout.addRow(QLabel("Subcategory:"), self.subcategory_edit)
        catalog_scroll_layout.addRow(QLabel("Era/Period:"), self.era_period_edit)
        catalog_scroll_layout.addRow(QLabel("Material:"), self.material_edit)
        catalog_scroll_layout.addRow(QLabel("Dimensions:"), self.dimensions_edit)
        catalog_scroll_layout.addRow(QLabel("Weight:"), self.weight_edit)
        catalog_scroll_layout.addRow(QLabel("Color Scheme:"), self.color_scheme_edit)
        catalog_scroll_layout.addRow(QLabel("Rarity:"), self.rarity_combo)
        catalog_scroll_layout.addRow(QLabel("Authentication:"), self.auth_combo)
        catalog_scroll_layout.addRow(QLabel("Condition:"), self.condition_combo)
        catalog_scroll_layout.addRow(QLabel("Status:"), self.status_combo)
        catalog_scroll_layout.addRow(QLabel("Location:"), self.location_edit)
        catalog_scroll_layout.addRow(QLabel("Tags:"), self.tags_edit)
        catalog_scroll_layout.addRow(QLabel("Public Display:"), self.public_display_check)
        catalog_scroll_layout.addRow(QLabel("Featured Item:"), self.featured_item_check)
        
        catalog_scroll.setWidget(catalog_scroll_widget)
        catalog_form.addRow(catalog_scroll)
        tabs.addTab(catalog_tab, "Catalog Details")
        
        # Financial Tab
        financial_tab = QWidget()
        financial_form = QFormLayout(financial_tab)
        
        # Price range fields (editable)
        pr_low = self.item.get('prc_low')
        pr_med = self.item.get('prc_med')
        pr_hi = self.item.get('prc_hi')
        if pr_low in (None, '') and pr_med in (None, '') and pr_hi in (None, ''):
            pr_low, pr_med, pr_hi = self.db.get_price_range(self.item_id)
        
        self.prc_low_edit = QDoubleSpinBox()
        self.prc_low_edit.setMaximum(999999.99)
        self.prc_low_edit.setValue(float(pr_low) if pr_low not in (None, '') else 0.0)
        
        self.prc_med_edit = QDoubleSpinBox()
        self.prc_med_edit.setMaximum(999999.99)
        self.prc_med_edit.setValue(float(pr_med) if pr_med not in (None, '') else 0.0)
        
        self.prc_hi_edit = QDoubleSpinBox()
        self.prc_hi_edit.setMaximum(999999.99)
        self.prc_hi_edit.setValue(float(pr_hi) if pr_hi not in (None, '') else 0.0)
        
        self.acquisition_cost_edit = QDoubleSpinBox()
        self.acquisition_cost_edit.setMaximum(999999.99)
        acq_cost = self.item.get('acquisition_cost', 0.0)
        self.acquisition_cost_edit.setValue(float(acq_cost) if acq_cost not in (None, '') else 0.0)
        
        self.insurance_value_edit = QDoubleSpinBox()
        self.insurance_value_edit.setMaximum(999999.99)
        ins_val = self.item.get('insurance_value', 0.0)
        self.insurance_value_edit.setValue(float(ins_val) if ins_val not in (None, '') else 0.0)
        
        self.acquisition_date_edit = QLineEdit(self.item.get('acquisition_date', ''))
        self.acquisition_source_edit = QLineEdit(self.item.get('acquisition_source', ''))
        
        financial_form.addRow(QLabel("Price Low:"), self.prc_low_edit)
        financial_form.addRow(QLabel("Price Med:"), self.prc_med_edit)
        financial_form.addRow(QLabel("Price High:"), self.prc_hi_edit)
        financial_form.addRow(QLabel("Acquisition Cost:"), self.acquisition_cost_edit)
        financial_form.addRow(QLabel("Insurance Value:"), self.insurance_value_edit)
        financial_form.addRow(QLabel("Acquisition Date:"), self.acquisition_date_edit)
        financial_form.addRow(QLabel("Acquisition Source:"), self.acquisition_source_edit)
        
        tabs.addTab(financial_tab, "Financial")
        
        # Notes Tab
        notes_tab = QWidget()
        notes_form = QFormLayout(notes_tab)
        
        self.provenance_notes_edit = QTextEdit(self.item.get('provenance_notes', ''))
        self.notes_edit = QTextEdit(self.item.get('notes', ''))
        
        notes_form.addRow(QLabel("Provenance Notes:"), self.provenance_notes_edit)
        notes_form.addRow(QLabel("General Notes:"), self.notes_edit)
        
        tabs.addTab(notes_tab, "Notes")
        
        left_layout.addWidget(tabs)
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self._save_changes)
        left_layout.addWidget(save_btn)
        
        splitter.addWidget(left)

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

    def _save_changes(self):
        """Save all field changes using the enhanced update method."""
        fields = {
            # Basic fields
            'title': self.title_edit.text(),
            'brand': self.brand_edit.text(),
            'maker': self.maker_edit.text(),
            'description': self.description_edit.toPlainText(),
            
            # Catalog details
            'category': self.category_edit.text(),
            'subcategory': self.subcategory_edit.text(),
            'era_period': self.era_period_edit.text(),
            'material': self.material_edit.text(),
            'dimensions': self.dimensions_edit.text(),
            'weight': self.weight_edit.text(),
            'color_scheme': self.color_scheme_edit.text(),
            'rarity': self.rarity_combo.currentText(),
            'authentication': self.auth_combo.currentText(),
            'condition': self.condition_combo.currentText(),
            'status': self.status_combo.currentText(),
            'location_stored': self.location_edit.text(),
            'tags': self.tags_edit.text(),
            'public_display': 1 if self.public_display_check.isChecked() else 0,
            'featured_item': 1 if self.featured_item_check.isChecked() else 0,
            
            # Financial fields
            'prc_low': self.prc_low_edit.value(),
            'prc_med': self.prc_med_edit.value(),
            'prc_hi': self.prc_hi_edit.value(),
            'acquisition_cost': self.acquisition_cost_edit.value(),
            'insurance_value': self.insurance_value_edit.value(),
            'acquisition_date': self.acquisition_date_edit.text(),
            'acquisition_source': self.acquisition_source_edit.text(),
            
            # Notes
            'provenance_notes': self.provenance_notes_edit.toPlainText(),
            'notes': self.notes_edit.toPlainText(),
        }
        
        # Update using enhanced method
        success = self.db.update_item_fields(self.item_id, fields)
        
        if success:
            self.accept()
        else:
            # Show error message
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Save Error", "Failed to save changes to the database.")

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
