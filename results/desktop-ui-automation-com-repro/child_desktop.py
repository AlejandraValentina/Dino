from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.pop("QT_QPA_PLATFORM", None)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project

app = QApplication.instance() or QApplication([])
window = DinoDesktopWindow(new_design_project("SYNTHETIC UIA lifecycle only"))
window.setWindowTitle("Dino UIA COM Lifecycle Repro")
window.resize(1360, 900)
window.show()
QTimer.singleShot(300, lambda: Path(sys.argv[1]).write_text("visible\n", encoding="utf-8"))
sys.exit(app.exec())
