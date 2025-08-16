"""
CatalogPage: Browse, search, and view revision history and price tracking for all items.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHBoxLayout
from db import DB

class CatalogPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.db = DB()
        self.init_ui()
        self.refresh()

    def init_ui(self):
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Image", "Notes", "Value", "History"])
        layout.addWidget(self.table)
        self.refresh_btn = QPushButton("Refresh Catalog")
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        self.setLayout(layout)

    def refresh(self):
        items = self.db.get_all_items()
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(item['image_path']))
            self.table.setItem(row, 2, QTableWidgetItem(item['notes']))
            self.table.setItem(row, 3, QTableWidgetItem(item['value']))
            self.table.setItem(row, 4, QTableWidgetItem(str(item['history'])))
