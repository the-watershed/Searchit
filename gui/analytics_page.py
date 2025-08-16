"""
AnalyticsPage: Shows price tracking, listing performance, and revision history analytics.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from db import DB

class AnalyticsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        layout = QVBoxLayout()
        self.stats_label = QLabel("Analytics will appear here.")
        layout.addWidget(self.stats_label)
        self.setLayout(layout)

    def refresh(self):
        stats = self.db.get_analytics()
        self.stats_label.setText(stats)
