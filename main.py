"""
Provenance Program Entry Point
- Launches the PyQt5 GUI for image upload, annotation, cataloging, and analytics.
- All data is stored in provenance.db (SQLite).
"""


import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox

REQUIRED_PACKAGES = [
    'PyQt5',
    'pyqtgraph',
    # Add other dependencies as needed
]

def ensure_dependencies():
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg if pkg != 'PyQt5' else 'PyQt5.QtWidgets')
        except ImportError:
            missing.append(pkg)
    if missing:
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Missing Dependencies')
        msg.setText(f"The following packages are required but not installed: {', '.join(missing)}\n\nInstall them now?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        if msg.exec_() == QMessageBox.Yes:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            QMessageBox.information(None, 'Dependencies Installed', 'Dependencies installed. Please restart the application.')
            sys.exit(0)
        else:
            sys.exit(1)

ensure_dependencies()
from gui.app import ProvenanceApp

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--reset-settings', action='store_true', help='Reset QSettings for this app')
    args = parser.parse_args()
    if args.reset_settings:
        from PyQt5.QtCore import QSettings
        QSettings("JUREKA", "ProvenanceToyShop").clear()
        print("[INFO] QSettings cleared. Relaunch without --reset-settings.")
        sys.exit(0)
    print("[DEBUG] About to create ProvenanceApp...")
    app = ProvenanceApp(sys.argv)
    print("[DEBUG] Created ProvenanceApp.")
    print("[DEBUG] About to call setup_ui()...")
    app.setup_ui()
    print("[DEBUG] About to call app.exec_()...")
    sys.exit(app.exec_())
