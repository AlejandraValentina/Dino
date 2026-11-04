from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from motorsim.desktop.context import DesktopContext
from motorsim.desktop.parametric_study_snapshot import (
    SNAPSHOT_SCHEMA, import_parametric_study_csv_snapshot,
)
from motorsim.desktop.results_page import ResultsPage
from motorsim.desktop.services import load_results, new_design_project

APP=QApplication.instance() or QApplication([])
_COLUMNS=("study_schema","study_id","project_id","design_method","manifest_path","manifest_sha256",
    "baseline_engine_identity_sha256","parameter_id","parameter_label","parameter_unit","point_index",
    "design_value","design_unit","factor_values_json","rpm","run_id","source_run_id","execution_status",
    "classification","periodicity","cycles_completed","engine_identity_sha256","identity_sha256",
    "result_sha256","result_artifact_sha256","run_directory","reused_verified","source_verified",
    "source_verification","brake_power_kw","brake_torque_nm","BMEP_kpa","scientific_validation")


def _rows():
    common={"study_schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":"snapshot-synthetic",
        "project_id":"SYNTHETIC project","design_method":"GEOMETRY_V1","manifest_path":"source.study.json",
        "manifest_sha256":"a"*64,"baseline_engine_identity_sha256":"","parameter_id":"exhaust:length",
        "parameter_label":"Escape · longitud","parameter_unit":"mm","rpm":"3000",
        "engine_identity_sha256":"b"*64,"identity_sha256":"c"*64,"result_sha256":"d"*64,
        "result_artifact_sha256":"","run_directory":"","reused_verified":"False",
        "source_verified":"False","source_verification":"NOT_LOADED","scientific_validation":"NOT_CLAIMED"}
    factors=json.dumps([{"parameter_id":"exhaust:length","label":"Escape · longitud","value":38.123456789012345,"unit":"mm"}],
        ensure_ascii=False,separators=(",",":"))
    first={**common,"point_index":"0","design_value":"38.123456789012345","design_unit":"mm",
        "factor_values_json":factors,"run_id":"synthetic-periodic","source_run_id":"synthetic-periodic",
        "execution_status":"COMPLETE","classification":"PERIOD_1","periodicity":"PERIOD_1",
        "cycles_completed":"4","brake_power_kw":"12.345678901234567","brake_torque_nm":"","BMEP_kpa":""}
    second={**common,"point_index":"1","design_value":"39.987654321","design_unit":"mm",
        "factor_values_json":"[]","run_id":"synthetic-transient","source_run_id":"synthetic-transient",
        "execution_status":"COMPLETE","classification":"MAX_CYCLES_NONCONVERGED",
        "periodicity":"INSUFFICIENT_CYCLES","cycles_completed":"2","brake_power_kw":"",
        "brake_torque_nm":"","BMEP_kpa":""}
    return [first,second]


def _write(path,rows=None,columns=_COLUMNS):
    with Path(path).open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows or _rows())


def test_imported_study_csv_is_exact_read_only_snapshot_with_historical_source_status(tmp_path):
    source=tmp_path/"snapshot.csv";_write(source)
    data=import_parametric_study_csv_snapshot(source)
    assert data["schema"]==SNAPSHOT_SCHEMA
    assert data["snapshot"]["read_only"] is True
    assert data["snapshot"]["source_verification_time"]=="VERIFIED_AT_EXPORT_ONLY"
    assert data["snapshot"]["csv_sha256"]==hashlib.sha256(source.read_bytes()).hexdigest()
    assert data["experimental_validation"]=="NOT_CLAIMED"
    assert len(data["snapshot_points"])==2
    assert data["snapshot_points"][0]["design_value"]=="38.123456789012345"
    assert data["snapshot_points"][0]["brake_power_kw"]=="12.345678901234567"
    assert data["snapshot_points"][0]["source_verified_at_export"] is False
    assert data["snapshot_points"][1]["periodicity"]=="INSUFFICIENT_CYCLES"
    assert data["snapshot_points"][1]["brake_power_kw"]==""


def test_study_csv_import_fails_closed_on_mixed_hashes_duplicate_indexes_and_false_verification(tmp_path):
    source=tmp_path/"invalid.csv";rows=_rows();rows[1]["manifest_sha256"]="f"*64;_write(source,rows)
    with pytest.raises(ValueError,match="manifest_sha256"):
        import_parametric_study_csv_snapshot(source)
    rows=_rows();rows[1]["point_index"]="0";_write(source,rows)
    with pytest.raises(ValueError,match="duplicados"):
        import_parametric_study_csv_snapshot(source)
    rows=_rows();rows[0]["source_verified"]="True";rows[0]["identity_sha256"]="not-a-hash";_write(source,rows)
    with pytest.raises(ValueError,match="identity_sha256"):
        import_parametric_study_csv_snapshot(source)


def test_nonstudy_csv_is_left_for_existing_report_importer(tmp_path):
    source=tmp_path/"other.csv";_write(source,[{"rpm":"3000","power":"1"}],("rpm","power"))
    assert import_parametric_study_csv_snapshot(source) is None


def test_services_dispatches_study_snapshot_and_results_page_shows_read_only_detail(tmp_path):
    source=tmp_path/"study.csv";_write(source)
    data=load_results(source)
    page=ResultsPage(DesktopContext(new_design_project("snapshot-ui-synthetic")))
    page._show_parametric_study_csv_snapshot(data,source)
    assert page.source_kind=="PARAMETRIC_STUDY_CSV_SNAPSHOT"
    assert not page.study_csv_snapshot_group.isHidden()
    assert page.result_tabs.currentIndex()==3
    assert page.study_csv_snapshot_table.rowCount()==2
    assert page.study_csv_snapshot_table.item(0,1).text()=="Escape · longitud=38.123456789012344 mm"
    assert page.study_csv_snapshot_table.item(0,6).text()=="12.345678901234567"
    assert page.study_csv_snapshot_table.item(0,9).text()=="Fuente no cargada al exportar"
    assert "MAX_CYCLES_NONCONVERGED" in page.study_csv_snapshot_table.item(1,3).toolTip()
    assert "no re-verificado" in page.study_csv_snapshot_notice.text()
    assert page.point_table.rowCount()==0 and page.power_curves.curves==[]
    assert "result_sha256" in page.study_csv_snapshot_detail.toPlainText()
    page.close();APP.processEvents()


def test_previous_synthetic_study_export_opens_without_its_source_runs():
    exported=Path(__file__).resolve().parents[1]/"results/desktop-parametric-design-study-v2/study-data-export/synthetic-native-selected.csv"
    data=load_results(exported)
    assert data["schema"]==SNAPSHOT_SCHEMA and data["snapshot"]["study_id"]=="synthetic-matrix-csv-native-ui"
    assert [point["periodicity"] for point in data["snapshot_points"]]==["PERIOD_1","INSUFFICIENT_CYCLES"]
    assert all(not point["source_verified_at_export"] for point in data["snapshot_points"])
    assert data["snapshot_points"][1]["brake_power_kw"]==""
