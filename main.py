"""
Provenance Program Entry Point
- Launches the PyQt5 GUI for image upload, annotation, cataloging, and analytics.
- All data is stored in provenance.db (SQLite).
"""

import sys
from gui.app import ProvenanceApp

if __name__ == "__main__":
    app = ProvenanceApp(sys.argv)
    sys.exit(app.exec_())
