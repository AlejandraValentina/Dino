"""Ventana de edición de la base de escritorio."""

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import (
    QAction, QCloseEvent, QColor, QIcon, QKeySequence, QPainter, QPainterPath,
    QPalette, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QSizePolicy,
    QPushButton, QToolBar, QVBoxLayout, QWidget,
)

from .project import Project, ProjectError
from .storage import load_project, save_project


class _FilePathLabel(QLabel):
    """Ruta abreviada en la barra; la ruta completa queda en la ayuda emergente."""

    def __init__(self) -> None:
        super().__init__()
        self.full_text = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setMinimumWidth(100)
        self.setTextFormat(Qt.TextFormat.PlainText)

    def set_path_text(self, text: str) -> None:
        self.full_text = text
        self.setToolTip(text)
        self.setAccessibleName(text)
        self._fit_text()

    def _fit_text(self) -> None:
        self.setText(self.fontMetrics().elidedText(
            self.full_text, Qt.TextElideMode.ElideLeft, self.contentsRect().width()))

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._fit_text()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.path: Path | None = None
        self.dirty = False
        self.resize(900, 520)
        self.setMinimumSize(680, 440)
        self.setWindowTitle("MotorSim")
        self.setStyleSheet(Path(__file__).with_name("theme.qss").read_text(encoding="utf-8"))
        palette = self.palette()
        for role, color in (
            (QPalette.ColorRole.Window, "#131b2e"),
            (QPalette.ColorRole.Base, "#060e20"),
            (QPalette.ColorRole.AlternateBase, "#171f33"),
            (QPalette.ColorRole.Text, "#dae2fd"),
            (QPalette.ColorRole.WindowText, "#dae2fd"),
            (QPalette.ColorRole.Button, "#171f33"),
            (QPalette.ColorRole.ButtonText, "#dae2fd"),
            (QPalette.ColorRole.Highlight, "#24415b"),
            (QPalette.ColorRole.HighlightedText, "#ffffff"),
        ):
            palette.setColor(role, QColor(color))
        self.setPalette(palette)

        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(2147483647)
        self.name_edit.setObjectName("project_name")
        self.cycle_group = QButtonGroup(self)
        self.cycle_group.setExclusive(True)
        self.cycle_buttons = {}
        self.file_label = _FilePathLabel()
        self.state_label = QLabel()
        self.state_label.setObjectName("projectState")
        self.notice = QLabel("Simulación no disponible")
        self.notice.setObjectName("availability")

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
            action.setToolTip(f"{title.replace('&', '')}  ·  {action.shortcut().toString()}")
            menu.addAction(action)
            self.actions[key] = action
            if key in ("open", "save_as"):
                menu.addSeparator()

        self._build_toolbar()
        self._build_workspace()
        self._build_statusbar()

        self.name_edit.textChanged.connect(self._edited)
        self.cycle_group.buttonToggled.connect(lambda button, checked: self._edited() if checked else None)
        self._activate(Project(), None)

    @staticmethod
    def _label(text: str, style: str = "") -> QLabel:
        label = QLabel(text)
        label.setObjectName(style)
        label.setWordWrap(True)
        return label

    def _build_toolbar(self) -> None:
        self.file_toolbar = QToolBar("Acciones de proyecto", self)
        self.file_toolbar.setMovable(False)
        self.file_toolbar.setFloatable(False)
        self.file_toolbar.setContextMenuPolicy(Qt.ContextMenuPolicy.PreventContextMenu)
        self.file_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.file_toolbar.setIconSize(QSize(16, 16))
        for key in ("new", "open", "save", "save_as"):
            self.actions[key].setIcon(self._action_icon(key))
            self.file_toolbar.addAction(self.actions[key])
            if key == "open":
                self.file_toolbar.addSeparator()
        self.file_toolbar.widgetForAction(self.actions["save"]).setObjectName("primaryAction")
        self.addToolBar(self.file_toolbar)

    @staticmethod
    def _action_icon(key: str) -> QIcon:
        """Pictogramas de archivo dibujados con Qt, sin recursos externos."""
        outlines = {
            "new": [((4, 2), (10, 2), (14, 6), (14, 16), (4, 16), (4, 2)),
                    ((10, 2), (10, 6), (14, 6))],
            "open": [((2, 8), (2, 4), (7, 4), (9, 6), (16, 6), (14, 15), (2, 15), (2, 8), (15, 8))],
            "save": [((3, 2), (13, 2), (16, 5), (16, 16), (3, 16), (3, 2)),
                     ((6, 2), (6, 7), (12, 7), (12, 2)), ((6, 16), (6, 11), (13, 11), (13, 16))],
            "save_as": [((4, 2), (10, 2), (14, 6), (14, 9)),
                        ((9, 16), (4, 16), (4, 2)), ((10, 2), (10, 6), (14, 6)),
                        ((10, 13), (16, 13)), ((13, 10), (13, 16))],
        }
        pixmap = QPixmap(36, 36)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(2, 2)
        painter.setPen(QPen(QColor("#002c47" if key == "save" else "#93ccff"), 1.2))
        for points in outlines[key]:
            path = QPainterPath()
            path.moveTo(*points[0])
            for point in points[1:]:
                path.lineTo(*point)
            painter.drawPath(path)
        painter.end()
        return QIcon(pixmap)

    def _build_workspace(self) -> None:
        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(36, 32, 36, 32)
        form = QWidget()
        form.setObjectName("projectForm")
        form.setMaximumWidth(560)
        form.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        content = QVBoxLayout(form)
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(10)
        content.addWidget(self._label("Proyecto", "pageTitle"))
        content.addSpacing(12)
        name_label = self._label("&Nombre del proyecto")
        name_label.setBuddy(self.name_edit)
        content.addWidget(name_label)
        content.addWidget(self.name_edit)
        content.addSpacing(10)
        type_label = self._label("&Tipo de motor")
        content.addWidget(type_label)
        cycle_row = QHBoxLayout()
        cycle_row.setSpacing(12)
        for cycle, title in (("2T", "2 tiempos (2T)"), ("4T", "4 tiempos (4T)")):
            button = QPushButton(title)
            button.setObjectName("cycleCard")
            button.setCheckable(True)
            button.setFixedHeight(64)
            button.setAccessibleName(title)
            button.setToolTip(f"Seleccionar {title}")
            button.setProperty("cycle", cycle)
            self.cycle_group.addButton(button)
            self.cycle_buttons[cycle] = button
            cycle_row.addWidget(button, 1)
        type_label.setBuddy(self.cycle_buttons["2T"])
        content.addLayout(cycle_row)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(form, 1)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()
        self.setCentralWidget(central)
        QWidget.setTabOrder(self.name_edit, self.cycle_buttons["2T"])
        QWidget.setTabOrder(self.cycle_buttons["2T"], self.cycle_buttons["4T"])

    def _build_statusbar(self) -> None:
        information = QWidget()
        layout = QHBoxLayout(information)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(14)
        layout.addWidget(self.file_label, 1)
        layout.addWidget(self.state_label)
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setObjectName("statusDivider")
        divider.setFixedHeight(14)
        layout.addWidget(divider)
        layout.addWidget(self.notice)
        self.statusBar().addPermanentWidget(information, 1)

    def project(self) -> Project:
        selected = self.cycle_group.checkedButton()
        return Project(self.name_edit.text(), selected.property("cycle") if selected else "2T")

    def _edited(self) -> None:
        self.dirty = True
        self._refresh_status()

    def _refresh_status(self) -> None:
        self.file_label.set_path_text(str(self.path) if self.path else "Sin archivo asociado")
        self.state_label.setText("Cambios pendientes" if self.dirty else
                                 ("Guardado" if self.path else "Sin cambios pendientes"))
        self.state_label.setProperty("pending", self.dirty)
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)
        for cycle, button in self.cycle_buttons.items():
            title = "2 tiempos (2T)" if cycle == "2T" else "4 tiempos (4T)"
            button.setText(f"✓  {title}" if button.isChecked() else title)

    def _activate(self, project: Project, path: Path | None) -> None:
        self.name_edit.setText(project.name)
        self.cycle_buttons[project.cycle].setChecked(True)
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
