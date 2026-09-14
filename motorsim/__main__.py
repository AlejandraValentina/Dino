"""Ejecutar con python -m motorsim desde la raíz del repositorio."""

import sys

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from .window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MotorSim")
    QLocale.setDefault(QLocale("es_UY"))
    translator = QTranslator(app)
    translator.load("qt_es", QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
    app.installTranslator(translator)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
