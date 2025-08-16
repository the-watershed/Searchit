"""
ProvenanceApp: Main PyQt5 Application
- Sets up main window and navigation between pages.
"""


from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from gui.upload_page import UploadPage
from gui.catalog_page import CatalogPage
from gui.analytics_page import AnalyticsPage
from gui.settings_page import SettingsPage
from gui.about_page import AboutPage


class ProvenanceApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.window = QMainWindow()
        self.window.setWindowTitle("Provenance Toy Shop")
        self.tabs = QTabWidget()
        self.upload_page = UploadPage(self)
        self.catalog_page = CatalogPage(self)
        self.analytics_page = AnalyticsPage(self)
        self.settings_page = SettingsPage(self)
        self.about_page = AboutPage(self)
        self.tabs.addTab(self.upload_page, "Analyze")
        self.tabs.addTab(self.catalog_page, "Catalog")
        self.tabs.addTab(self.analytics_page, "Analytics")
        self.tabs.addTab(self.settings_page, "Settings")
        self.tabs.addTab(self.about_page, "About")
        self.window.setCentralWidget(self.tabs)
        self.window.resize(1200, 800)
        self.window.show()

    # Navigation is now handled by tabs
