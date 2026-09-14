"""Ventana de edición de la base de escritorio."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFileDialog, QFormLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QVBoxLayout, QWidget,
)

from .project import Project, ProjectError
from .storage import load_project, save_project


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.path: Path | None = None
        self.dirty = False
        self.resize(640, 300)
        self.setMinimumSize(420, 260)

        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(2147483647)
        self.name_edit.setObjectName("project_name")
        self.cycle_combo = QComboBox()
        self.cycle_combo.setObjectName("project_cycle")
        self.cycle_combo.addItems(["2T", "4T"])
        form = QFormLayout()
        form.addRow("&Nombre del proyecto:", self.name_edit)
        form.addRow("&Tipo de motor:", self.cycle_combo)
        self.file_label = QLabel()
        self.file_label.setWordWrap(True)
        self.file_label.setTextFormat(Qt.TextFormat.PlainText)
        self.file_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.state_label = QLabel()
        self.notice = QLabel("Versión básica: simulación no disponible")
        self.notice.setWordWrap(True)
        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(self.file_label)
        layout.addWidget(self.state_label)
        layout.addStretch()
        layout.addWidget(self.notice)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        menu = self.menuBar().addMenu("&Archivo")
        self.actions = {}
        for key, title, shortcut, callback in (
            ("new", "&Nuevo", QKeySequence.StandardKey.New, self.new_project),
            ("open", "&Abrir…", QKeySequence.StandardKey.Open, self.open_project),
            ("save", "&Guardar", QKeySequence.StandardKey.Save, self.save),
            ("save_as", "Guardar &como…", QKeySequence.StandardKey.SaveAs, self.save_as),
            ("exit", "&Salir", QKeySequence("Alt+F4"), self.close),
        ):
            action = QAction(title, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            menu.addAction(action)
            self.actions[key] = action

        self.name_edit.textChanged.connect(self._edited)
        self.cycle_combo.currentTextChanged.connect(self._edited)
        self._activate(Project(), None)

    def project(self) -> Project:
        return Project(self.name_edit.text(), self.cycle_combo.currentText())

    def _edited(self) -> None:
        self.dirty = True
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.setWindowTitle(f"MotorSim — {self.name_edit.text()}{' *' if self.dirty else ''}")
        self.file_label.setText(f"Archivo: {self.path}" if self.path else "Sin archivo asociado")
        self.state_label.setText("Cambios pendientes" if self.dirty else "Sin cambios pendientes")

    def _activate(self, project: Project, path: Path | None) -> None:
        self.name_edit.setText(project.name)
        self.cycle_combo.setCurrentText(project.cycle)
        self.path = path
        self.dirty = False
        self._refresh_status()

    def _error(self, error: ProjectError) -> None:
        box = QMessageBox(QMessageBox.Icon.Critical, "MotorSim — Error", str(error), parent=self)
        box.addButton("Aceptar", QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def _ask_changes(self) -> str:
        box = QMessageBox(QMessageBox.Icon.Warning, "Cambios pendientes",
                          "¿Querés guardar los cambios del proyecto antes de continuar?", parent=self)
        save = box.addButton("Guardar", QMessageBox.ButtonRole.AcceptRole)
        discard = box.addButton("Descartar", QMessageBox.ButtonRole.DestructiveRole)
        cancel = box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        box.exec()
        if box.clickedButton() is save:
            return "save"
        if box.clickedButton() is discard:
            return "discard"
        return "cancel"

    def _can_leave(self) -> bool:
        if not self.dirty:
            return True
        choice = self._ask_changes()
        return choice == "discard" or (choice == "save" and self.save())

    def new_project(self) -> None:
        if self._can_leave():
            self._activate(Project(), None)

    def _choose_file(self, saving: bool) -> Path | None:
        dialog = QFileDialog(self, "Guardar proyecto como" if saving else "Abrir proyecto")
        # Diálogo Qt para mantener etiquetas en español en cualquier Windows.
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog)
        dialog.setNameFilters(["Proyectos JSON (*.json)", "Todos los archivos (*)"])
        dialog.setLabelText(QFileDialog.DialogLabel.LookIn, "Carpeta:")
        dialog.setLabelText(QFileDialog.DialogLabel.FileName, "Archivo:")
        dialog.setLabelText(QFileDialog.DialogLabel.FileType, "Tipo de archivo:")
        dialog.setLabelText(QFileDialog.DialogLabel.Accept, "Guardar" if saving else "Abrir")
        dialog.setLabelText(QFileDialog.DialogLabel.Reject, "Cancelar")
        if saving:
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            dialog.setDefaultSuffix("json")
            # La confirmación explícita también se usa en los tests.
            dialog.setOption(QFileDialog.Option.DontConfirmOverwrite)
            if self.path:
                dialog.selectFile(str(self.path))
        else:
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return Path(dialog.selectedFiles()[0]).absolute()
        return None

    def open_project(self) -> None:
        # Elegir y validar primero: cancelar o rechazar un archivo no altera
        # siquiera el estado pendiente, aunque después se decida guardar.
        path = self._choose_file(False)
        if path is None:
            return
        try:
            project = load_project(path)
        except ProjectError as exc:
            self._error(exc)
            return
        if self._can_leave():
            # Guardar antes de abrir puede haber actualizado ese mismo archivo.
            try:
                project = load_project(path)
            except ProjectError as exc:
                self._error(exc)
                return
            self._activate(project, path)

    def _confirm_overwrite(self, path: Path) -> bool:
        box = QMessageBox(QMessageBox.Icon.Warning, "Confirmar sobrescritura",
                          f"Ya existe «{path}». ¿Querés reemplazarlo?", parent=self)
        replace = box.addButton("Reemplazar", QMessageBox.ButtonRole.AcceptRole)
        cancel = box.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(cancel)
        box.setEscapeButton(cancel)
        box.exec()
        return box.clickedButton() is replace

    def _save_to(self, path: Path) -> bool:
        try:
            save_project(path, self.project())
        except ProjectError as exc:
            self._error(exc)
            return False
        self.path = path
        self.dirty = False
        self._refresh_status()
        return True

    def save(self) -> bool:
        return self._save_to(self.path) if self.path else self.save_as()

    def save_as(self) -> bool:
        try:
            self.project().validate()
        except ProjectError as exc:
            self._error(exc)
            return False
        path = self._choose_file(True)
        if path is None:
            return False
        if path.exists() and not self._confirm_overwrite(path):
            return False
        return self._save_to(path)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._can_leave():
            event.accept()
        else:
            event.ignore()
