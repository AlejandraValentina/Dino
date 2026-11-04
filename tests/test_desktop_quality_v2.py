"""Product presentation regressions; fixtures are synthetic and never solver evidence."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QTableWidgetItem
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtCore import QLocale

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.services import new_design_project
from motorsim.desktop.presentation import EngineeringNumberDelegate, display_value, format_number, state_label
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import load_results
from motorsim.desktop.widgets.run_history import RunHistoryWidget
from motorsim.desktop.widgets.context_bar import ContextBar
from motorsim.desktop.performance_curves import _visible_rpm_ticks

APP = QApplication.instance() or QApplication([])


def test_shared_presentation_formats_numbers_and_localizes_unknown_codes():
    assert format_number(12345.678901) == "12345.7"
    assert format_number(-0.000123456789) == "-0.000123457"
    assert state_label("MAX_CYCLES_NONCONVERGED") == "Límite de ciclos · no convergida"
    assert "UNTRANSLATED_INTERNAL_STATUS" not in state_label("UNTRANSLATED_INTERNAL_STATUS")
    delegate = EngineeringNumberDelegate()
    original = 1.234567890123
    assert delegate.displayText(original, QLocale()) == "1.23457"
    assert original == 1.234567890123


def test_status_chrome_uses_words_and_rpm_axis_keeps_clear_endpoints():
    context_bar=ContextBar()
    context_bar.set_context(new_design_project("ui-test"),None,False)
    assert context_bar.saved.text()=="Guardado"
    assert not any(mark in context_bar.saved.text() for mark in "□■✓✕●")
    ticks=_visible_rpm_ticks([1000,1300,1600,1900,2200,2500,2800,3100,3400,
                              3700,4000,4300,4600,4900,5000],120,1100)
    assert ticks[0][0]==1000 and ticks[-1][0]==5000
    assert all(b[1]-a[1]>=58 for a,b in zip(ticks,ticks[1:]))
    context_bar.close()


def test_nested_traceability_metadata_localizes_keys_and_preserves_original_value():
    text=display_value({"schema":"LEGACY_RESULT_V1","hard_failures":[],"warning_policy":
        "warnings require explanation and do not override physical validity"})
    assert 'Formato de datos' in text
    assert 'Fallos críticos' in text
    assert 'Política de advertencias' in text
    assert 'Las advertencias requieren explicación' in text
    assert 'warning_policy' not in text and 'hard_failures' not in text


def test_historical_result_origin_stays_distinct_when_open_project_changes():
    context = DesktopContext(new_design_project("active-project-before"))
    page = ResultsPage(context)
    row = {"project_id": "source-project-id", "variant_id": "Escape A", "rpm": 6000,
           "classification": "MAX_CYCLES_NONCONVERGED", "periodicity": "NOT_CONVERGED",
           "audit_status": "NOT_PERFORMED", "brake_power_status": "UNDEFINED",
           "brake_torque_status": "UNDEFINED", "BMEP_status": "UNDEFINED",
           "result_sha256": "a" * 64, "artifact_directory": "historical/run-1"}
    page.dataset = {"points": [row], "provenance": "synthetic presentation fixture",
                    "experimental_validation": "NOT_CLAIMED"}
    page.source_kind = "EXPLORATORY"
    page.show_point(row)
    original_active_project = context.project["project_id"]
    context.replace_project(new_design_project("active-project-after"))
    labels = [page.details.item(i, 0).text() for i in range(page.details.rowCount())]
    values = {page.details.item(i, 0).text(): page.details.item(i, 1).text()
              for i in range(page.details.rowCount())}
    assert values["Proyecto del resultado"] == "source-project-id"
    assert values["Proyecto abierto"] != original_active_project
    assert values["Resultado SHA-256"] == "a" * 64
    assert "MAX_CYCLES_NONCONVERGED" not in page.run_summary.text()
    assert "MAX_CYCLES_NONCONVERGED" not in " ".join(labels)
    page.close()


def _select_rows(widget, count=2):
    widget.table.setRowCount(count)
    selection = widget.table.selectionModel()
    for row in range(count):
        item = QTableWidgetItem(str(row))
        widget.table.setItem(row, 0, item)
        selection.select(widget.table.model().index(row, 0),
                         QItemSelectionModel.SelectionFlag.Select |
                         QItemSelectionModel.SelectionFlag.Rows)


def test_history_selection_explains_exact_ab_pair_and_different_rpm():
    context = DesktopContext(new_design_project())
    widget = RunHistoryWidget(context, "unused")
    widget.entries = [
        {"result_path": "a/result.json", "rpm": 6000, "variant": "A"},
        {"result_path": "b/result.json", "rpm": 6000, "variant": "B"},
    ]
    _select_rows(widget)
    widget._selection_changed()
    assert widget.compare_button.isEnabled()
    assert widget.compare_button.text() == "Comparar A/B · 6000 RPM"
    assert "Par A/B exacto" in widget.status.text()
    widget.entries[1]["rpm"] = 6500
    widget._selection_changed()
    assert widget.compare_button.text() == "Ver dos RPM"
    assert "no forman un par A/B exacto" in widget.status.text()
    widget.close()


def test_real_legacy_historical_result_opens_as_read_only_without_fabricated_metrics():
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    path = root / "results/engine-physics-v1/campaign-evidence-r3/engine_a_3000/result.json"
    data = load_results(path)
    point = data["points"][0]
    assert data["schema"] == "DINO_DESKTOP_LEGACY_HISTORICAL_SUMMARY_V1"
    assert point["rpm"] == 3000.0
    assert point["classification"] == "NO_CONVERGENCE_WITHIN_HORIZON"
    assert point["periodicity"] == "NOT_CONVERGED"
    assert point["brake_power"] is None and point["brake_torque"] is None
    assert point["result_sha256"] == data["source_sha256"]
    assert len(point["legacy_cycle_summary"]) == point["cycles_completed"]
    context=DesktopContext(new_design_project("traceability-open-project"))
    page=ResultsPage(context);page.dataset=data;page.source_kind="LEGACY_HISTORICAL"
    page.show_point(point)
    labels=[page.details.item(i,0).text() for i in range(page.details.rowCount())]
    visible=" ".join(labels+[page.details.item(i,1).text() for i in range(page.details.rowCount())])
    assert "hard_failures" not in visible and "warning_policy" not in visible and "schema" not in visible
    assert "Formato de datos" in visible and "Fallos críticos" in visible
    assert "Las advertencias requieren explicación" in visible
    assert data["source_sha256"] in visible
    page.close()
