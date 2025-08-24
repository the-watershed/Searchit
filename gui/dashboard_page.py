"""
Futuristic Server Dashboard Page
- Neon/cyberpunk theme
- Real-time server status, comms, and analytics
- Modular, resizable panels
- Ready for data integration
"""


import sys
import datetime
import subprocess
import json
import psutil
REQUIRED_PACKAGES = [
    'PyQt5',
    'pyqtgraph',
]
def ensure_dependencies():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg if pkg != 'PyQt5' else 'PyQt5.QtWidgets')
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[DEBUG] Missing dependencies in dashboard_page.py: {missing}")
        # Do not create QApplication or QMessageBox here! Let main.py handle it.
        raise ImportError(f"Missing dependencies: {', '.join(missing)}")

ensure_dependencies()
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTableWidget, QTableWidgetItem,
    QProgressBar, QTextEdit, QPushButton, QComboBox, QFileDialog, QMessageBox, QInputDialog
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg

class DashboardPage(QWidget):
    def __init__(self, app=None, parent=None):
        print("[DEBUG] DashboardPage __init__ called")
        super().__init__(parent)
        from db import DB
        self.db = DB()
        self.app = app
        # Initialize dashboard state variables before UI/timers
        self.timeline_x = []
        self.timeline_y = []
        self.heatmap_data = None
        self.api_latency = []
        self.api_status = 'Unknown'
        self.cpu_usage = []
        self.ram_usage = []
        self.net_usage = []
        self.cpu_core_bars = []  # Ensure this is always defined before init_ui
        self.init_ui()
        self.init_timers()



    def init_ui(self):
        main_layout = QVBoxLayout()

        # Theme picker
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel('Theme:'))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Neon Curio', 'Steampunk', 'Dark Carnival'])
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_row.addWidget(self.theme_combo)
        theme_row.addStretch(1)
        main_layout.addLayout(theme_row)

        # 1. AI Activity & Provenance Timeline
        self.timeline_plot = pg.PlotWidget(title='AI Activity & Provenance Timeline')
        self.timeline_plot.setToolTip('Timeline of all AI analyses, catalog changes, and user actions. Click points for details.')
        main_layout.addWidget(self.timeline_plot)

        # 2. Artifact Price Heatmap (uses prc_med)
        self.value_heatmap = pg.ImageView()
        self.value_heatmap.setToolTip('Artifact Price Heatmap: Visualizes median price of cataloged items.')
        # Seed with a default image to avoid autoLevels errors before data arrives
        try:
            import numpy as _np
            _img = _np.zeros((2, 2), dtype=float)
            self.value_heatmap.setImage(_img, autoLevels=False)
            # Provide explicit min/max levels
            if hasattr(self.value_heatmap, 'setLevels'):
                self.value_heatmap.setLevels(0.0, 1.0)
        except Exception:
            pass
        main_layout.addWidget(self.value_heatmap)

        # 3. OpenAI API Health & Usage
        api_status_layout = QHBoxLayout()
        self.api_status_label = QLabel('OpenAI API: Online')
        self.api_status_label.setToolTip('Shows current OpenAI API status.')
        self.api_latency_bar = QProgressBar()
        self.api_latency_bar.setRange(0, 1000)
        self.api_latency_bar.setValue(50)
        self.api_latency_bar.setToolTip('Current OpenAI API latency in ms.')
        self.api_quota_label = QLabel('Quota: 95%')
        self.api_quota_label.setToolTip('Remaining OpenAI API quota for this month.')
        api_status_layout.addWidget(self.api_status_label)
        api_status_layout.addWidget(self.api_latency_bar)
        api_status_layout.addWidget(self.api_quota_label)
        main_layout.addLayout(api_status_layout)
        # Add a plot for API health
        self.api_health_plot = pg.PlotWidget(title='OpenAI API Health')
        self.api_health_plot.setToolTip('Graph of OpenAI API latency over time.')
        main_layout.addWidget(self.api_health_plot)

        # 4. Curio Cabinet Inventory (visual grid)
        self.cabinet_table = QTableWidget(2, 5)
        self.cabinet_table.setHorizontalHeaderLabels([f'Slot {i+1}' for i in range(5)])
        self.cabinet_table.setVerticalHeaderLabels(['Top Shelf', 'Bottom Shelf'])
        self.cabinet_table.setToolTip('Curio Cabinet: Visual grid of artifacts. Drag and drop to rearrange. Hover for details.')
        main_layout.addWidget(self.cabinet_table)

        # 5. (No eBay/Market Feed in production)

        # 6. System Health & Security
        sys_health_layout = QHBoxLayout()
        self.cpu_bar = QProgressBar(); self.cpu_bar.setRange(0, 100); self.cpu_bar.setValue(30); self.cpu_bar.setFormat('CPU: %p%')
        self.ram_bar = QProgressBar(); self.ram_bar.setRange(0, 100); self.ram_bar.setValue(40); self.ram_bar.setFormat('RAM: %p%')
        self.ram_label = QLabel('')
        self.disk_bar = QProgressBar(); self.disk_bar.setRange(0, 100); self.disk_bar.setFormat('Disk: %p%')
        self.disk_label = QLabel('')
        self.net_bar = QProgressBar(); self.net_bar.setRange(0, 100); self.net_bar.setValue(20); self.net_bar.setFormat('NET: %p%')
        self.net_label = QLabel('')
        self.security_label = QLabel('Security: All clear')
        for w in (self.cpu_bar, self.ram_bar, self.ram_label, self.disk_bar, self.disk_label, self.net_bar, self.net_label, self.security_label):
            sys_health_layout.addWidget(w)
        main_layout.addLayout(sys_health_layout)

        # Per-core CPU bars
        try:
            from PyQt5.QtWidgets import QGridLayout
            import psutil as _ps
            cores_layout = QGridLayout()
            core_count = max(1, _ps.cpu_count(logical=True) or 1)
            self.cpu_core_bars = []
            cols = 8  # wrap bars for readability
            for i in range(core_count):
                bar = QProgressBar(); bar.setRange(0, 100); bar.setFormat(f"Core {i}: %p%")
                self.cpu_core_bars.append(bar)
                r, c = divmod(i, cols)
                cores_layout.addWidget(bar, r, c)
            main_layout.addLayout(cores_layout)
        except Exception:
            pass

        # 7. Narrative/Story Mode
        self.lore_panel = QTextEdit()
        self.lore_panel.setReadOnly(True)
        self.lore_panel.setPlaceholderText('Lore and narrative will be woven here by the AI...')
        self.lore_panel.setToolTip('Narrative/Story Mode: AI-generated lore and artifact stories.')
        main_layout.addWidget(self.lore_panel)

        # 8. Quick Actions
        actions_layout = QHBoxLayout()
        self.analyze_btn = QPushButton('Analyze New Artifact')
        self.analyze_btn.setToolTip('Start a new AI analysis for a recently added artifact.')
        self.export_btn = QPushButton('Export Catalog')
        self.export_btn.setToolTip('Export the entire artifact catalog to file.')
        self.reeval_btn = QPushButton('AI Re-Evaluate All')
        self.reeval_btn.setToolTip('Re-run AI analysis on all cataloged artifacts.')
        self.ebay_btn = QPushButton('Generate eBay Listing')
        self.ebay_btn.setToolTip('Generate an eBay-ready listing for the selected artifact.')
        # Wire up actions
        try:
            self.analyze_btn.clicked.connect(self._go_to_upload)
            self.export_btn.clicked.connect(self._export_catalog)
            self.reeval_btn.clicked.connect(self._reevaluate_all)
            self.ebay_btn.clicked.connect(self._generate_ebay_listing)
        except Exception:
            pass
        actions_layout.addWidget(self.analyze_btn)
        actions_layout.addWidget(self.export_btn)
        actions_layout.addWidget(self.reeval_btn)
        actions_layout.addWidget(self.ebay_btn)
        main_layout.addLayout(actions_layout)

        self.setLayout(main_layout)
        self.update_dashboard()
        self.theme_label = QLabel('Theme:')
        self.theme_label.setToolTip('Switch the dashboard visual theme.')


    # Removed _status_gauge and server widgets

    def init_timers(self):
        import numpy as np
        import psutil
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(2000)

    def update_dashboard(self):
        import numpy as np, psutil, time
        # Timeline: show revision history count over time
        revisions = []
        for item in self.db.get_all_items():
            for rev in item.get('history', []):
                # get_revision_history returns (notes, timestamp)
                try:
                    ts = rev[1] if isinstance(rev, (list, tuple)) and len(rev) >= 2 else None
                except Exception:
                    ts = None
                try:
                    t = time.mktime(datetime.datetime.fromisoformat(ts).timetuple()) if ts else 0
                except Exception:
                    t = 0
                revisions.append((t, item['id']))
        revisions.sort()
        self.timeline_x = [r[0] for r in revisions]
        self.timeline_y = [r[1] for r in revisions]
        self.timeline_plot.clear()
        if self.timeline_x:
            self.timeline_plot.plot(self.timeline_x, self.timeline_y, pen=pg.mkPen('#ffaa00', width=2), symbol='o')

        # Heatmap: artifact prices (by prc_med)
        items = self.db.get_all_items()
        def mid_price(i):
            # Prefer prc_med; if missing, average low/high if available
            pm = i.get('prc_med')
            if pm is not None:
                return float(pm)
            pl, ph = i.get('prc_low'), i.get('prc_hi')
            try:
                if pl is not None and ph is not None:
                    return (float(pl) + float(ph)) / 2.0
            except Exception:
                pass
            return 0.0
        values = [mid_price(i) for i in items]
        if values:
            grid = int(np.ceil(np.sqrt(len(values))))
            arr = np.zeros((grid, grid))
            for idx, v in enumerate(values):
                arr[idx//grid, idx%grid] = v
            self.heatmap_data = arr
            self.value_heatmap.setImage(arr, autoLevels=True)

        # API health: ping OpenAI API and measure latency (requests optional)
        try:
            import requests
            start = time.time()
            r = requests.get('https://api.openai.com/v1/models', timeout=2)
            latency = int((time.time() - start) * 1000)
            self.api_status = 'Online' if r.status_code == 200 else 'Error'
        except Exception:
            latency = 999
            self.api_status = 'Offline'
        self.api_latency.append(latency)
        if len(self.api_latency) > 60:
            self.api_latency = self.api_latency[-60:]
        self.api_status_label.setText(f'OpenAI API: {self.api_status}')
        self.api_latency_bar.setValue(latency)
        self.api_health_plot.clear()
        self.api_health_plot.plot(list(range(len(self.api_latency))), self.api_latency, pen=pg.mkPen('#00fff7', width=2))

        # System health: real CPU, RAM, NET
        # CPU (overall and per-core)
        cpu_percent = psutil.cpu_percent()
        self.cpu_usage.append(cpu_percent)
        per_core = psutil.cpu_percent(percpu=True)
        for i, val in enumerate(per_core):
            if i < len(self.cpu_core_bars):
                self.cpu_core_bars[i].setValue(int(val))
        self.cpu_bar.setValue(int(cpu_percent))
        # RAM
        ram = psutil.virtual_memory()
        self.ram_usage.append(ram.percent)
        self.ram_bar.setValue(int(ram.percent))
        self.ram_label.setText(f"{ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB")
        # Disk (pick a valid mount/drive)
        import os as _os
        try:
            if _os.name == 'nt':
                drive = _os.path.splitdrive(_os.getcwd())[0] or 'C:'
                disk = psutil.disk_usage(drive + '\\')
            else:
                disk = psutil.disk_usage('/')
        except Exception:
            disk = psutil.disk_usage('/')
        self.disk_bar.setValue(int(disk.percent))
        self.disk_label.setText(f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB")
        # Disk I/O (optional: could add a plot or more detail)
        # Network
        net = psutil.net_io_counters()
        # Calculate throughput (bytes/sec)
        if not hasattr(self, '_last_net'): self._last_net = net
        sent_per_sec = net.bytes_sent - getattr(self, '_last_net').bytes_sent
        recv_per_sec = net.bytes_recv - getattr(self, '_last_net').bytes_recv
        self.net_bar.setValue(min(int((sent_per_sec + recv_per_sec) / 1024), 100))
        self.net_label.setText(f"Up: {sent_per_sec//1024} KB/s | Down: {recv_per_sec//1024} KB/s")
        self._last_net = net
        # Curio Cabinet: show real catalog items
        self.cabinet_table.clearContents()
        for idx, item in enumerate(items):
            row, col = idx // 5, idx % 5
            if row < 2:
                label = item.get('title') or f'ID {item["id"]}'
                self.cabinet_table.setItem(row, col, QTableWidgetItem(label))
        # Lore: generate from provenance and notes
        lore = '\n'.join([f"{i.get('title','Unknown')}: {i.get('provenance_notes','') or i.get('notes','')}" for i in items if i.get('provenance_notes') or i.get('notes')])
        self.lore_panel.setPlainText(lore)

    def futuristic_qss(self):
        return """
            QWidget { background: #181c24; color: #e0e0e0; font-family: 'Consolas', monospace; }
            QTableWidget { background: #23283a; color: #00fff7; gridline-color: #444; }
            QHeaderView::section { background: #1a1f2b; color: #00fff7; border: 1px solid #333; }
            QProgressBar { background: #23283a; border: 1px solid #00fff7; border-radius: 5px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00fff7, stop:1 #ff00e1); }
            QLabel#UptimeLabel { color: #ffaa00; font-weight: bold; }
            QLabel#AlertLabel { color: #00ff99; font-size: 16px; }
            QTextEdit { background: #181c24; color: #ffaa00; border: 1px solid #444; }
            QPushButton { background: #23283a; color: #00fff7; border: 1px solid #00fff7; border-radius: 5px; padding: 4px 12px; }
            QPushButton:hover { background: #00fff7; color: #181c24; }
            QTabBar::tab {
                background: #23283a;
                color: #fff;
                border: 1px solid #00fff7;
                border-bottom: none;
                padding: 6px 18px;
                min-width: 80px;
                font-weight: bold;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: #00fff7;
                color: #181c24;
                border: 1px solid #00fff7;
            }
            QTabWidget::pane {
                border: 1px solid #00fff7;
                top: -1px;
                background: #181c24;
            }
        """

    def steampunk_qss(self):
        return """
            QWidget { background: #2b221b; color: #f4e5c2; font-family: 'Garamond'; }
            QTableWidget { background: #3a2f25; color: #f0d9b5; gridline-color: #5a4a3b; }
            QHeaderView::section { background: #514131; color: #f4e5c2; border: 1px solid #8b5e34; }
            QProgressBar { background: #3a2f25; border: 1px solid #8b5e34; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: #c49a6c; }
            QTextEdit { background: #2b221b; color: #f4e5c2; border: 1px solid #8b5e34; }
            QPushButton { background: #8b5e34; color: #f7efe4; border: 1px solid #6f482a; border-radius: 4px; padding: 4px 10px; }
            QPushButton:hover { background: #a66f3c; }
            QTabBar::tab { background: #3a2f25; color: #f4e5c2; border: 1px solid #8b5e34; border-bottom: none; padding: 6px 14px; }
            QTabBar::tab:selected, QTabBar::tab:hover { background: #8b5e34; color: #2b221b; }
            QTabWidget::pane { border: 1px solid #8b5e34; top: -1px; background: #2b221b; }
        """

    def carnival_qss(self):
        return """
            QWidget { background: #1a0f1f; color: #fdf6ff; font-family: 'Trebuchet MS'; }
            QTableWidget { background: #2a1533; color: #ffe070; gridline-color: #5c2a6e; }
            QHeaderView::section { background: #3a1a47; color: #ffe070; border: 1px solid #ff4da6; }
            QProgressBar { background: #2a1533; border: 1px solid #ff4da6; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #ff4da6, stop:1 #ffd166); }
            QTextEdit { background: #1a0f1f; color: #ffd166; border: 1px solid #5c2a6e; }
            QPushButton { background: #3a1a47; color: #ffd166; border: 1px solid #ff4da6; border-radius: 4px; padding: 4px 10px; }
            QPushButton:hover { background: #ff4da6; color: #1a0f1f; }
            QTabBar::tab { background: #2a1533; color: #ffd166; border: 1px solid #ff4da6; border-bottom: none; padding: 6px 14px; }
            QTabBar::tab:selected, QTabBar::tab:hover { background: #ff4da6; color: #1a0f1f; }
            QTabWidget::pane { border: 1px solid #ff4da6; top: -1px; background: #1a0f1f; }
        """

    def _on_theme_changed(self, idx: int):
        try:
            if hasattr(self, 'app') and hasattr(self.app, 'set_global_theme'):
                self.app.set_global_theme(idx)
        except Exception:
            pass

    # --- Quick action handlers ---
    def _go_to_upload(self):
        try:
            if hasattr(self.app, 'tabs') and hasattr(self.app, 'upload_page'):
                idx = self.app.tabs.indexOf(self.app.upload_page)
                if idx != -1:
                    self.app.tabs.setCurrentIndex(idx)
        except Exception:
            pass

    def _export_catalog(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Export Catalog", "catalog_export.json", "JSON Files (*.json)")
            if not path:
                return
            items = self.db.get_all_items() or []
            # Enrich with images array
            for it in items:
                try:
                    it['images'] = self.db.get_images(it['id'])
                except Exception:
                    it['images'] = []
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Export", f"Catalog exported to:\n{path}")
        except Exception as e:
            try:
                QMessageBox.critical(self, "Export Error", str(e))
            except Exception:
                pass

    def _reevaluate_all(self):
        # Bulk AI re-evaluation: re-run OpenAI analysis on all items using stored images and annotations.
        try:
            items = self.db.get_all_items() or []
            if not items:
                QMessageBox.information(self, "Re-evaluate", "No items in catalog.")
                return
            from openai_client import analyze_images
            # Provide a tiny progress window via log area
            processed = 0
            errors = 0
            for it in items:
                try:
                    img_paths = []
                    legacy = it.get('image_path')
                    if legacy:
                        img_paths.append(legacy)
                    imgs = self.db.get_images(it['id']) or []
                    for p in imgs:
                        if p not in img_paths:
                            img_paths.append(p)
                    if not img_paths:
                        continue
                    annos = self.db.get_image_annotations(it['id'])
                    analyze_images.log_box = getattr(self, 'lore_panel', None)
                    res = analyze_images(img_paths, annos or [])
                    if res and isinstance(res, str):
                        self.db.update_item_analysis(it['id'], res)
                        processed += 1
                    else:
                        errors += 1
                except Exception:
                    errors += 1
            QMessageBox.information(self, "Re-evaluate",
                                    f"Re-evaluated {processed} item(s). Errors: {errors}.")
            # Refresh UI panels
            self.update_dashboard()
        except Exception as e:
            try:
                QMessageBox.critical(self, "Re-evaluate Error", str(e))
            except Exception:
                pass

    def _generate_ebay_listing(self):
        # Generate a simple eBay listing text for a selected item by ID.
        try:
            items = self.db.get_all_items() or []
            if not items:
                QMessageBox.information(self, "eBay Listing", "No items available.")
                return
            ids = [str(it['id']) for it in items]
            item_id_str, ok = QInputDialog.getItem(self, "Select Item", "Item ID:", ids, 0, False)
            if not ok or not item_id_str:
                return
            item_id = int(item_id_str)
            item = self.db.get_item(item_id)
            if not item:
                QMessageBox.warning(self, "eBay Listing", "Item not found.")
                return
            # Build a simple listing text using known fields
            title = item.get('title') or f"Artifact #{item_id}"
            brand = item.get('brand') or ''
            maker = item.get('maker') or ''
            desc = item.get('description') or item.get('provenance_notes') or (item.get('notes') or '')
            low, med, high = self.db.get_price_range(item_id)
            price_hint = f"Price guidance: Low ${low} / Median ${med} / High ${high}" if any((low, med, high)) else ""
            listing = (
                f"Title: {title}\n"
                f"Brand/Maker: {brand} {maker}\n\n"
                f"Description:\n{desc}\n\n"
                f"Shipping: Carefully packed; ships within 2 business days.\n"
                f"Condition: {item.get('condition') or 'See photos for details.'}\n\n"
                f"{price_hint}"
            ).strip()
            # Show listing text
            QMessageBox.information(self, "Generated eBay Listing", listing)
        except Exception as e:
            try:
                QMessageBox.critical(self, "Listing Error", str(e))
            except Exception:
                pass

# Example usage (add to your main window):
# dashboard = DashboardPage()
# main_layout.addWidget(dashboard)
