"""
CatalogPage: Browse, sort, and preview images for all items.
"""
import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLabel,
    QFormLayout,
    QHeaderView,
    QSplitter,
    QMenu,
    QAbstractItemView,
    QScrollArea,
    QGridLayout,
    QStyleOptionHeader,
    QStyle,
)
from PyQt5.QtGui import QPixmap, QPainter, QPolygon, QColor
from PyQt5.QtCore import Qt, QPoint
from db import DB
from .edit_item_dialog import EditItemDialog
from .edit_image_dialog import EditImageDialog
from .utils import run_in_thread


class _MultiSortHeader(QHeaderView):
    """Custom header that supports multi-column sorting with visual indicators."""
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        # Disable built-in sorting - we'll handle it ourselves
        self.setSortIndicatorShown(False)
        
        # Multi-sort state: list of (column, order) tuples in priority order
        self._sort_criteria = []  # [(col, order), (col, order), ...]
        
        # Store original header texts without arrows
        self._original_headers = {}
        
        # Connect to header clicks for multi-sort logic
        self.sectionClicked.connect(self._on_section_clicked)

    def _on_section_clicked(self, section: int):
        """Handle header clicks for multi-sort behavior."""
        try:
            from PyQt5.QtWidgets import QApplication
            modifiers = QApplication.keyboardModifiers()
            
            # Check if Ctrl/Cmd is held for multi-sort
            ctrl_held = bool(modifiers & Qt.ControlModifier)
            
            if ctrl_held:
                # Multi-sort mode: add/modify/remove from sort criteria
                self._handle_multi_sort(section)
            else:
                # Single sort mode: replace all criteria with this column
                self._handle_single_sort(section)
            
            self._update_header_text()
            
            # Notify parent to re-sort the data
            if hasattr(self.parent(), '_apply_multi_sort'):
                self.parent()._apply_multi_sort(self._sort_criteria)
                
        except Exception as e:
            print(f"[MultiSortHeader] Error in section click: {e}")

    def _handle_single_sort(self, section: int):
        """Handle single-column sort (clear all others)."""
        # Find current order for this column, or default to ascending
        current_order = Qt.AscendingOrder
        
        # If this column is already the primary sort, toggle its order
        if self._sort_criteria and self._sort_criteria[0][0] == section:
            current_order = Qt.DescendingOrder if self._sort_criteria[0][1] == Qt.AscendingOrder else Qt.AscendingOrder
        
        # Replace all criteria with this single column
        self._sort_criteria = [(section, current_order)]
        print(f"[MultiSortHeader] Single sort: column {section}, order {current_order}")

    def _handle_multi_sort(self, section: int):
        """Handle multi-column sort (Ctrl+click behavior)."""
        # Check if this column is already in the criteria
        existing_index = None
        for i, (col, order) in enumerate(self._sort_criteria):
            if col == section:
                existing_index = i
                break
        
        if existing_index is not None:
            # Column exists - cycle through: asc -> desc -> remove
            current_order = self._sort_criteria[existing_index][1]
            if current_order == Qt.AscendingOrder:
                # Change to descending
                self._sort_criteria[existing_index] = (section, Qt.DescendingOrder)
                print(f"[MultiSortHeader] Changed column {section} to descending")
            else:
                # Remove from criteria
                self._sort_criteria.pop(existing_index)
                print(f"[MultiSortHeader] Removed column {section} from sort criteria")
        else:
            # New column - add as ascending at the end
            self._sort_criteria.append((section, Qt.AscendingOrder))
            print(f"[MultiSortHeader] Added column {section} as ascending")

    def _update_header_text(self):
        """Update header text to show multi-sort indicators."""
        try:
            model = self.model()
            if not model:
                return
                
            # First, restore all headers to original text
            for col in range(model.columnCount()):
                original_text = self._original_headers.get(col, "")
                if original_text:
                    model.setHeaderData(col, Qt.Horizontal, original_text, Qt.DisplayRole)
            
            # Add indicators for each sorted column
            for priority, (section, order) in enumerate(self._sort_criteria):
                original_text = self._original_headers.get(section, "")
                if original_text:
                    # Choose arrow and priority number
                    arrow = "▲" if order == Qt.AscendingOrder else "▼"
                    priority_num = f"{priority + 1}" if len(self._sort_criteria) > 1 else ""
                    
                    # Format: "1▲ Title" or "▲ Title" for single sort
                    prefix = f"{priority_num}{arrow} " if priority_num else f"{arrow} "
                    new_text = prefix + original_text
                    
                    model.setHeaderData(section, Qt.Horizontal, new_text, Qt.DisplayRole)
                    print(f"[MultiSortHeader] Updated header {section}: '{new_text}'")
                    
        except Exception as e:
            print(f"[MultiSortHeader] Error updating header text: {e}")

    def store_original_headers(self, headers):
        """Store the original header texts before we modify them."""
        self._original_headers = {i: headers[i] for i in range(len(headers))}
        print(f"[MultiSortHeader] Stored original headers: {self._original_headers}")

    def set_sort_criteria(self, criteria):
        """Manually set sort criteria and update display."""
        self._sort_criteria = criteria[:]  # Copy the list
        self._update_header_text()

    def get_sort_criteria(self):
        """Get current sort criteria."""
        return self._sort_criteria[:]

    def clear_sort(self):
        """Clear all sort criteria."""
        self._sort_criteria = []
        self._update_header_text()


class CatalogPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.current_row = 0
        # Multi-sort state
        self._sort_criteria = [(1, Qt.AscendingOrder)]  # Default sort by Title column ascending
        # Image preview (scrollable grid)
        self.img_scroll = None
        self.img_container = None
        self.img_grid = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        
        # Add instruction label for multi-sort
        instruction_label = QLabel("💡 Click column headers to sort. Hold Ctrl+Click to add multiple sort criteria.")
        instruction_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        main_layout.addWidget(instruction_label)
        
        self.splitter = QSplitter(Qt.Vertical)

        # Table (top)
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        
        # Define headers
        header_labels = [
            "ID",
            "Title", 
            "Brand",
            "Maker",
            "Description",
            "Condition",
            "Provenance Notes",
            "Notes",
            "Price Low",
            "Price Med", 
            "Price High",
            "Image Path",
            "Created At",
        ]
        
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.setSelectionBehavior(self.table.SelectRows)
        self.table.setSelectionMode(self.table.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Disable built-in sorting - we'll handle multi-sort ourselves
        self.table.setSortingEnabled(False)
        self.table.setAlternatingRowColors(True)

        # Install custom header for multi-sort display
        header = _MultiSortHeader(Qt.Horizontal, self.table)
        self.table.setHorizontalHeader(header)
        
        # Store original header texts before we modify them
        header.store_original_headers(header_labels)
        
        header.setSectionsMovable(True)  # drag & drop to reorder columns
        header.setSectionsClickable(True)
        # Built-in sorting is disabled, we handle multi-sort ourselves
        header.setSortIndicatorShown(False)
        header.setSectionResizeMode(QHeaderView.Interactive)  # allow resizing by user
        header.setStretchLastSection(False)
        
        # Initialize with default sort criteria
        print(f"[CatalogPage] Setting initial sort criteria: {self._sort_criteria}")
        header.set_sort_criteria(self._sort_criteria)
        
        # Remove padding since we're not using painted arrows anymore
        try:
            header.setStyleSheet("QHeaderView::up-arrow, QHeaderView::down-arrow { image: none; width: 0px; height: 0px; }")
        except Exception:
            pass
        # Ensure built-in arrows are fully hidden regardless of style
        try:
            header.setStyleSheet(
                "QHeaderView::up-arrow, QHeaderView::down-arrow { image: none; width: 0px; height: 0px; }"
                " QHeaderView::section { padding-left: 28px; }"
            )
        except Exception:
            pass
        # Capture default widths for per-column reset
        try:
            self._default_section_sizes = [header.sectionSize(i) for i in range(self.table.columnCount())]
        except Exception:
            self._default_section_sizes = []
        # Multi-sort functionality is handled in the header itself
        # Header context menu + double-click autosize
        header.setContextMenuPolicy(Qt.CustomContextMenu)
        header.customContextMenuRequested.connect(self._on_header_menu)
        try:
            header.sectionDoubleClicked.connect(self._on_header_double_clicked)
        except Exception:
            pass
        # Capture default header state to enable "Reset columns"
        try:
            self._default_header_state = header.saveState()
        except Exception:
            self._default_header_state = None

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.itemSelectionChanged.connect(self.show_details)
        # Also update preview when the current cell changes (e.g., via keyboard)
        try:
            self.table.currentCellChanged.connect(lambda *_: self.show_details())
        except Exception:
            pass
        # Also update preview on any cell click
        try:
            self.table.cellClicked.connect(lambda _r, _c: self.show_details())
        except Exception:
            pass
        self.splitter.addWidget(self.table)

        # Detail/preview panel (bottom)
        self.detail_widget = QWidget()
        self.detail_widget.setObjectName("detailpanel")
        self.detail_layout = QFormLayout()
        self.detail_widget.setLayout(self.detail_layout)
        self.img_scroll = QScrollArea()
        self.img_scroll.setWidgetResizable(True)
        self.img_container = QWidget()
        self.img_grid = QGridLayout(self.img_container)
        self.img_grid.setContentsMargins(0, 0, 0, 0)
        self.img_container.setLayout(self.img_grid)
        self.img_scroll.setWidget(self.img_container)
        self.detail_layout.addRow(QLabel("Images:"), self.img_scroll)
        self.splitter.addWidget(self.detail_widget)
        self.splitter.setSizes([500, 300])

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)

    # --- Row/selection helpers ---
    def _selected_item_id(self):
        try:
            row = self.table.currentRow()
            if row < 0:
                return None
            cell = self.table.item(row, 0)
            if not cell:
                return None
            return int(cell.text())
        except Exception:
            return None

    def _select_row_by_id(self, item_id: int):
        try:
            for r in range(self.table.rowCount()):
                it = self.table.item(r, 0)
                if it and it.text() == str(item_id):
                    self.table.selectRow(r)
                    return
        except Exception:
            pass

    def _apply_multi_sort(self, sort_criteria):
        """Apply multi-column sorting to the table data."""
        try:
            if not sort_criteria:
                print("[CatalogPage] No sort criteria provided")
                return
            
            print(f"[CatalogPage] Applying multi-sort with criteria: {sort_criteria}")
            
            # Get all table rows as tuples of (row_index, values)
            rows_data = []
            for row in range(self.table.rowCount()):
                row_values = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    value = item.text() if item else ""
                    row_values.append(value)
                rows_data.append((row, row_values))
            
            # Sort using multiple criteria
            def multi_sort_key(row_data):
                _, values = row_data
                sort_keys = []
                
                for col_index, sort_order in sort_criteria:
                    if col_index < len(values):
                        value = values[col_index]
                        
                        # Try to convert to appropriate type for sorting
                        sort_value = self._convert_sort_value(value, col_index)
                        
                        # Reverse for descending order
                        if sort_order == Qt.DescendingOrder:
                            if isinstance(sort_value, str):
                                sort_value = sort_value.lower()  # Case-insensitive
                                sort_keys.append((False, sort_value))  # False sorts before True
                            else:
                                sort_keys.append(-sort_value if isinstance(sort_value, (int, float)) else sort_value)
                        else:
                            if isinstance(sort_value, str):
                                sort_value = sort_value.lower()  # Case-insensitive  
                            sort_keys.append(sort_value)
                    else:
                        sort_keys.append("")  # Default for missing columns
                
                return sort_keys
            
            # Sort the data
            sorted_rows = sorted(rows_data, key=multi_sort_key)
            
            # Rearrange table rows according to sorted order
            self._rearrange_table_rows(sorted_rows)
            
            # Update the sort criteria state
            self._sort_criteria = sort_criteria[:]
            
            # Refresh preview for currently selected row
            self.show_details()
            
        except Exception as e:
            print(f"[CatalogPage] Error in multi-sort: {e}")
            import traceback
            traceback.print_exc()

    def _convert_sort_value(self, value: str, col_index: int):
        """Convert string value to appropriate type for sorting."""
        try:
            # Price columns (8, 9, 10) should be sorted as numbers
            if col_index in [0, 8, 9, 10]:  # ID, Price Low, Price Med, Price High
                try:
                    return float(value) if value else 0.0
                except ValueError:
                    return 0.0
            
            # Date column (12) - basic string sort should work for ISO dates
            elif col_index == 12:  # Created At
                return value if value else ""
            
            # All other columns sort as strings (case-insensitive)
            else:
                return value.lower() if value else ""
                
        except Exception:
            return value if value else ""

    def _rearrange_table_rows(self, sorted_rows):
        """Rearrange table rows according to the sorted order."""
        try:
            # Remember current selection
            current_id = self._selected_item_id()
            
            # Temporarily disable sorting to avoid conflicts
            self.table.setSortingEnabled(False)
            
            # Create new table content
            new_table_data = []
            for sort_index, (original_row_index, row_values) in enumerate(sorted_rows):
                new_table_data.append(row_values)
            
            # Clear and repopulate table
            self.table.setRowCount(0)
            self.table.setRowCount(len(new_table_data))
            
            for row, row_values in enumerate(new_table_data):
                for col, value in enumerate(row_values):
                    self.table.setItem(row, col, QTableWidgetItem(value))
            
            # Restore selection by ID if possible
            if current_id:
                self._select_row_by_id(current_id)
            elif new_table_data:
                self.table.selectRow(0)
                
        except Exception as e:
            print(f"[CatalogPage] Error rearranging table rows: {e}")
            import traceback
            traceback.print_exc()

    def _on_header_double_clicked(self, logical_index: int):
        # Auto-fit the double-clicked column to contents
        if logical_index is None or logical_index < 0:
            return
        try:
            self.table.resizeColumnToContents(logical_index)
        except Exception:
            pass

    def _on_header_menu(self, pos):
        # Context menu on header to fit/reset columns and manage multi-sort
        header = self.table.horizontalHeader()
        try:
            col = header.logicalIndexAt(pos)
        except Exception:
            col = -1
        menu = QMenu(self)
        
        # Column sizing actions
        act_fit_col = menu.addAction("Fit This Column")
        act_reset_col = menu.addAction("Reset This Column")
        act_fit_all = menu.addAction("Fit All Columns")
        act_reset = menu.addAction("Reset Columns")
        
        # Multi-sort actions
        menu.addSeparator()
        act_clear_sort = menu.addAction("Clear All Sorting")
        
        # Show current sort criteria
        if hasattr(header, 'get_sort_criteria'):
            criteria = header.get_sort_criteria()
            if criteria:
                menu.addSeparator()
                sort_info = menu.addAction(f"Current: {len(criteria)} sort criteria")
                sort_info.setEnabled(False)  # Just for display
        
        # Debug actions
        menu.addSeparator()
        act_debug_info = menu.addAction("Debug Info")
        
        action = menu.exec_(header.mapToGlobal(pos))
        if action == act_fit_col and col >= 0:
            try:
                self.table.resizeColumnToContents(col)
            except Exception:
                pass
        elif action == act_reset_col and col >= 0:
            try:
                default_w = None
                if hasattr(self, '_default_section_sizes') and self._default_section_sizes and col < len(self._default_section_sizes):
                    default_w = int(self._default_section_sizes[col])
                if default_w and default_w > 0:
                    header.resizeSection(col, default_w)
                else:
                    self.table.resizeColumnToContents(col)
            except Exception:
                pass
        elif action == act_fit_all:
            try:
                for i in range(self.table.columnCount()):
                    self.table.resizeColumnToContents(i)
            except Exception:
                pass
        elif action == act_reset:
            try:
                if getattr(self, '_default_header_state', None):
                    header.restoreState(self._default_header_state)
                # Ensure interactive resize and multi-sort remain enabled
                header.setSectionResizeMode(QHeaderView.Interactive)
                header.setSectionsMovable(True)
                header.setSectionsClickable(True)
                header.setSortIndicatorShown(False)  # We handle our own indicators
            except Exception:
                pass
        elif action == act_clear_sort:
            # Clear all sort criteria
            try:
                if hasattr(header, 'clear_sort'):
                    header.clear_sort()
                    self._sort_criteria = []
                    print("[CatalogPage] Cleared all sort criteria")
                    # Refresh without sorting to show original order
                    self.refresh()
            except Exception as e:
                print(f"[CatalogPage] Error clearing sort: {e}")
        elif action == act_debug_info:
            # Debug: show current multi-sort state
            try:
                from PyQt5.QtWidgets import QMessageBox
                if hasattr(header, 'get_sort_criteria'):
                    criteria = header.get_sort_criteria()
                    criteria_str = ", ".join([f"Col{col}:{('Asc' if order==Qt.AscendingOrder else 'Desc')}" for col, order in criteria])
                else:
                    criteria_str = "N/A"
                    
                info = f"""Multi-Sort Debug Info:
Sort Criteria: {criteria_str}
Criteria Count: {len(self._sort_criteria)}
Original Headers: {getattr(header, '_original_headers', 'N/A')}"""
                QMessageBox.information(self, "Multi-Sort Debug", info)
            except Exception as e:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Debug Error", str(e))

    # Context menu
    def open_context_menu(self, pos):
        menu = QMenu(self)
        edit_action = menu.addAction("Edit (Popup)")
        reevaluate_action = menu.addAction("Re-evaluate (AI)")
        action = menu.exec_(self.table.viewport().mapToGlobal(pos))
        if action == edit_action:
            # Invoke edit for selected ID
            item_id = self._selected_item_id()
            if item_id is not None:
                self.open_edit_dialog_by_id(item_id)
        elif action == reevaluate_action:
            self.reevaluate_selected()

    def reevaluate_selected(self):
        from PyQt5.QtWidgets import QMessageBox
        # Identify selected item
        item_id = self._selected_item_id()
        if not item_id:
            QMessageBox.warning(self, "Re-evaluate", "No item selected.")
            return
        # Prefer cached item dict; fallback to DB
        item = None
        try:
            if hasattr(self, '_items_by_id'):
                item = self._items_by_id.get(item_id)
        except Exception:
            item = None
        if not item:
            item = self.db.get_item(item_id) or {'id': item_id}

        # Collect image paths: legacy primary + images table, deduped, existing files preferred
        paths = []
        seen = set()
        legacy = item.get('image_path') or ''
        if legacy and legacy not in seen:
            seen.add(legacy)
            paths.append(legacy)
        for p in self.db.get_images(item_id) or []:
            if p and p not in seen:
                seen.add(p)
                paths.append(p)
        # Filter to existing files; keep non-existing as best-effort
        existing = [p for p in paths if os.path.exists(p)]
        if not existing and paths:
            # If none exist on disk, still try with whatever we have (may fail in client)
            existing = paths
        if not existing:
            QMessageBox.warning(self, "Re-evaluate", "This item has no images to analyze.")
            return

        # Gather per-image annotations where available
        annos = []
        for p in existing:
            try:
                ann = self.db.get_image_annotation(item_id, p) or ""
            except Exception:
                ann = ""
            annos.append(ann)

        # Run analysis in a background thread
        self.setCursor(Qt.WaitCursor)
        from openai_client import analyze_images

        # Optional: Add a tiny caption meta for better hints
        try:
            analyze_images.meta = {"captions": [os.path.basename(p) for p in existing]}
        except Exception:
            pass

        def _work():
            return analyze_images(existing, annos)

        def _on_result(result):
            try:
                self.db.update_item_analysis(item_id, result)
                QMessageBox.information(self, "Re-evaluate", "Item updated with new AI analysis.")
            except Exception as e:
                QMessageBox.warning(self, "Re-evaluate", f"Saved raw result, but failed to update fields: {e}")
        # Refresh UI and re-select the same ID
        self.refresh()
        self._select_row_by_id(item_id)

        def _on_error(e):
            QMessageBox.critical(self, "Re-evaluate", f"AI error: {e}")

        def _on_finished():
            self.unsetCursor()

        run_in_thread(_work, on_result=_on_result, on_error=_on_error, on_finished=_on_finished)

    def open_edit_dialog_by_id(self, item_id: int):
        if not item_id:
            return
        dlg = EditItemDialog(self, item_id)
        if dlg.exec_():
            self.refresh()
            self._select_row_by_id(item_id)

    def refresh(self):
        # Remember current selection and sort state
        current_id = self._selected_item_id()
        header = self.table.horizontalHeader()
        
        # Get current sort criteria from header or use defaults
        if hasattr(header, 'get_sort_criteria'):
            current_sort_criteria = header.get_sort_criteria()
        else:
            current_sort_criteria = self._sort_criteria
        
        # Load fresh data from database
        self.items = self.db.get_all_items()
        # Fast lookup by ID for current page state
        try:
            self._items_by_id = {it['id']: it for it in self.items}
        except Exception:
            self._items_by_id = {}
        
        # Populate table with raw data (unsorted)
        self.table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            low, med, high = self.db.get_price_range(item["id"])
            self.table.setItem(row, 0, QTableWidgetItem(str(item["id"])) )
            self.table.setItem(row, 1, QTableWidgetItem(item.get("title", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("brand", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("maker", "")))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("description", "")))
            self.table.setItem(row, 5, QTableWidgetItem(item.get("condition", "")))
            self.table.setItem(row, 6, QTableWidgetItem(item.get("provenance_notes", "")))
            self.table.setItem(row, 7, QTableWidgetItem(item.get("notes", "")))
            self.table.setItem(row, 8, QTableWidgetItem(str(low)))
            self.table.setItem(row, 9, QTableWidgetItem(str(med)))
            self.table.setItem(row, 10, QTableWidgetItem(str(high)))
            self.table.setItem(row, 11, QTableWidgetItem(item.get("image_path", "")))
            self.table.setItem(row, 12, QTableWidgetItem(item.get("created_at", "")))
        
        # Apply multi-sort if we have criteria
        if current_sort_criteria:
            print(f"[CatalogPage] Refresh: Applying sort criteria {current_sort_criteria}")
            self._apply_multi_sort(current_sort_criteria)
            # Update header display
            if hasattr(header, 'set_sort_criteria'):
                header.set_sort_criteria(current_sort_criteria)
        
        # Restore selection by ID if possible
        if current_id:
            self._select_row_by_id(current_id)
        elif self.items:
            self.table.selectRow(0)
            
        # Ensure header remains interactive
        try:
            header.setSectionResizeMode(QHeaderView.Interactive)
            header.setSectionsMovable(True)
            header.setSectionsClickable(True)
            header.setSortIndicatorShown(False)  # We handle our own indicators
        except Exception:
            pass
            
        self.show_details()

    def show_details(self):
        if not hasattr(self, 'items') or not self.items:
            self._populate_image_thumbs(None)
            return
        item_id = self._selected_item_id()
        if not item_id:
            self._populate_image_thumbs(None)
            return
        # Use cached row dict if available
        item = None
        try:
            if hasattr(self, '_items_by_id'):
                item = self._items_by_id.get(item_id)
        except Exception:
            item = None
        if not item:
            item = self.db.get_item(item_id)
        self._populate_image_thumbs(item)

    def _populate_image_thumbs(self, item):
        # Clear current thumbnails
        while self.img_grid.count():
            it = self.img_grid.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        if not item:
            return
        # Build ordered, deduped list of paths
        db_images = self.db.get_images(item['id']) or []
        legacy = item.get('image_path') or ''
        ordered = ([legacy] if legacy else []) + db_images
        seen, paths = set(), []
        for p in ordered:
            if p and p not in seen:
                seen.add(p)
                paths.append(p)
        # Populate grid
        cols, r, c = 6, 0, 0
        for p in paths:
            pix = QPixmap(p)
            if pix.isNull():
                continue

            # Card container with image and optional annotation text
            card = QWidget()
            from PyQt5.QtWidgets import QVBoxLayout
            vbox = QVBoxLayout(card)
            vbox.setContentsMargins(4, 4, 4, 4)
            vbox.setSpacing(4)

            img_lbl = QLabel()
            img_lbl.setFixedSize(96, 96)
            img_lbl.setAlignment(Qt.AlignCenter)
            img_lbl.setToolTip(p)
            img_lbl.setPixmap(pix.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            vbox.addWidget(img_lbl, 0, Qt.AlignHCenter)

            # Annotation text (if any)
            ann_text = ""
            try:
                ann_text = self.db.get_image_annotation(item['id'], p) or ""
            except Exception:
                ann_text = ""
            if ann_text.strip():
                ann_lbl = QLabel(ann_text)
                ann_lbl.setWordWrap(True)
                ann_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
                ann_lbl.setFixedWidth(96)
                ann_lbl.setStyleSheet("color: #666; font-size: 10px;")
                vbox.addWidget(ann_lbl, 0, Qt.AlignHCenter)

            # Context menu for image/card
            def make_menu(widget: QWidget, path: str):
                def _on_menu(pos):
                    from PyQt5.QtWidgets import QMenu, QFileDialog, QMessageBox
                    menu = QMenu(self)
                    act_edit = menu.addAction("Edit…")
                    act_replace = menu.addAction("Replace…")
                    act_delete = menu.addAction("Delete")
                    action = menu.exec_(widget.mapToGlobal(pos))
                    if action == act_edit:
                        # Load existing per-image annotation if any
                        ann = ""
                        try:
                            ann = self.db.get_image_annotation(item['id'], path) or ""
                        except Exception:
                            ann = ""
                        dlg = EditImageDialog(self, path, ann)
                        if dlg.exec_():
                            _lbl, new_text = dlg.get_values()
                            try:
                                # Persist per-image annotation
                                self.db.update_image_annotation(item['id'], path, new_text)
                                # Also leave a revision breadcrumb
                                self.db.add_revision(item['id'], f"Updated image annotation for {os.path.basename(path)}")
                            except Exception:
                                pass
                    elif action == act_replace:
                        new_path, _ = QFileDialog.getOpenFileName(self, "Choose Replacement Image", os.path.dirname(path), "Images (*.png *.jpg *.jpeg *.bmp)")
                        if new_path:
                            try:
                                # Update path via DB helper
                                self.db.replace_image_path(item['id'], path, new_path)
                            except Exception:
                                # Fallback: add new image and remove old
                                try:
                                    self.db.add_image(item['id'], new_path)
                                    self.db.delete_image_path(item['id'], path)
                                except Exception:
                                    pass
                            self.refresh()
                    elif action == act_delete:
                        try:
                            from PyQt5.QtWidgets import QMessageBox
                            if QMessageBox.question(self, "Delete Image", f"Remove this image from item #{item['id']}?") == QMessageBox.Yes:
                                self.db.delete_image_path(item['id'], path)
                                self.refresh()
                        except Exception:
                            pass
                return _on_menu

            handler = make_menu(card, p)
            img_lbl.setContextMenuPolicy(Qt.CustomContextMenu)
            img_lbl.customContextMenuRequested.connect(handler)
            card.setContextMenuPolicy(Qt.CustomContextMenu)
            card.customContextMenuRequested.connect(handler)

            self.img_grid.addWidget(card, r, c)
            c += 1
            if c >= cols:
                c = 0
                r += 1

    # --- UI state persistence helpers ---
    def get_splitter_sizes(self):
        try:
            return self.splitter.sizes()
        except Exception:
            return []

    def set_splitter_sizes(self, sizes):
        try:
            sizes = [int(s) for s in sizes] if sizes else None
            if sizes:
                self.splitter.setSizes(sizes)
        except Exception:
            pass

    def get_table_header_state(self):
        try:
            return self.table.horizontalHeader().saveState()
        except Exception:
            return None

    def set_table_header_state(self, state):
        try:
            if state:
                header = self.table.horizontalHeader()
                header.restoreState(state)
                # Re-assert interactive and movable behaviors in case the saved state disabled them
                header.setSectionResizeMode(QHeaderView.Interactive)
                header.setSectionsMovable(True)
                header.setSectionsClickable(True)
                # Keep built-in indicator hidden; custom painter draws arrow
                header.setSortIndicatorShown(False)
                header.setStyleSheet(
                    "QHeaderView::up-arrow, QHeaderView::down-arrow { image: none; width: 0px; height: 0px; }"
                    " QHeaderView::section { padding-left: 28px; }"
                )
                self.table.setSortingEnabled(True)
                try:
                    header._active_sort_section = header.sortIndicatorSection()
                    header._active_sort_order = header.sortIndicatorOrder()
                    header.update()
                except Exception:
                    pass
        except Exception:
            pass

    # Multi-sort functionality - old single-sort method no longer needed

