"""Pruebas de widgets sin pantalla; no sustituyen el recorrido manual Windows."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QFileDialog, QLineEdit, QMessageBox

from motorsim.project import Project, ProjectError
from motorsim.storage import load_project, save_project
from motorsim.window import MainWindow


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "original.json"
        self.copy = self.path.with_name("copia.json")
        self.window = MainWindow()
        self.window.show()
        self.app.processEvents()
        self.error_patch = patch.object(self.window, "_error")
        self.error = self.error_patch.start()
        self.addCleanup(self.error_patch.stop)

    def tearDown(self):
        self.window.dirty = False
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def edit(self):
        self.window.name_edit.selectAll()
        QTest.keyClicks(self.window.name_edit, "Motor editado")
        self.window.cycle_combo.setCurrentText("4T")

    def snapshot(self):
        return self.window.project(), self.window.path, self.window.dirty

    def test_initial_window_and_edit(self):
        self.assertEqual(self.snapshot(), (Project(), None, False))
        self.assertEqual([self.window.cycle_combo.itemText(i) for i in range(2)], ["2T", "4T"])
        self.assertEqual(self.window.cycle_combo.count(), 2)
        self.assertFalse(self.window.cycle_combo.isEditable())
        self.assertIn("simulación no disponible", self.window.notice.text())
        self.assertIn("Sin archivo", self.window.file_label.text())
        self.edit()
        self.assertTrue(self.window.dirty)
        self.assertIn("*", self.window.windowTitle())
        self.assertEqual(self.window.state_label.text(), "Cambios pendientes")

    def test_save_as_keeps_original_and_changes_active_path(self):
        self.edit()
        with patch.object(self.window, "_choose_file", return_value=self.path):
            self.assertTrue(self.window.save())
        original = self.path.read_bytes()
        self.window.name_edit.setText("Copia áéíóú")
        with patch.object(self.window, "_choose_file", return_value=self.copy):
            self.assertTrue(self.window.save_as())
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(load_project(self.copy), self.window.project())
        self.assertEqual(self.window.path, self.copy)
        self.assertFalse(self.window.dirty)
        self.window.name_edit.setText("Guardar en la ruta activa")
        with patch.object(self.window, "_choose_file") as choose:
            self.assertTrue(self.window.save())
            choose.assert_not_called()
        self.assertEqual(load_project(self.copy).name, "Guardar en la ruta activa")

    def test_save_cancel_overwrite_reject_and_failure_preserve_state(self):
        save_project(self.path, Project())
        self.window._activate(Project(), self.path)
        self.edit()
        original = self.path.read_bytes()
        before = self.snapshot()
        with patch.object(self.window, "_choose_file", return_value=None):
            self.assertFalse(self.window.save_as())
        self.assertEqual(self.snapshot(), before)
        with patch.object(self.window, "_choose_file", return_value=self.path):
            with patch.object(self.window, "_confirm_overwrite", return_value=False) as confirm:
                self.assertFalse(self.window.save_as())
                confirm.assert_called_once_with(self.path)
        self.assertEqual(self.snapshot(), before)
        with patch("motorsim.storage.os.replace", side_effect=PermissionError("Acceso denegado")):
            self.assertFalse(self.window.save())
            with patch.object(self.window, "_choose_file", return_value=self.copy):
                self.assertFalse(self.window.save_as())
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertFalse(self.copy.exists())
        self.error.assert_called()

    def test_overwrite_accepted(self):
        save_project(self.path, Project())
        self.edit()
        with patch.object(self.window, "_choose_file", return_value=self.path):
            with patch.object(self.window, "_confirm_overwrite", return_value=True):
                self.assertTrue(self.window.save_as())
        self.assertEqual(load_project(self.path), self.window.project())

    def test_invalid_name_preserves_edit_and_path(self):
        for name in ("", "   "):
            self.window.name_edit.setText(name)
            before = self.snapshot()
            with patch.object(self.window, "_choose_file") as choose:
                self.assertFalse(self.window.save())
                choose.assert_not_called()
            self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.error.call_count, 2)

    def test_open_cancel_invalid_and_unreadable_preserve_pending(self):
        self.edit()
        before = self.snapshot()
        self.path.write_text("malformado", encoding="utf-8")
        for path in (None, self.path, self.copy):
            with self.subTest(path=path):
                with patch.object(self.window, "_choose_file", return_value=path):
                    with patch.object(self.window, "_ask_changes", return_value="discard"):
                        self.window.open_project()
                self.assertEqual(self.snapshot(), before)

    def test_cancel_new_open_exit_and_window_close(self):
        save_project(self.path, Project("Otro", "2T"))
        self.edit()
        before = self.snapshot()
        with patch.object(self.window, "_ask_changes", return_value="cancel"):
            self.window.actions["new"].trigger()
            with patch.object(self.window, "_choose_file", return_value=self.path):
                self.window.actions["open"].trigger()
            self.window.actions["exit"].trigger()
            self.assertFalse(self.window.close())
        self.assertTrue(self.window.isVisible())
        self.assertEqual(self.snapshot(), before)

    def test_discard_new_open_and_close(self):
        self.edit()
        with patch.object(self.window, "_ask_changes", return_value="discard"):
            self.window.new_project()
            self.assertEqual(self.snapshot(), (Project(), None, False))
            self.edit()
            other = Project("Motor á", "4T")
            save_project(self.path, other)
            with patch.object(self.window, "_choose_file", return_value=self.path):
                self.window.open_project()
            self.assertEqual(self.snapshot(), (other, self.path, False))
            self.edit()
            self.assertTrue(self.window.close())

    def test_save_before_new_open_and_close(self):
        for operation in ("new", "open", "close"):
            with self.subTest(operation=operation):
                self.window._activate(Project(), self.path)
                self.edit()
                edited = self.window.project()
                save_project(self.copy, Project("Otro", "2T"))
                with patch.object(self.window, "_ask_changes", return_value="save"):
                    if operation == "new":
                        self.window.new_project()
                        self.assertEqual(self.window.project(), Project())
                    elif operation == "open":
                        with patch.object(self.window, "_choose_file", return_value=self.copy):
                            self.window.open_project()
                        self.assertEqual(self.window.project(), Project("Otro", "2T"))
                    else:
                        self.assertTrue(self.window.close())
                self.assertEqual(load_project(self.path), edited)

    def test_cancelled_or_failed_save_blocks_transitions(self):
        save_project(self.path, Project("Abrir", "2T"))
        self.edit()
        before = self.snapshot()
        for failed in (False, True):
            with patch.object(self.window, "_ask_changes", return_value="save"):
                with patch.object(self.window, "_choose_file", return_value=self.path if failed else None):
                    with patch.object(self.window, "_confirm_overwrite", return_value=True):
                        with patch("motorsim.window.save_project", side_effect=ProjectError("Fallo")):
                            self.window.new_project()
                            self.assertFalse(self.window.close())
                with patch.object(self.window, "_choose_file", side_effect=[self.path, None]):
                    self.window.open_project()
            self.assertEqual(self.snapshot(), before)
            self.assertTrue(self.window.isVisible())

    def test_open_same_file_after_save_uses_saved_data(self):
        save_project(self.path, Project())
        self.window._activate(Project(), self.path)
        self.edit()
        edited = self.window.project()
        with patch.object(self.window, "_choose_file", return_value=self.path):
            with patch.object(self.window, "_ask_changes", return_value="save"):
                self.window.open_project()
        self.assertEqual(self.snapshot(), (edited, self.path, False))

    def test_long_name_is_not_truncated_when_opened(self):
        project = Project("á" * 40000, "4T")
        save_project(self.path, project)
        with patch.object(self.window, "_choose_file", return_value=self.path):
            self.window.open_project()
        self.assertEqual(self.window.project(), project)

    def test_real_pending_dialog_buttons_and_escape(self):
        for caption, expected in (("Guardar", "save"), ("Descartar", "discard"),
                                  ("Cancelar", "cancel"), (None, "cancel")):
            def answer():
                box = self.app.activeModalWidget()
                if isinstance(box, QMessageBox):
                    if caption is None:
                        QTest.keyClick(box, Qt.Key.Key_Escape)
                    else:
                        for button in box.buttons():
                            if button.text() == caption:
                                QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            QTimer.singleShot(0, answer)
            with self.subTest(caption=caption):
                self.assertEqual(self.window._ask_changes(), expected)

    def test_real_file_dialogs_save_open_and_cancel(self):
        failures = []
        timeout = QTimer()
        timeout.setInterval(3000)

        def timed_out():
            failures.append("El diálogo no terminó dentro de 3 segundos")
            dialog = self.app.activeModalWidget()
            if dialog:
                dialog.reject()

        timeout.timeout.connect(timed_out)
        timeout.start()
        self.addCleanup(timeout.stop)

        def choose(path):
            def answer():
                dialog = self.app.activeModalWidget()
                try:
                    self.assertIsInstance(dialog, QFileDialog)
                    if path is None:
                        QTest.keyClick(dialog, Qt.Key.Key_Escape)
                    else:
                        filename = dialog.findChild(QLineEdit, "fileNameEdit")
                        filename.setFocus()
                        filename.selectAll()
                        QTest.keyClicks(filename, str(path))
                        QTest.keyClick(filename, Qt.Key.Key_Return)
                except Exception as exc:
                    failures.append(exc)
                    if dialog:
                        dialog.reject()
            QTimer.singleShot(100, answer)

        self.edit()
        # Se comprueba también que el diálogo agrega .json al destino.
        choose(self.path.with_suffix(""))
        self.assertTrue(self.window.save())
        self.assertTrue(self.path.exists())
        edited = self.window.project()
        self.window.new_project()
        choose(self.path)
        self.window.open_project()
        self.assertEqual(self.window.project(), edited)
        self.assertTrue(self.window.path.samefile(self.path))
        self.assertFalse(self.window.dirty)
        self.edit()
        before = self.snapshot()
        choose(None)
        self.window.open_project()
        self.assertEqual(self.snapshot(), before)
        choose(None)
        self.assertFalse(self.window.save_as())
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(failures, [])

    def test_real_overwrite_confirmation(self):
        for caption, expected in (("Reemplazar", True), ("Cancelar", False)):
            def answer():
                box = self.app.activeModalWidget()
                if isinstance(box, QMessageBox):
                    for button in box.buttons():
                        if button.text() == caption:
                            QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            QTimer.singleShot(100, answer)
            with self.subTest(caption=caption):
                self.assertEqual(self.window._confirm_overwrite(self.path), expected)
