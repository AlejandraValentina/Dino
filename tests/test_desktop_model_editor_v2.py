"""Synthetic UI contracts for engineering editing; no solver campaign."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import json,math,tempfile,unittest
from copy import deepcopy
from pathlib import Path
import desktop_qsettings_isolation
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QRectF,QPoint
from PySide6.QtTest import QTest
from motorsim.desktop.app import DinoDesktopWindow
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.services import new_design_project
from motorsim.desktop.engine_page import EnginePage
from motorsim.desktop.exhaust_page import ExhaustPage
from motorsim.desktop.model_diagrams import PortTimingView,can_edit_opening,top_from_opening
from motorsim.two_stroke_ports import TwoStrokePortSet
from motorsim.kinematics import piston_position
from motorsim.engine_configuration import identity
from motorsim.engine_project import save_project,load_project

APP=QApplication.instance() or QApplication([])


class ModelEditorTests(unittest.TestCase):
    def setUp(self):self.context=DesktopContext(new_design_project())
    def port_set(self):return TwoStrokePortSet.from_dict(self.context.engine()['native_configuration']['port_binding']['port_set'])

    def test_disconnected_intervals_are_not_reported_as_one_duration(self):
        from types import SimpleNamespace
        port=SimpleNamespace(id='synthetic-multiple-intervals',role='exhaust')
        class Source:
            ports=[port]
            def event_angles(self,p):return (0,30,60,90,120,180,360)
            def area_at(self,p,angle):return 10 if 30<angle<60 or 90<angle<120 else 0
        source=Source()
        self.assertEqual(EnginePage._area_timing(source,port),(None,None,None))
        view=PortTimingView();view.set_events(source)
        self.assertEqual(view.rows[0]['intervals'],[(30,60),(90,120)])

    def test_inverse_is_restricted_and_reproduces_backend_events(self):
        ports=self.port_set();port=next(p for p in ports.ports if can_edit_opening(p))
        for angle in (45.,95.,130.):
            top=top_from_opening(port,ports.stroke_mm,ports.rod_length_mm,angle)
            p=deepcopy(port.to_dict());p['top_mm']=top
            candidate=type(port).from_dict(p)
            self.assertTrue(any(abs(a-angle)<1e-8 for a in ports.event_angles(candidate)))
            self.assertAlmostEqual(top,piston_position(ports.stroke_mm,ports.rod_length_mm,angle))
        for value in (0.,180.,200.,float('nan')):
            with self.assertRaises(ValueError):top_from_opening(port,ports.stroke_mm,ports.rod_length_mm,value)
        intake=next(p for p in ports.ports if p.role=='intake')
        self.assertFalse(can_edit_opening(intake))
        with self.assertRaises(ValueError):top_from_opening(intake,ports.stroke_mm,ports.rod_length_mm,95)

    def test_degrees_table_geometry_timeline_apply_and_persistence_agree(self):
        page=EnginePage(self.context);ports=self.port_set();row=next(i for i,p in enumerate(ports.ports) if can_edit_opening(p))
        before=identity(self.context.engine())
        page.ports.item(row,7).setText('105')
        expected=piston_position(ports.stroke_mm,ports.rod_length_mm,105)
        self.assertAlmostEqual(float(page.ports.item(row,2).text()),expected,places=9)
        self.assertAlmostEqual(float(page.ports.item(row,8).text()),255,places=5)
        self.assertAlmostEqual(float(page.ports.item(row,9).text()),150,places=5)
        self.assertFalse(page.timing.item(row,1).flags() & Qt.ItemFlag.ItemIsEditable)
        self.assertTrue(any(page.port_areas.item(i,0).text()==ports.ports[row].id and page.port_areas.item(i,1).text()=='105' for i in range(page.port_areas.rowCount())))
        self.assertAlmostEqual(page.port_geometry.rows[row]['effective_top'],expected,places=9)
        intervals=next(p['intervals'] for p in page.port_timeline.rows if p['id']==ports.ports[row].id)
        self.assertAlmostEqual(min(a for a,b in intervals),105,places=7)
        self.assertAlmostEqual(max(b for a,b in intervals),255,places=7)
        self.assertEqual(identity(self.context.engine()),before)
        page.apply();self.assertNotEqual(identity(self.context.engine()),before)
        self.assertAlmostEqual(self.port_set().ports[row].top_mm,expected,places=9)
        after=self.port_set()
        self.assertEqual(after.ports[row].height_mm,ports.ports[row].height_mm)
        self.assertEqual(after.ports[row].width_mm,ports.ports[row].width_mm)
        for index,port in enumerate(ports.ports):
            if index!=row:self.assertEqual(after.ports[index].to_dict(),port.to_dict())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'synthetic.dino2t.json';save_project(path,self.context.project)
            self.assertEqual(load_project(path),self.context.project)
        committed=identity(self.context.engine());page.ports.item(row,7).setText('200');page.apply()
        self.assertIn('rechazada',page.validation.text().lower());self.assertEqual(identity(self.context.engine()),committed)
        page.refresh();self.assertIsNone(page._angle_error)
        exhaust=next(i for i,p in enumerate(self.port_set().ports) if p.role=='exhaust' and p.family=='rectangular_window')
        page.ports.item(exhaust,6).setText('1')
        self.assertFalse(page.ports.item(exhaust,7).flags() & Qt.ItemFlag.ItemIsEditable)

    def test_geometry_preview_is_not_a_silent_project_write(self):
        page=EnginePage(self.context);before=identity(self.context.engine())
        page.controls['bore_mm'].setValue(57)
        self.assertEqual(page.cylinder_diagram.bore,57)
        self.assertIn('BORRADOR SIN APLICAR',page.summary.text())
        self.assertIn('57',page.summary.text());self.assertEqual(identity(self.context.engine()),before)
        page.controls['rod_length_mm'].setValue(20)
        self.assertIn('inválido',page.validation.text())
        page.apply();self.assertEqual(identity(self.context.engine()),before)

    def test_component_selector_has_no_hidden_duplicate_navigation(self):
        window=DinoDesktopWindow(self.context.project);window.resize(964,641);window.show();APP.processEvents()
        self.assertEqual(window.component_nav.currentIndex(),8)
        self.assertTrue(window.model_selector.isVisible());self.assertFalse(window.component_nav.isVisible())
        for section,inner in ((0,0),(7,5),(6,4),(1,1),(8,6),(9,7)):
            window.model_selector.setCurrentIndex(window.model_selector.findData(section));APP.processEvents()
            self.assertEqual(window.pages[0].component_tabs.currentIndex(),inner)
            button=window.pages[0].apply_button
            self.assertLessEqual(button.mapTo(window,QPoint(0,0)).y()+button.height(),window.height())
        window.close()

    def test_exhaust_shared_frame_selection_and_dimensions_stay_synchronized(self):
        page=ExhaustPage(self.context);page.resize(920,600);page.show();APP.processEvents()
        original=deepcopy(page.profile.sections);overlay=deepcopy(original);overlay[0]['length_mm']+=20
        page.profile.set_sections(original,overlay=overlay)
        rect=QRectF(42,14,800,170);x,scale=page.profile.frame(rect)
        self.assertAlmostEqual(x+sum(s['length_mm'] for s in overlay)*scale,rect.right())
        self.assertLess(x+sum(s['length_mm'] for s in original)*scale,rect.right())
        page.table.setCurrentCell(2,1);self.assertEqual(page.profile.selected_section,2)
        page.table.item(2,1).setText('220')
        self.assertEqual(page.profile.sections[2]['length_mm'],220)
        self.assertIn('220',page.selection_notice.text())
        page.profile.section_selected.emit(0);self.assertEqual(page.table.currentRow(),0)
        page.close()
