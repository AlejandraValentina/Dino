from __future__ import annotations

import csv
from pathlib import Path

import pytest

from motorsim.desktop.parametric_factorial_snapshot import (
    EXPORT_FIELDS, EXPORT_SCHEMA, SNAPSHOT_SCHEMA,
    import_parametric_factorial_csv_snapshot,
)
from motorsim.desktop.services import load_results


FIXTURE=Path("results/desktop-parametric-design-study-v2/factor-effects-csv/native-smoke-20261104T200320Z/factorial-export.csv")


def _rows(path):
    with path.open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        return reader.fieldnames,list(reader)


def _write(path,fields,rows):
    with path.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader();writer.writerows(rows)


def test_existing_native_factorial_export_roundtrips_exactly_as_read_only_snapshot():
    from motorsim.desktop.results_page import _FACTORIAL_EFFECTS_CSV_FIELDS
    assert tuple(_rows(FIXTURE)[0])==EXPORT_FIELDS
    assert EXPORT_FIELDS==_FACTORIAL_EFFECTS_CSV_FIELDS
    snapshot=import_parametric_factorial_csv_snapshot(FIXTURE)
    assert snapshot["schema"]==SNAPSHOT_SCHEMA
    assert snapshot["snapshot"]["csv_schema"]==EXPORT_SCHEMA
    assert snapshot["snapshot"]["manifest_current_verification"]=="CURRENT_HASH_AND_IDENTITY_MATCH"
    assert snapshot["snapshot"]["contrast_source_bindings"]=="MISSING_IN_EXPORTED_CONTRAST_ROWS"
    assert snapshot["snapshot"]["scientific_validation"]=="NOT_CLAIMED"
    assert snapshot["snapshot"]["read_only"] is True
    assert len(snapshot["snapshot_points"])==4 and len(snapshot["snapshot_contrasts"])==9
    assert snapshot["snapshot_points"][0]["factor_a_value"]=="0.0"
    assert snapshot["snapshot_points"][0]["brake_power_kw"]=="10.0"
    assert snapshot["snapshot_points"][0]["current_source_verification"]=="CURRENT_HASH_AND_IDENTITY_MATCH"
    assert all(row["contrast_source_binding_status"]=="NOT_PRESENT_IN_EXPORTED_CONTRAST_ROW"
        for row in snapshot["snapshot_contrasts"])
    assert load_results(FIXTURE)["schema"]==SNAPSHOT_SCHEMA


def test_factorial_csv_fails_closed_on_header_order_row_counts_and_invalid_hash(tmp_path):
    fields,rows=_rows(FIXTURE)
    reversed_path=tmp_path/"reversed.csv";_write(reversed_path,list(reversed(fields)),rows)
    with pytest.raises(ValueError,match="encabezados u orden"):
        import_parametric_factorial_csv_snapshot(reversed_path)
    short_path=tmp_path/"short.csv";_write(short_path,fields,rows[:-1])
    with pytest.raises(ValueError,match="13 filas"):
        import_parametric_factorial_csv_snapshot(short_path)
    invalid_path=tmp_path/"invalid-hash.csv"
    for row in rows:row["manifest_sha256"]="not-a-sha"
    _write(invalid_path,fields,rows)
    with pytest.raises(ValueError,match="SHA-256 del manifiesto"):
        import_parametric_factorial_csv_snapshot(invalid_path)


def test_factorial_csv_preserves_changed_source_and_manifest_states_without_claiming_verification(tmp_path):
    fields,rows=_rows(FIXTURE)
    changed_manifest=tmp_path/"changed-manifest.csv"
    for row in rows:
        row["manifest_sha256"]="0"*64
    _write(changed_manifest,fields,rows)
    snapshot=import_parametric_factorial_csv_snapshot(changed_manifest)
    assert snapshot["snapshot"]["manifest_current_verification"]=="CHANGED"

    fields,rows=_rows(FIXTURE)
    source=Path(rows[0]["source_path"])/"result.json"
    rows[0]["result_sha256"]="0"*64;rows[0]["result_artifact_sha256"]="0"*64
    modified=tmp_path/"modified-source.csv";_write(modified,fields,rows)
    snapshot=import_parametric_factorial_csv_snapshot(modified)
    assert snapshot["snapshot_points"][0]["source_verified_at_export"] is True
    assert snapshot["snapshot_points"][0]["current_source_verification"]=="SOURCE_CHANGED_OR_IDENTITY_MISMATCH"
    assert snapshot["snapshot_points"][1]["current_source_verification"]=="CURRENT_HASH_AND_IDENTITY_MATCH"
    assert source.is_file()  # the accepted source artifact was only read

    fields,rows=_rows(FIXTURE)
    rows[0]["source_path"]=str(tmp_path/"source-no-longer-available")
    unavailable=tmp_path/"unavailable-source.csv";_write(unavailable,fields,rows)
    snapshot=import_parametric_factorial_csv_snapshot(unavailable)
    assert snapshot["snapshot_points"][0]["source_verified_at_export"] is True
    assert snapshot["snapshot_points"][0]["current_source_verification"]=="SOURCE_UNAVAILABLE"


def test_factorial_csv_rejects_unqualified_values_duplicate_designs_and_missing_formula(tmp_path):
    fields,rows=_rows(FIXTURE)
    rows[0]["brake_power_qualification"]="WITHHELD_NONPERIODIC"
    invalid=tmp_path/"unqualified.csv";_write(invalid,fields,rows)
    with pytest.raises(ValueError,match="pese a no estar calificada"):
        import_parametric_factorial_csv_snapshot(invalid)

    fields,rows=_rows(FIXTURE)
    rows[1]["factor_a_value"]=rows[0]["factor_a_value"]
    rows[1]["factor_b_value"]=rows[0]["factor_b_value"]
    duplicate=tmp_path/"duplicate.csv";_write(duplicate,fields,rows)
    with pytest.raises(ValueError,match="duplicadas"):
        import_parametric_factorial_csv_snapshot(duplicate)

    fields,rows=_rows(FIXTURE)
    rows[4]["contrast_formula"]=""
    missing=tmp_path/"missing-formula.csv";_write(missing,fields,rows)
    with pytest.raises(ValueError,match="sin definición"):
        import_parametric_factorial_csv_snapshot(missing)


def test_nonperiodic_point_qualification_and_unavailable_contrasts_remain_explicit(tmp_path):
    fields,rows=_rows(FIXTURE)
    point=rows[0]
    point.update(classification="MAX_CYCLES_NONCONVERGED",periodicity="INSUFFICIENT_CYCLES")
    point["result_sha256"]="0"*64;point["result_artifact_sha256"]="0"*64
    for value_field,status_field,qualification_field in (
        ("brake_power_kw","brake_power_status","brake_power_qualification"),
        ("brake_torque_nm","brake_torque_status","brake_torque_qualification"),
        ("BMEP_kpa","BMEP_status","BMEP_qualification")):
        point[value_field]="";point[status_field]="UNDEFINED";point[qualification_field]="WITHHELD_NONPERIODIC"
    for row in rows:
        if row["record_type"]=="CONTRAST":
            row["contrast_value"]="";row["contrast_status"]="UNAVAILABLE"
            row["contrast_reason"]="Punto de origen no periódico"
    path=tmp_path/"nonperiodic-export.csv";_write(path,fields,rows)
    snapshot=import_parametric_factorial_csv_snapshot(path)
    assert snapshot["snapshot_points"][0]["periodicity"]=="INSUFFICIENT_CYCLES"
    assert snapshot["snapshot_points"][0]["brake_power_kw"]==""
    assert snapshot["snapshot_points"][0]["brake_power_qualification"]=="WITHHELD_NONPERIODIC"
    assert all(row["contrast_status"]=="UNAVAILABLE" and not row["contrast_value"]
        for row in snapshot["snapshot_contrasts"])


def test_non_factorial_csv_is_left_for_existing_importers(tmp_path):
    path=tmp_path/"ordinary.csv";path.write_text("rpm,power\n3000,12\n",encoding="utf-8")
    assert import_parametric_factorial_csv_snapshot(path) is None
