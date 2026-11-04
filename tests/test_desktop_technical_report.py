import hashlib
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QPushButton
from PySide6.QtCore import Qt
from unittest.mock import patch

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project
from motorsim.desktop.technical_report import render_technical_report


APP = QApplication.instance() or QApplication([])


def _row(variant, rpm, power, *, classification="PERIOD_1", periodicity=None):
    periodicity = periodicity or classification
    return {
        "project_id": "source-project", "variant_id": variant, "run_id": f"run-{variant}-{rpm}",
        "point_id": f"point-{variant}-{rpm}", "rpm": rpm,
        "classification": classification, "periodicity": periodicity,
        "audit_status": "PASS", "cycles_completed": 8,
        "brake_power": power, "brake_power_status": "DEFINED" if power is not None else "UNDEFINED",
        "brake_torque": 12.3456789012345 if power is not None else None,
        "brake_torque_status": "DEFINED" if power is not None else "UNDEFINED",
        "BMEP": 456.7890123456 if power is not None else None,
        "BMEP_status": "DEFINED" if power is not None else "UNDEFINED",
        "result_sha256": "a" * 64,
    }


def test_html_report_preserves_exact_records_and_evidence_boundaries(tmp_path):
    source = tmp_path / "source.json"
    source.write_text('{"fixture":"synthetic"}', encoding="utf-8")
    exact = 123.456789012345
    transient = _row("A", 6500, None, classification="MAX_CYCLES_NONCONVERGED")
    transient["transient_estimates"] = {"brake_power": 7.987654321098}
    dataset = {
        "schema": "DINO_EXPLORATORY_COMPARISON_V1",
        "provenance": "synthetic presentation fixture",
        "experimental_validation": "NOT_PERFORMED",
        "points": [_row("A", 6000, exact), _row("B", 6000, 125.0), transient,
                   _row("C", 6000, 999.0)],
    }
    html = render_technical_report(dataset, source_kind="EXPLORATORY",
        selected_variants=["A", "B"], source_path=source, active_project_id="active-project",
        generated_at="2026-11-04T12:00:00+00:00")
    assert "Corridas exploratorias" in html
    assert "no son mediciones experimentales" not in html
    assert "No realizada" in html
    assert str(exact) in html
    assert hashlib.sha256(source.read_bytes()).hexdigest() in html
    assert "active-project" in html and "source-project" in html
    assert "A → B" in html and "6000 RPM" in html
    assert "C →" not in html and "999.0" not in html
    assert "6500 RPM" in html and "estimación transitoria disponible" in html
    assert "MAX_CYCLES_NONCONVERGED" in html  # Preserved in the exact-source appendix.
    assert "Marcadores = puntos disponibles. No hay interpolación" in html
    assert "7.987654321098" in html  # Exact transient value remains in raw appendix.
    assert 'r="5"' in html


def test_report_marks_synthetic_historical_data_and_keeps_untranslated_text_safe():
    row = _row("<script>alert(1)</script>", 3000, 1.23456789012345)
    report = render_technical_report({"points": [row], "provenance": "HISTORICAL_IMPL2",
        "experimental_validation": "NOT_PERFORMED"}, source_kind="HISTORICAL_IMPL2",
        generated_at="fixed")
    assert "Datos históricos sintéticos" in report
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report
    assert "<script>alert(1)</script>" not in report
    assert "1.23456789012345" in report
    assert "no implica validación experimental" in report


def test_report_uses_declared_periodic_class_when_legacy_field_is_absent():
    row = _row("A", 5500, 120.000000000001)
    row["periodicity"] = None
    report = render_technical_report({"points": [row], "experimental_validation": "NOT_PERFORMED"},
        source_kind="HISTORICAL_IMPL2", generated_at="fixed")
    assert "<svg" in report
    assert 'aria-label="Potencia de freno por RPM"' in report
    assert "120.000000000001" in report


def test_report_embeds_parametric_manifest_and_preserves_study_provenance(tmp_path):
    manifest_path = tmp_path / "study.json"
    manifest_path.write_text('{"source":"synthetic fixture"}', encoding="utf-8")
    manifest = {
        "schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1", "study_id": "synthetic-study",
        "status": "PARTIAL", "rpm": 3000,
        "parameter": {"id": "port:primary-window:top_mm", "label": "Transfer top", "unit": "mm"},
        "points": [{"index": 0, "status": "COMPLETE", "value": 38.4086, "unit": "mm",
                    "engine_identity_sha256": "b" * 64,
                    "classification": "MAX_CYCLES_NONCONVERGED",
                    "periodicity": "INSUFFICIENT_CYCLES"}],
    }
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    html = render_technical_report({"points": [_row("Synthetic A", 3000, None,
        classification="MAX_CYCLES_NONCONVERGED")], "experimental_validation": "NOT_PERFORMED"},
        source_kind="EXPLORATORY", design_study_manifest=manifest,
        design_study_manifest_path=manifest_path, generated_at="fixed")
    assert "Estudio paramétrico asociado" in html
    assert "synthetic-study" in html and "Transfer top" in html and "38.4086 mm" in html
    assert "MAX_CYCLES_NONCONVERGED" in html and "INSUFFICIENT_CYCLES" in html
    assert digest in html and "b" * 64 in html
    assert "no implica periodicidad ni validación científica" in html
    assert "Manifiesto paramétrico original adjunto (JSON)" in html


def test_report_rejects_unknown_parametric_manifest_schema():
    import pytest
    with pytest.raises(ValueError, match="esquema.*reconocido"):
        render_technical_report({"points": [_row("A", 3000, 1.0)]},
            source_kind="EXPLORATORY", design_study_manifest={"schema": "unknown"})


def test_results_page_exports_report_using_current_variant_selection(tmp_path):
    context = DesktopContext(new_design_project("report-ui"))
    page = ResultsPage(context)
    page.dataset = {"schema": "DINO_EXPLORATORY_COMPARISON_V1", "provenance": "synthetic",
        "experimental_validation": "NOT_PERFORMED", "points": [_row("A", 6000, 2.0)]}
    page.source_kind = "EXPLORATORY"
    page.design_study_manifest = {"schema": "DINO_PARAMETRIC_DESIGN_STUDY_V1",
        "study_id": "ui-study", "status": "COMPLETE", "parameter": {"label": "Largo escape"},
        "points": [{"index": 0, "status": "COMPLETE", "value": 83.0, "unit": "mm",
                    "engine_identity_sha256": "c" * 64}]}
    page.variants.addItem("A")
    page.variants.item(0).setCheckState(Qt.CheckState.Checked)
    destination = tmp_path / "report.html"
    with patch.object(QFileDialog, "getSaveFileName", return_value=(str(destination), "")):
        assert page.export_technical_report()
    assert destination.is_file()
    assert "Informe técnico de resultados" in destination.read_text(encoding="utf-8")
    assert page.findChild(QPushButton, "exportTechnicalReport") is not None
    page.close()
