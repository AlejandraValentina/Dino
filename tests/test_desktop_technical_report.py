import hashlib,json
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog, QPushButton
from PySide6.QtCore import Qt
from unittest.mock import patch

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import new_design_project
from motorsim.desktop.technical_report import render_technical_report,render_study_comparison_report


APP = QApplication.instance() or QApplication([])


def test_cross_study_report_preserves_exact_provenance_and_evidence_boundaries():
    comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":"a"*64,"scientific_validation":"NOT_CLAIMED",
        "notice":"No interpolation; no aggregate effect.","studies":[
            {"study_id":"study <A>","source_project_id":"project-a","manifest_path":"a.study.json",
             "manifest_sha256":"b"*64,"baseline_engine_identity_sha256":"a"*64,
             "parameter":{"label":"Escape"},"manifest":{"study_id":"study <A>"},"points":[
                {"index":0,"value":83.123456789,"unit":"mm","rpm":3000,"status":"COMPLETE",
                 "classification":"PERIOD_1","periodicity":"PERIOD_1","cycles_completed":20,
                 "source_run_id":"run-a","engine_identity_sha256":"c"*64,"identity_sha256":"d"*64,
                 "result_sha256":"e"*64,"result_artifact_sha256":"f"*64,
                 "run_directory":"C:/artifacts/run-a","source_verified":True,
                 "metrics":{"brake_power":10.0,"brake_torque":None,"BMEP":None}}]},
            {"study_id":"study B","source_project_id":"project-b","manifest_path":"b.study.json",
             "manifest_sha256":"1"*64,"baseline_engine_identity_sha256":"a"*64,
             "parameter":{"label":"Escape"},"manifest":{"study_id":"study B"},"points":[
                {"index":0,"value":85.987654321,"unit":"mm","rpm":3000,"status":"COMPLETE",
                 "classification":"PERIOD_1","periodicity":"PERIOD_1","cycles_completed":20,
                 "source_run_id":"run-b","engine_identity_sha256":"2"*64,"identity_sha256":"3"*64,
                 "result_sha256":"4"*64,"result_artifact_sha256":"5"*64,
                 "run_directory":"C:/artifacts/run-b","source_verified":True,
                 "metrics":{"brake_power":12.5,"brake_torque":None,"BMEP":None}}]}],
        "pairs":[{"study_a":"study <A>","point_a":{"run_id":"run-a"},"study_b":"study B",
            "point_b":{"run_id":"run-b"},"rpm":3000,
            "pairing":"EXACT_RPM_AND_OPERATING_CONTEXT",
            "metrics":{"brake_power":{"a":10.0,"b":12.5,"delta":2.5},
                "brake_torque":{"a":None,"b":None,"delta":None},"BMEP":{"a":None,"b":None,"delta":None}}}],
        "unpaired":[{"study_id":"study B","reason":"Condiciones informadas incompatibles: total_finite_volume_cells.",
            "point":{"run_id":"run-other","rpm":4000,"classification":"MAX_CYCLES_NONCONVERGED",
                "periodicity":"INSUFFICIENT_CYCLES","engine_identity_sha256":"7"*64}}]}
    html=render_study_comparison_report(comparison)
    assert "study &lt;A&gt;" in html and "2.5 kW" in html
    assert "C:/artifacts/run-a" in html and "a"*64 in html and "f"*64 in html
    assert "Puntos sin contraparte" in html and "total_finite_volume_cells" in html
    assert "no se interpolan, ajustan ni agregan" in html
    assert "NOT_CLAIMED" in html


def test_results_page_exports_selected_cross_study_comparison(tmp_path):
    context=DesktopContext(new_design_project("cross-study-report-export"))
    page=ResultsPage(context)
    page.study_comparison={"schema":"DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1",
        "baseline_engine_identity_sha256":"a"*64,"scientific_validation":"NOT_CLAIMED",
        "notice":"Exact comparisons only.","studies":[
            {"study_id":"A","source_project_id":"p","manifest_path":"a.study.json",
             "manifest_sha256":"b"*64,"baseline_engine_identity_sha256":"a"*64,
             "parameter":{"label":"Escape"},"manifest":{"study_id":"A"},"points":[]},
            {"study_id":"B","source_project_id":"p","manifest_path":"b.study.json",
             "manifest_sha256":"c"*64,"baseline_engine_identity_sha256":"a"*64,
             "parameter":{"label":"Escape"},"manifest":{"study_id":"B"},"points":[]}],
        "pairs":[],"unpaired":[]}
    output=tmp_path/"cross-study-report.html"
    with patch("motorsim.desktop.results_page.QFileDialog.getSaveFileName",return_value=(str(output),"HTML")):
        assert page.export_study_comparison() is True
    html=output.read_text(encoding="utf-8")
    assert "Comparación de estudios paramétricos" in html and "A" in html and "B" in html
    page.close();APP.processEvents()


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
                    "run_id":"study-p00","source_run_id":"historical-run-00",
                    "historical_source_project_id":"source-project",
                    "run_directory":"C:/artifacts/historical-run-00",
                    "result_sha256":"e"*64,"result_artifact_sha256":"f"*64,
                    "reused_verified":True,
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
    assert "historical-run-00" in html and "source-project" in html
    assert "C:/artifacts/historical-run-00" in html and "e"*64 in html and "f"*64 in html
    assert "Artefacto SHA-256" in html and "Reuso verificado" in html
    assert "no implica periodicidad ni validación científica" in html
    assert "Manifiesto paramétrico original adjunto (JSON)" in html


def test_rpm_envelope_report_retains_exact_grid_states_and_hash_bound_sources(tmp_path):
    sweep_path=tmp_path/"series.json"
    sweep_raw=json.dumps({"schema":"DINO_POWER_CURVE_V1","synthetic":True},
        sort_keys=True,separators=(",",":")).encode()
    sweep_path.write_bytes(sweep_raw);sweep_hash=hashlib.sha256(sweep_raw).hexdigest()
    points=[]
    for index,(design_index,value,rpm,state,periodicity) in enumerate((
        (0,83.1234567890123,3000,"MAX_CYCLES_NONCONVERGED","INSUFFICIENT_CYCLES"),
        (0,83.1234567890123,4000,"MAX_CYCLES_NONCONVERGED","INSUFFICIENT_CYCLES"),
        (1,88.9876543210987,3000,"NOT_STARTED","NOT_EVALUATED"),
        (1,88.9876543210987,4000,"CANCELLED_CHECKPOINTED","NOT_EVALUATED"),
    )):
        points.append({"index":index,"design_index":design_index,"value":value,"unit":"mm","rpm":rpm,
            "status":"COMPLETE" if state.startswith("MAX_") else state,"classification":state,
            "periodicity":periodicity,"cycles_completed":1 if state.startswith("MAX_") else 0,
            "run_id":f"synthetic-envelope-p{index:02d}","engine_identity_sha256":str(design_index+1)*64,
            "result_artifact_sha256":hashlib.sha256(f"result-{index}".encode()).hexdigest(),
            "run_directory":str(tmp_path/f"run-{index}"),"sweep_manifest":str(sweep_path),
            "sweep_manifest_sha256":sweep_hash})
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","design_method":"RPM_ENVELOPE_V1",
        "study_id":"synthetic-rpm-envelope-report","project_id":"synthetic-report-project",
        "parameter":{"id":"exhaust:length","label":"Longitud del escape","unit":"mm"},
        "values":[83.1234567890123,88.9876543210987],"rpms":[3000,4000],
        "max_cycles":1,"point_budget_seconds":45,"total_budget_seconds":180,
        "memory_limit_mib":512,"status":"COMPLETE","scientific_validation":"NOT_CLAIMED",
        "groups":[{"index":0,"status":"COMPLETE","sweep_manifest":str(sweep_path),
                    "sweep_manifest_sha256":sweep_hash},
                   {"index":1,"status":"PARTIAL","sweep_manifest":str(sweep_path),
                    "sweep_manifest_sha256":sweep_hash}],"points":points}
    manifest_path=tmp_path/"envelope.study.json"
    manifest_path.write_text(json.dumps(manifest,sort_keys=True),encoding="utf-8")
    html=render_technical_report({"points":[_row("synthetic",3000,None,
        classification="MAX_CYCLES_NONCONVERGED",periodicity="INSUFFICIENT_CYCLES")],
        "experimental_validation":"NOT_PERFORMED"},source_kind="EXPLORATORY",
        design_study_manifest=manifest,design_study_manifest_path=manifest_path,generated_at="fixed")
    assert "Envolvente geometría × RPM" in html and "RPM_ENVELOPE_V1" in html
    assert "RPM exactas: 3000, 4000" in html and "83.1235 mm" in html and "88.9877 mm" in html
    assert "Límite de ciclos · no convergida" in html and "Ciclos insuficientes" in html
    assert "synthetic-envelope-p00" in html and str(sweep_path) in html and sweep_hash in html
    assert "sin validación científica" in html.lower() or "no declarada" in html.lower()
    assert "No se interpolan puntos" in html
    sweep_path.write_text("{changed:true}",encoding="utf-8")
    import pytest
    with pytest.raises(ValueError,match="hash del manifiesto de barrido"):
        render_technical_report({"points":[_row("synthetic",3000,None)]},source_kind="EXPLORATORY",
            design_study_manifest=manifest,design_study_manifest_path=manifest_path,generated_at="fixed")


def test_rpm_envelope_report_rejects_stale_or_unlinked_manifest(tmp_path):
    import pytest
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","design_method":"RPM_ENVELOPE_V1",
        "study_id":"stale-envelope","values":[],"rpms":[],"groups":[],"points":[]}
    path=tmp_path/"stale.study.json";path.write_text(json.dumps({**manifest,"study_id":"changed"}),encoding="utf-8")
    with pytest.raises(ValueError,match="manifiesto RPM cambió"):
        render_technical_report({"points":[_row("synthetic",3000,None)]},source_kind="EXPLORATORY",
            design_study_manifest=manifest,design_study_manifest_path=path)
    with pytest.raises(ValueError,match="necesita la ruta del manifiesto"):
        render_technical_report({"points":[_row("synthetic",3000,None)]},source_kind="EXPLORATORY",
            design_study_manifest=manifest)


def test_results_page_exports_hash_bound_rpm_envelope_report(tmp_path):
    context=DesktopContext(new_design_project("rpm-envelope-report-ui"))
    page=ResultsPage(context)
    manifest={"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","design_method":"RPM_ENVELOPE_V1",
        "study_id":"synthetic-rpm-envelope-ui","project_id":context.project["project_id"],
        "baseline_engine_identity_sha256":"a"*64,"parameter":{"label":"Largo de escape","unit":"mm"},
        "values":[83.123456789],"rpms":[3000],"status":"PARTIAL","scientific_validation":"NOT_CLAIMED",
        "groups":[],"points":[{"index":0,"design_index":0,"value":83.123456789,"unit":"mm","rpm":3000,
            "status":"COMPLETE","classification":"MAX_CYCLES_NONCONVERGED",
            "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":1,"run_id":"synthetic-envelope-run",
            "engine_identity_sha256":"b"*64,"result_artifact_sha256":"c"*64}]}
    manifest_path=tmp_path/"envelope.study.json";manifest_path.write_text(json.dumps(manifest),encoding="utf-8")
    page.dataset={"schema":"DINO_EXPLORATORY_COMPARISON_V1","points":[_row("synthetic",3000,None,
        classification="MAX_CYCLES_NONCONVERGED",periodicity="INSUFFICIENT_CYCLES")],
        "experimental_validation":"NOT_PERFORMED"}
    page.source_kind="EXPLORATORY";page.design_study_manifest=manifest;page.design_study_manifest_path=manifest_path
    page.variants.addItem("synthetic");page.variants.item(0).setCheckState(Qt.CheckState.Checked)
    destination=tmp_path/"envelope-report.html"
    with patch.object(QFileDialog,"getSaveFileName",return_value=(str(destination),"HTML")):
        assert page.export_technical_report()
    report=destination.read_text(encoding="utf-8")
    assert "RPM_ENVELOPE_V1" in report and "synthetic-envelope-run" in report
    assert "Límite de ciclos" in report and "Ciclos insuficientes" in report
    page.close();APP.processEvents()


def test_report_rejects_unknown_parametric_manifest_schema():
    import pytest
    with pytest.raises(ValueError, match="esquema.*reconocido"):
        render_technical_report({"points": [_row("A", 3000, 1.0)]},
            source_kind="EXPLORATORY", design_study_manifest={"schema": "unknown"})


def test_report_shows_factorial_values_without_derived_effects():
    report=render_technical_report({"points":[_row("factorial",3000,None,
        classification="MAX_CYCLES_NONCONVERGED")],"experimental_validation":"NOT_PERFORMED"},
        source_kind="EXPLORATORY",generated_at="fixed",design_study_manifest={
            "schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"factorial-synthetic",
            "status":"PARTIAL","parameter":{"label":"2×2 · top × volume"},
            "points":[{"index":3,"status":"COMPLETE","engine_identity_sha256":"d"*64,
                "factor_values":[{"label":"Transfer top","value":39.1,"unit":"mm"},
                                 {"label":"Crankcase volume","value":355.0,"unit":"cm³"}]}]})
    assert "Transfer top=39.1 mm" in report
    assert "Crankcase volume=355 cm³" in report
    assert "interaction effect" not in report.lower()
    assert "no recalculan el solver" in report


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
    assert "Estudio paramétrico asociado" in destination.read_text(encoding="utf-8")
    assert "ui-study" in destination.read_text(encoding="utf-8")
    assert page.findChild(QPushButton, "exportTechnicalReport") is not None
    page.close()
