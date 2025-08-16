"""
SettingsPage: Manage API keys and preferences.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
import json
import os

CONFIG_PATH = "config.json"

class SettingsPage(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.init_ui()
        self.load_config()

    def init_ui(self):
        layout = QVBoxLayout()
        self.api_label = QLabel("OpenAI API Key:")
        self.api_input = QLineEdit()
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.api_label)
        layout.addWidget(self.api_input)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                self.api_input.setText(config.get("openai_api_key", ""))

    def save_config(self):
        config = {"openai_api_key": self.api_input.text()}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
