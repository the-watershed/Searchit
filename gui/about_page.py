"""
AboutPage: Shows app info and credits.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

class AboutPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        about = QLabel("""
        <h2>Provenance Toy Shop</h2>
        <p>Futuristic provenance and cataloging tool.<br>
        Created by JUREKA! Treasures.<br>
        Powered by OpenAI Vision.<br>
        <b>Version:</b> 1.0.0</p>
        """)
        about.setTextFormat(1)  # RichText
        layout.addWidget(about)
        self.setLayout(layout)
