"""
SettingsPage: Manage API keys and preferences using secure storage.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
    QTextEdit, QCheckBox, QMessageBox, QHBoxLayout
)
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
        
        # Security notice
        security_label = QLabel("🔒 API Key Security")
        security_label.setStyleSheet("font-weight: bold; color: #2b1e1e;")
        layout.addWidget(security_label)
        
        security_text = QLabel(
            "For maximum security, set environment variable: SEARCHIT_OPENAI_API_KEY\n"
            "Otherwise, your key will be stored in encoded format locally."
        )
        security_text.setStyleSheet("color: #666; font-size: 11px;")
        security_text.setWordWrap(True)
        layout.addWidget(security_text)
        
        # API Key section
        self.api_label = QLabel("OpenAI API Key:")
        self.api_input = QLineEdit()
        self.api_input.setEchoMode(QLineEdit.Password)  # Hide the key
        
        # Show/hide toggle
        key_layout = QHBoxLayout()
        key_layout.addWidget(self.api_input)
        
        self.show_key_btn = QPushButton("👁")
        self.show_key_btn.setMaximumWidth(40)
        self.show_key_btn.clicked.connect(self.toggle_key_visibility)
        key_layout.addWidget(self.show_key_btn)
        
        layout.addWidget(self.api_label)
        layout.addLayout(key_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_btn)
        
        self.test_btn = QPushButton("Test API Key")
        self.test_btn.clicked.connect(self.test_api_key)
        button_layout.addWidget(self.test_btn)
        
        self.clear_btn = QPushButton("Clear Key")
        self.clear_btn.clicked.connect(self.clear_api_key)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # Status display
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        layout.addWidget(QLabel("Status:"))
        layout.addWidget(self.status_text)
        
        self.setLayout(layout)

    def toggle_key_visibility(self):
        """Toggle between showing and hiding the API key."""
        if self.api_input.echoMode() == QLineEdit.Password:
            self.api_input.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("🙈")
        else:
            self.api_input.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("👁")

    def load_config(self):
        """Load API key from secure storage."""
        try:
            from secure_storage import get_openai_api_key
            api_key = get_openai_api_key()
            
            if api_key:
                self.api_input.setText(api_key)
                if api_key.startswith("env:"):
                    self.status_text.setText("✅ Using environment variable (most secure)")
                else:
                    self.status_text.setText("✅ Using encoded local storage")
            else:
                self.status_text.setText("⚠️ No API key found. Please enter your OpenAI API key.")
                
        except ImportError:
            self.status_text.setText("⚠️ Secure storage not available. Using fallback config.json")
            # Fallback to old method
            config = {}
            if os.path.exists(CONFIG_PATH):
                try:
                    with open(CONFIG_PATH, "r") as f:
                        content = f.read().strip()
                        if content:
                            config = json.loads(content)
                except Exception as e:
                    self.status_text.setText(f"❌ Error loading config: {e}")
            
            self.api_input.setText(config.get("openai_api_key", ""))

    def save_config(self):
        """Save API key using secure storage."""
        api_key = self.api_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter an API key.")
            return
            
        try:
            from secure_storage import store_openai_api_key
            
            if store_openai_api_key(api_key):
                self.status_text.setText("✅ API key saved securely")
                QMessageBox.information(self, "Success", "API key saved securely!")
                
                # Also remove from old config.json for security
                self._remove_from_old_config()
            else:
                self.status_text.setText("❌ Failed to save API key")
                QMessageBox.warning(self, "Error", "Failed to save API key securely.")
                
        except ImportError:
            # Fallback to old method
            self.status_text.setText("⚠️ Using fallback storage (less secure)")
            config = {"openai_api_key": api_key}
            try:
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f)
                QMessageBox.information(self, "Saved", "API key saved to config.json")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {e}")

    def _remove_from_old_config(self):
        """Remove API key from old config.json for security."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r") as f:
                    config = json.load(f)
                
                if "openai_api_key" in config:
                    del config["openai_api_key"]
                    
                    with open(CONFIG_PATH, "w") as f:
                        json.dump(config, f, indent=2)
                        
                    self.status_text.append("🔒 Removed API key from config.json for security")
        except Exception as e:
            print(f"Warning: Could not clean old config: {e}")

    def test_api_key(self):
        """Test the API key by making a simple request."""
        api_key = self.api_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter an API key first.")
            return
            
        self.status_text.setText("🔄 Testing API key...")
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Simple test request
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'API test successful'"}],
                max_tokens=10
            )
            
            if response.choices[0].message.content:
                self.status_text.setText("✅ API key test successful!")
                QMessageBox.information(self, "Success", "API key is working correctly!")
            else:
                self.status_text.setText("❌ API key test failed - no response")
                
        except Exception as e:
            error_msg = f"❌ API key test failed: {str(e)}"
            self.status_text.setText(error_msg)
            QMessageBox.warning(self, "Test Failed", f"API key test failed:\n{str(e)}")

    def clear_api_key(self):
        """Clear the stored API key."""
        reply = QMessageBox.question(
            self, "Confirm", 
            "Are you sure you want to clear the stored API key?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                from secure_storage import secure_key_manager
                secure_key_manager.remove_api_key("openai")
                self.api_input.clear()
                self.status_text.setText("🗑️ API key cleared from secure storage")
                QMessageBox.information(self, "Cleared", "API key has been removed.")
            except ImportError:
                # Fallback: clear from config.json
                try:
                    if os.path.exists(CONFIG_PATH):
                        with open(CONFIG_PATH, "r") as f:
                            config = json.load(f)
                        config.pop("openai_api_key", None)
                        with open(CONFIG_PATH, "w") as f:
                            json.dump(config, f, indent=2)
                    
                    self.api_input.clear()
                    self.status_text.setText("🗑️ API key cleared from config.json")
                    QMessageBox.information(self, "Cleared", "API key has been removed.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to clear key: {e}")
