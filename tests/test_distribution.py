"""Arranque y distribución: dobles, sin integraciones numéricas."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PySide6.QtCore import QProcess
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from motorsim.runtime import worker_command,build_info,diagnostic,resource,APP_VERSION
from motorsim.window import MainWindow


class DistributionTests(unittest.TestCase):
    def test_source_command_absolute_and_cwd_independent(self):
        executable,args,cwd=worker_command()
        self.assertTrue(Path(executable).is_absolute())
        self.assertEqual(args,['-u','-m','motorsim.reference_run'])
        self.assertTrue((Path(cwd)/'motorsim/reference_run.py').is_file())
        self.assertTrue(resource('theme.qss').is_file());self.assertTrue(resource('ayuda.txt').is_file())

    def test_frozen_worker_unicode_missing_and_found(self):
        with tempfile.TemporaryDirectory(prefix='MotorSim á ') as root:
            with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(Path(root)/'MotorSim.exe')):
                with self.assertRaisesRegex(FileNotFoundError,'carpeta completa'):worker_command()
                (Path(root)/'MotorSimWorker.exe').write_bytes(b'fixture; no executable')
                executable,args,cwd=worker_command()
                self.assertEqual(Path(executable),(Path(root)/'MotorSimWorker.exe').resolve())
                self.assertEqual(args,[]);self.assertEqual(Path(cwd),Path(root).resolve())

    def test_build_identity_and_diagnostics_outside_resources(self):
        self.assertEqual(build_info()['app_version'],APP_VERSION)
        with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,LOCALAPPDATA=root):
            first=diagnostic('controlado uno');second=diagnostic('controlado dos')
            self.assertNotEqual(first,second);self.assertIn('controlado uno',first.read_text(encoding='utf-8'))
            self.assertEqual(first.parent,Path(root)/'MotorSim/Diagnostico')

    def test_worker_imports_no_qt(self):
        code='import sys;import motorsim.reference_run;assert not any(k.startswith(("PySide6","shiboken6")) for k in sys.modules)'
        subprocess.run([sys.executable,'-c',code],check=True)


class DistributionWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_absent_or_failed_worker_preserves_coherent_state(self):
        w=MainWindow();v=w.simulation_view
        try:
            with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,LOCALAPPDATA=root):
                with patch('motorsim.simulation_view.worker_command',side_effect=FileNotFoundError('Falta auxiliar')):
                    v.start(output=Path(root)/'absent')
                self.assertFalse(v.active);self.assertIn('Falta auxiliar',v.error_label.text())
                with patch('motorsim.simulation_view.worker_command',return_value=(str(Path(root)/'missing.exe'),[],root)):
                    v.start(output=Path(root)/'failure')
                for _ in range(100):
                    if not v.active:break
                    QTest.qWait(10)
                self.assertFalse(v.active);self.assertIsNone(v.result)
                self.assertTrue(v.run_button.isEnabled());self.assertFalse(v.cancel_button.isEnabled())
                self.assertIn('auxiliar de cálculo',v.error_label.text())
                self.assertEqual(len(list((Path(root)/'MotorSim/Diagnostico').glob('*.txt'))),1)
        finally:w.dirty=False;w.close();w.deleteLater()


if __name__=='__main__':unittest.main()
