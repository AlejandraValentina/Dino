"""Synthetic UI integration for the single Windows rc10 candidate."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile,unittest
from pathlib import Path
import desktop_qsettings_isolation
from PySide6.QtWidgets import QApplication,QTableWidget
from PySide6.QtCore import QPoint
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.services import new_design_project
from motorsim.engine_project import save_project,load_project
from motorsim.engine_configuration import identity

APP=QApplication.instance() or QApplication([])


class RC10IntegrationTests(unittest.TestCase):
    def test_intake_transfer_views_share_one_editor_without_losing_drafts(self):
        window=DinoDesktopWindow(new_design_project());window.show();APP.processEvents();page=window.pages[0]
        window.model_selector.setCurrentIndex(window.model_selector.findData(6));APP.processEvents()
        table=page.ducts
        intake=next(i for i in range(table.rowCount()) if table.item(i,1).text()=='intake')
        transfer=next(i for i in range(table.rowCount()) if table.item(i,1).text()=='transfer')
        self.assertFalse(table.isRowHidden(intake));self.assertTrue(table.isRowHidden(transfer))
        table.item(intake,2).setText('85')
        window.model_selector.setCurrentIndex(window.model_selector.findData(10));APP.processEvents()
        self.assertIs(table,page.ducts);self.assertTrue(table.isRowHidden(intake));self.assertFalse(table.isRowHidden(transfer))
        self.assertTrue(table.isVisible());self.assertEqual(table.item(intake,2).text(),'85')
        table.item(transfer,2).setText('52');page.apply()
        native=window.context.engine()['native_configuration'];ducts={d['id']:d for d in native['ducts']}
        self.assertAlmostEqual(ducts[page._duct_ids[intake]]['mesh']['faces'][-1],.085)
        self.assertAlmostEqual(ducts[page._duct_ids[transfer]]['mesh']['faces'][-1],.052)
        window.model_selector.setCurrentIndex(window.model_selector.findData(6));APP.processEvents()
        self.assertTrue(table.isVisible());self.assertFalse(table.isRowHidden(intake));self.assertTrue(table.isRowHidden(transfer))
        self.assertEqual(len(page.findChildren(QTableWidget,'editableIntakeTransferDucts')),1)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.json';save_project(path,window.context.project)
            self.assertEqual(identity(load_project(path)['base_engine']),identity(window.context.engine()))
        window.context.dirty=False;window.close()

    def test_compact_exhaust_keeps_actions_and_views_inside_window(self):
        window=DinoDesktopWindow(new_design_project());window.resize(960,630);window.show();APP.processEvents()
        window.model_selector.setCurrentIndex(window.model_selector.findData(2));APP.processEvents()
        page=window.pages[1]
        self.assertTrue(page.profile.isVisible())
        for index in range(3):
            page.view_tabs.setCurrentIndex(index);APP.processEvents()
            for button in (page.apply_button,page.save_current_button):
                self.assertTrue(button.isVisible())
                self.assertLessEqual(button.mapTo(window,QPoint()).y()+button.height(),window.height())
        page.view_tabs.setCurrentIndex(1);APP.processEvents();self.assertTrue(page.table.isVisible())
        page._toggle_stations();APP.processEvents();self.assertTrue(page.stations.isVisible())
        window.close()
