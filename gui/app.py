"""
ProvenanceApp: Main PyQt5 Application
- Sets up main window and navigation between pages.
"""


from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QPainter, QPolygon
from PyQt5.QtCore import QSettings, QByteArray, QObject, QEvent, QTimer, Qt, QStandardPaths, QPoint
import os
import hashlib





class ProvenanceApp(QApplication):
    def set_global_theme(self, idx):
        """Set the global stylesheet for the whole app based on theme index."""
        if idx == 0:  # Neon Curio
            self.setStyleSheet(self.dashboard_page.futuristic_qss())
        elif idx == 1:  # Steampunk
            self.setStyleSheet(self.dashboard_page.steampunk_qss())
        elif idx == 2:  # Dark Carnival
            self.setStyleSheet(self.dashboard_page.carnival_qss())
    def __init__(self, argv):
        print("[DEBUG] ProvenanceApp.__init__ starting...")
        super().__init__(argv)
        self.settings = QSettings("JUREKA", "ProvenanceToyShop")
        # Do not create any widgets here!
        print("[DEBUG] ProvenanceApp.__init__ finished.")

    def setup_ui(self):
        print("[DEBUG] ProvenanceApp.setup_ui starting...")
        # Import all pages only after QApplication is constructed
        from gui.upload_page import UploadPage
        from gui.catalog_page import CatalogPage
        from gui.analytics_page import AnalyticsPage
        from gui.settings_page import SettingsPage
        from gui.about_page import AboutPage

        # Main window
        self.window = QMainWindow()
        self.window.setWindowTitle("Curio Cabinet")
        self.window.setObjectName("MainWindow")
        self.window.setToolTip(self.window.objectName())
        # Set program icon to a QR code of the Quadratic Equation
        try:
            qr_text = "x = (-b ± sqrt(b^2 - 4ac)) / (2a)"
            qr_size = 256
            cache_path = self._qr_cache_path(qr_text, qr_size)
            qr_pix = QPixmap(cache_path) if os.path.exists(cache_path) else QPixmap()
            if qr_pix.isNull():
                qr_pix = self._build_qr_icon_pixmap(qr_text, size=qr_size)
                # best-effort cache write
                try:
                    if not qr_pix.isNull():
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        qr_pix.save(cache_path, "PNG")
                except Exception:
                    pass
            if not qr_pix.isNull():
                icon = QIcon(qr_pix)
                self.setWindowIcon(icon)
                self.window.setWindowIcon(icon)
        except Exception as _e:
            # Non-fatal if QR generation fails
            pass

        # Curio shop theme: font, palette, stylesheet
        self.setFont(QFont("Garamond", 10))
        palette = QPalette()
        parchment = QColor("#f8f3e7")
        parchment_alt = QColor("#efe7d6")
        text = QColor("#3b2f2f")
        accent = QColor("#8b5e34")
        highlight = QColor("#c49a6c")
        palette.setColor(QPalette.Window, parchment)
        palette.setColor(QPalette.Base, QColor("#fffdf7"))
        palette.setColor(QPalette.AlternateBase, parchment_alt)
        palette.setColor(QPalette.WindowText, text)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, accent)
        palette.setColor(QPalette.ButtonText, QColor("#f7efe4"))
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, QColor("#2b1e1e"))
        self.setPalette(palette)
        # Build larger white sort arrow icons for header
        try:
            up_path = self._arrow_icon_cache_path("up", 16, QColor("white"))
            down_path = self._arrow_icon_cache_path("down", 16, QColor("white"))
            if not os.path.exists(up_path):
                up_pix = self._build_sort_arrow_pixmap("up", 16, QColor("white"))
                if not up_pix.isNull():
                    os.makedirs(os.path.dirname(up_path), exist_ok=True)
                    up_pix.save(up_path, "PNG")
            if not os.path.exists(down_path):
                down_pix = self._build_sort_arrow_pixmap("down", 16, QColor("white"))
                if not down_pix.isNull():
                    os.makedirs(os.path.dirname(down_path), exist_ok=True)
                    down_pix.save(down_path, "PNG")
        except Exception:
            up_path, down_path = "", ""

        up_url = up_path.replace('\\', '/') if up_path else ""
        down_url = down_path.replace('\\', '/') if down_path else ""

        stylesheet = """
            QWidget { background: #f8f3e7; color: #3b2f2f; }
            QMainWindow::separator { background: #d8c6a1; }
            QTabWidget::pane { border: 1px solid #bda77b; background: #efe7d6; }
            QTabBar::tab { background: #e9dfc8; padding: 6px 12px; border: 1px solid #bda77b; border-bottom: none; }
            QTabBar::tab:selected { background: #fffdf7; }
            QHeaderView::section { background: #d8c6a1; color: #2b1e1e; padding: 6px; padding-right: 22px; border: none; }
            /* Larger white sort indicators on the right */
            QHeaderView::up-arrow {
                width: 16px; height: 16px;
                image: url(UPURL);
            }
            QHeaderView::down-arrow {
                width: 16px; height: 16px;
                image: url(DOWNURL);
            }
            QTableView { gridline-color: #bda77b; selection-background-color: #c49a6c; selection-color: #2b1e1e; alternate-background-color: #efe7d6; }
            QToolTip { background: #fffdf7; color: #2b1e1e; border: 1px solid #bda77b; }
            QPushButton { background: #8b5e34; color: #f7efe4; border: 1px solid #6f482a; padding: 6px 10px; border-radius: 4px; }
            QPushButton:hover { background: #a66f3c; }
            QPushButton:disabled { background: #cbb79a; color: #7a6a58; }
            QLineEdit, QTextEdit { background: #fffdf7; border: 1px solid #b8996f; padding: 4px; }
            QTextEdit { border-radius: 4px; }
            QMenu { background: #fffdf7; border: 1px solid #bda77b; }
            QMenu::item:selected { background: #c49a6c; color: #2b1e1e; }
            QSplitter::handle { background: #d8c6a1; }
        """.replace("UPURL", up_url).replace("DOWNURL", down_url)
        self.setStyleSheet(stylesheet)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("MainTabs")
        self.tabs.setToolTip(self.tabs.objectName())

        print("[DEBUG] Creating UploadPage...")
        self.upload_page = UploadPage(self)
        self.upload_page.setObjectName("UploadPage")
        self.upload_page.setToolTip(self.upload_page.objectName())

        print("[DEBUG] About to create CatalogPage...")
        self.catalog_page = CatalogPage(self)
        self.catalog_page.setObjectName("CatalogPage")
        self.catalog_page.setToolTip(self.catalog_page.objectName())
        print("[DEBUG] Created CatalogPage.")

        print("[DEBUG] About to create AnalyticsPage...")
        self.analytics_page = AnalyticsPage(self)
        self.analytics_page.setObjectName("AnalyticsPage")
        self.analytics_page.setToolTip(self.analytics_page.objectName())
        print("[DEBUG] Created AnalyticsPage.")

        print("[DEBUG] About to create SettingsPage...")
        self.settings_page = SettingsPage(self)
        self.settings_page.setObjectName("SettingsPage")
        self.settings_page.setToolTip(self.settings_page.objectName())
        print("[DEBUG] Created SettingsPage.")

        print("[DEBUG] About to create AboutPage...")
        self.about_page = AboutPage(self)
        self.about_page.setObjectName("AboutPage")
        self.about_page.setToolTip(self.about_page.objectName())
        print("[DEBUG] Created AboutPage.")

        from PyQt5.QtWidgets import QMessageBox
        print("[DEBUG] About to import and create DashboardPage...")
        try:
            from gui.dashboard_page import DashboardPage
            print("[DEBUG] Imported DashboardPage class.")
            self.dashboard_page = DashboardPage(self)
            self.dashboard_page.setObjectName("DashboardPage")
            self.dashboard_page.setToolTip(self.dashboard_page.objectName())
            print("[DEBUG] Created DashboardPage instance.")
            self.tabs.insertTab(0, self.dashboard_page, "Dashboard")
            self.tabs.setTabToolTip(0, self.dashboard_page.objectName())
            self.tabs.setCurrentIndex(0)
            print("[DEBUG] Inserted DashboardPage tab.")
            # Now that dashboard_page is assigned, apply the initial theme
            self.dashboard_page._on_theme_changed(0)
        except Exception as e:
            import traceback
            print("[DEBUG] Exception caught in DashboardPage creation!")
            print(f"DashboardPage could not be loaded: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(None, "Dashboard Error", f"DashboardPage could not be loaded:\n{e}")

        # Add tabs and set tab tooltips
        self.tabs.addTab(self.upload_page, "Analyze")
        self.tabs.setTabToolTip(self.tabs.indexOf(self.upload_page), self.upload_page.objectName())
        self.tabs.addTab(self.catalog_page, "Catalog")
        self.tabs.setTabToolTip(self.tabs.indexOf(self.catalog_page), self.catalog_page.objectName())
        self.tabs.addTab(self.analytics_page, "Analytics")
        self.tabs.setTabToolTip(self.tabs.indexOf(self.analytics_page), self.analytics_page.objectName())
        self.tabs.addTab(self.settings_page, "Settings")
        self.tabs.setTabToolTip(self.tabs.indexOf(self.settings_page), self.settings_page.objectName())
        self.tabs.addTab(self.about_page, "About")
        self.tabs.setTabToolTip(self.tabs.indexOf(self.about_page), self.about_page.objectName())

        self.window.setCentralWidget(self.tabs)
        # Ensure every widget has a tooltip matching its objectName (or auto-name)
        self._apply_hover_labels(self.window)
        self.restore_window_settings()
        # Restore last selected tab if present
        try:
            last_idx = self.settings.value("last_tab_index")
            if last_idx is not None:
                self.tabs.setCurrentIndex(int(last_idx))
        except Exception:
            pass
        self.window.show()
        self.window.closeEvent = self.on_close
        # Defer size sync until widgets are laid out
        QTimer.singleShot(0, self._setup_size_sync_for_qpushbutton27)
        print("[DEBUG] ProvenanceApp.setup_ui finished.")

    def _apply_hover_labels(self, root: QWidget):
        # Assign objectNames where missing and set tooltips for all widgets
        blocked = {"q_pushbutton_28", "qpushbutton_28", "qpushbutton_27"}
        counters = {}
        widgets = [root] + root.findChildren(QWidget)
        for w in widgets:
            cls = w.metaObject().className() if hasattr(w, 'metaObject') else w.__class__.__name__
            name = w.objectName() if hasattr(w, 'objectName') else ""
            if not name:
                idx = counters.get(cls, 0) + 1
                counters[cls] = idx
                try:
                    w.setObjectName(f"{cls}_{idx}")
                except Exception:
                    pass
                name = getattr(w, 'objectName', lambda: "")()
            # If this widget is explicitly blocked, remove it from UI
            try:
                if (name or "").lower() in blocked:
                    parent = w.parentWidget()
                    if parent is not None and hasattr(parent, 'layout'):
                        lay = parent.layout()
                        if lay is not None:
                            lay.removeWidget(w)
                    w.setParent(None)
                    w.deleteLater()
                    continue
            except Exception:
                pass
            # Avoid setting tooltips for internal Qt widgets like qt_scrollarea_viewport
            try:
                lname = (name or "").lower()
                if lname.startswith("qt_") or "viewport" in lname:
                    continue
                if hasattr(w, 'setToolTip'):
                    w.setToolTip(name or cls)
            except Exception:
                continue

    def restore_window_settings(self):
        # Main window geometry/state
        geo = self.settings.value("window_geometry")
        if isinstance(geo, QByteArray) or geo:
            self.window.restoreGeometry(geo)
        state = self.settings.value("window_state")
        if isinstance(state, QByteArray) or state:
            self.window.restoreState(state)
        # Upload page splitter
        us = self.settings.value("upload_splitter_sizes")
        if us:
            try:
                self.upload_page.set_splitter_sizes([int(s) for s in us])
            except Exception:
                pass
        # Catalog page splitter and table header
        cs = self.settings.value("catalog_splitter_sizes")
        if cs:
            try:
                self.catalog_page.set_splitter_sizes([int(s) for s in cs])
            except Exception:
                pass
        ch = self.settings.value("catalog_header_state")
        if isinstance(ch, QByteArray) or ch:
            try:
                self.catalog_page.set_table_header_state(ch)
            except Exception:
                pass

    def on_close(self, event):
        # Save window geometry/state
        self.settings.setValue("window_geometry", self.window.saveGeometry())
        self.settings.setValue("window_state", self.window.saveState())
        # Per-page UI state
        self.settings.setValue("upload_splitter_sizes", self.upload_page.get_splitter_sizes())
        # Catalog state
        try:
            self.settings.setValue("catalog_splitter_sizes", self.catalog_page.get_splitter_sizes())
        except Exception:
            pass
        try:
            self.settings.setValue("catalog_header_state", self.catalog_page.get_table_header_state())
        except Exception:
            pass
        # Last selected tab index
        try:
            self.settings.setValue("last_tab_index", self.tabs.currentIndex())
        except Exception:
            pass
        event.accept()

    # Navigation is now handled by tabs

    # --- Helper: Keep QPushButton_27 the same height as the 'detailpanel' widget ---
    class _ResizeSync(QObject):
        def __init__(self, source: QWidget, target: QWidget):
            super().__init__(source)
            self.source = source
            self.target = target
            source.installEventFilter(self)

        def eventFilter(self, obj, event):
            if obj is self.source and event.type() == QEvent.Resize:
                try:
                    h = max(0, self.source.height())
                    # Match height; allow target to expand horizontally as needed
                    self.target.setMinimumHeight(h)
                    self.target.setMaximumHeight(h)
                except Exception:
                    pass
            return False

    def _setup_size_sync_for_qpushbutton27(self):
        try:
            # Find target button by name (case-insensitive variants)
            btn = self.window.findChild(QWidget, "QPushButton_27") or self.window.findChild(QWidget, "qpushbutton_27")
            detail = self.window.findChild(QWidget, "detailpanel")
            if btn is None or detail is None:
                return
            # Make the button expand horizontally, fix height to match detail panel
            try:
                sp = btn.sizePolicy()
                sp.setHorizontalPolicy(sp.Expanding)
                btn.setSizePolicy(sp)
            except Exception:
                pass
            # Initial sync now that window is shown
            h = max(0, detail.height())
            btn.setMinimumHeight(h)
            btn.setMaximumHeight(h)
            # Keep them in sync on future resizes
            self._qpushbutton27_sync = self._ResizeSync(detail, btn)
        except Exception:
            pass

    # --- Helper: Build a QR code pixmap containing provided text ---
    def _build_qr_icon_pixmap(self, text: str, size: int = 256) -> QPixmap:
        try:
            import io
            import qrcode  # type: ignore
            from qrcode.constants import ERROR_CORRECT_M  # type: ignore

            qr = qrcode.QRCode(
                version=None,
                error_correction=ERROR_CORRECT_M,
                box_size=10,
                border=2,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            # Convert to PNG bytes
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            data = buf.getvalue()
            pix = QPixmap()
            pix.loadFromData(data, "PNG")
            if size and size > 0:
                pix = pix.scaled(size, size, transformMode=Qt.SmoothTransformation)
            return pix
        except Exception:
            return QPixmap()

    # --- Helper: Determine cache path for QR icon ---
    def _qr_cache_path(self, text: str, size: int) -> str:
        try:
            base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not base:
                base = os.path.join(os.path.expanduser("~"), ".provenance_cache")
            digest = hashlib.sha1(f"{text}|{size}".encode("utf-8")).hexdigest()[:16]
            icon_dir = os.path.join(base, "icons")
            return os.path.join(icon_dir, f"qr_{digest}.png")
        except Exception:
            # Fallback to local directory
            return os.path.abspath("qr_icon.png")

    # --- Helper: Build white sort-arrow pixmaps ---
    def _build_sort_arrow_pixmap(self, direction: str, size: int = 16, color: QColor = QColor("white")) -> QPixmap:
        try:
            s = max(8, int(size))
            pix = QPixmap(s, s)
            pix.fill(Qt.transparent)
            painter = QPainter(pix)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            if direction == "up":
                points = [QPoint(s//2, s//4), QPoint(s//4, 3*s//4), QPoint(3*s//4, 3*s//4)]
            else:  # down
                points = [QPoint(s//4, s//4), QPoint(3*s//4, s//4), QPoint(s//2, 3*s//4)]
            painter.drawPolygon(QPolygon(points))
            painter.end()
            return pix
        except Exception:
            return QPixmap()

    def _arrow_icon_cache_path(self, direction: str, size: int, color: QColor) -> str:
        try:
            base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not base:
                base = os.path.join(os.path.expanduser("~"), ".provenance_cache")
            digest = hashlib.sha1(f"{direction}|{size}|{color.name()}".encode("utf-8")).hexdigest()[:16]
            icon_dir = os.path.join(base, "icons")
            return os.path.join(icon_dir, f"arrow_{direction}_{digest}.png")
        except Exception:
            return os.path.abspath(f"arrow_{direction}.png")
