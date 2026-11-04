from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

import pytest
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from motorsim.desktop.comparison_snapshot import (
    EXPORT_FIELDS, EXPORT_SCHEMA, SNAPSHOT_SCHEMA,
    import_cross_study_comparison_csv_snapshot,
)
from motorsim.desktop.context import DesktopContext
from motorsim.desktop.results_page import ResultsPage, _CROSS_STUDY_CSV_FIELDS
from motorsim.desktop.services import load_results, new_design_project

APP=QApplication.instance() or QApplication([])
FIXTURE=Path("results/desktop-parametric-design-study-v2/cross-study-csv-export/synthetic-comparison.csv")


def _read(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader=csv.DictReader(stream)
        return list(reader.fieldnames or ()),list(reader)


def _write(path, fields, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer=csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def test_existing_cross_study_csv_imports_exactly_as_read_only_snapshot():
    fields,rows=_read(FIXTURE)
    assert tuple(fields)==EXPORT_FIELDS==_CROSS_STUDY_CSV_FIELDS
    snapshot=import_cross_study_comparison_csv_snapshot(FIXTURE)
    assert snapshot["schema"]==SNAPSHOT_SCHEMA
    assert snapshot["source_sha256"]=="819af0ddfaf839cb221e790526f9b6be9282bca50fa31e539a3b14f13028905a"
    assert snapshot["scientific_validation"]=="NOT_CLAIMED"
    assert snapshot["read_only"] is True
    assert len(snapshot["rows"])==2 and len(snapshot["study_ids"])==2
    assert snapshot["rows"][0]["comparison_schema"]==EXPORT_SCHEMA
    assert snapshot["rows"][0]["point_a_design_value"]=="38.40862784470379"
    assert snapshot["rows"][0]["pairing_status"]=="EXACT_RPM_AND_OPERATING_CONTEXT"
    assert snapshot["rows"][0]["brake_power_a_kw"]==""
    assert snapshot["rows"][1]["row_type"]=="UNPAIRED"
    assert snapshot["rows"][1]["pairing_reason"]=="Fixture sintético: sin punto compatible a 4000 RPM."
    assert snapshot["rows"][0]["point_a_periodicity"]=="INSUFFICIENT_CYCLES"
    assert snapshot["source_statuses"][0]["a"]=="NO_VERIFICADA_AL_EXPORTAR"
    assert load_results(FIXTURE)["schema"]==SNAPSHOT_SCHEMA


def test_cross_study_snapshot_rejects_unsupported_and_inconsistent_rows(tmp_path):
    fields,rows=_read(FIXTURE)
    unsupported=tmp_path/"unsupported.csv"
    rows[0]["comparison_schema"]="OTHER_SCHEMA";_write(unsupported,fields,rows)
    with pytest.raises(ValueError,match="schema CSV"):
        import_cross_study_comparison_csv_snapshot(unsupported)

    fields,rows=_read(FIXTURE)
    rows[1]["pairing_status"]="EXACT_RPM_AND_OPERATING_CONTEXT"
    invalid_pair=tmp_path/"invalid-pair.csv";_write(invalid_pair,fields,rows)
    with pytest.raises(ValueError,match="estado incompatible"):
        import_cross_study_comparison_csv_snapshot(invalid_pair)

    fields,rows=_read(FIXTURE)
    rows[1]["study_b_manifest_sha256"]="0"*64
    changed_binding=tmp_path/"changed-binding.csv";_write(changed_binding,fields,rows)
    with pytest.raises(ValueError,match="cambia entre filas"):
        import_cross_study_comparison_csv_snapshot(changed_binding)


def test_changed_current_manifest_is_rejected_when_export_claimed_verified(tmp_path):
    fields,rows=_read(FIXTURE)
    rows[0]["point_a_source_verified"]="True"
    rows[0]["study_a_manifest_sha256"]="0"*64
    changed=tmp_path/"changed-verified.csv";_write(changed,fields,rows)
    with pytest.raises(ValueError,match="fuente marcada verificada ya no coincide"):
        import_cross_study_comparison_csv_snapshot(changed)


def test_changed_verified_result_artifact_is_rejected_without_rewriting_source(tmp_path):
    fields,rows=_read(FIXTURE)
    manifests={};directories={}
    for study_id in ("synthetic-study-A","synthetic-study-B"):
        manifest_path=tmp_path/f"{study_id}.study.json"
        raw=json.dumps({"schema":"DINO_PARAMETRIC_DESIGN_STUDY_V1","study_id":study_id,
            "baseline_engine_identity_sha256":"9"*64},sort_keys=True,separators=(",",":")).encode()
        manifest_path.write_bytes(raw)
        manifests[study_id]=(manifest_path,hashlib.sha256(raw).hexdigest())
    for row in rows:
        for side in ("a","b"):
            study_id=row[f"study_{side}_id"]
            if not study_id:continue
            run_id=row[f"point_{side}_source_run_id"]
            directory=tmp_path/run_id;directory.mkdir(exist_ok=True)
            result={"schema":"DINO_ENGINEERING_RUN_V1","status":"COMPLETE","bindings":{
                "run_id":run_id,"identity_sha256":row[f"point_{side}_identity_sha256"].lower()}}
            result_raw=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
            (directory/"result.json").write_bytes(result_raw)
            (directory/"run.json").write_text(json.dumps({"result_sha256":hashlib.sha256(result_raw).hexdigest()}),encoding="utf-8")
            manifest_path,manifest_sha=manifests[study_id]
            row[f"study_{side}_manifest_path"]=str(manifest_path)
            row[f"study_{side}_manifest_sha256"]=manifest_sha
            row[f"point_{side}_run_directory"]=str(directory)
            row[f"point_{side}_result_sha256"]=hashlib.sha256(result_raw).hexdigest()
            row[f"point_{side}_result_artifact_sha256"]=hashlib.sha256(result_raw).hexdigest()
            row[f"point_{side}_source_verified"]="True"
            directories[run_id]=directory
    changed=directories["synthetic-B-1"]
    (changed/"result.json").write_text('{"changed":true}',encoding="utf-8")
    path=tmp_path/"changed-result.csv";_write(path,fields,rows)
    with pytest.raises(ValueError,match="ARTIFACT_CAMBIADO_O_IDENTIDAD_NO_COINCIDE"):
        import_cross_study_comparison_csv_snapshot(path)
    assert (changed/"result.json").read_text(encoding="utf-8")=="{\"changed\":true}"


def test_cross_study_snapshot_desktop_view_keeps_exact_rows_and_no_curves():
    data=load_results(FIXTURE)
    page=ResultsPage(DesktopContext(new_design_project("cross-study-csv-snapshot-ui")))
    page._show_cross_study_csv_snapshot(data,FIXTURE)
    assert not page.cross_study_csv_snapshot_group.isHidden()
    assert page.cross_study_csv_snapshot_table.rowCount()==2
    assert page.cross_study_csv_snapshot_table.item(0,0).text()=="Pareja exacta"
    assert "Ciclos insuficientes" in page.cross_study_csv_snapshot_table.item(0,3).text()
    assert page.cross_study_csv_snapshot_table.item(1,0).text()=="Sin pareja"
    assert page.cross_study_csv_snapshot_table.item(1,7).text()=="Fixture sintético: sin punto compatible a 4000 RPM."
    assert page.cross_study_csv_snapshot_table.item(0,7).text()=="RPM y contexto exactos"
    assert "No declarada" in page.cross_study_csv_snapshot_notice.text()
    assert page.plot.series==[] and page.design_study_table.rowCount()==0
    assert page.export_table_button.isHidden()
    page.cross_study_csv_snapshot_table.setCurrentCell(1,0);APP.processEvents()
    assert "study_b_manifest_sha256" in page.cross_study_csv_snapshot_detail.toPlainText()
    assert "NOT_CLAIMED" in page.cross_study_csv_snapshot_detail.toPlainText()
    assert "NOT_VERIFIED" not in page.cross_study_csv_snapshot_detail.toPlainText()
    page.close();APP.processEvents()
