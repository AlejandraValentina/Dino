"""Read-only import for the exact single-study CSV exported by Dino Desktop."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


SNAPSHOT_SCHEMA = "DINO_PARAMETRIC_STUDY_CSV_SNAPSHOT_V1"
EXPORT_STUDY_SCHEMA = "DINO_PARAMETRIC_DESIGN_STUDY_V1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_COLUMNS = {
    "study_schema", "study_id", "project_id", "design_method", "manifest_path",
    "manifest_sha256", "parameter_id", "parameter_label", "point_index", "rpm",
    "run_id", "source_run_id", "execution_status", "classification", "periodicity",
    "cycles_completed", "factor_values_json", "source_verified", "source_verification",
    "brake_power_kw", "brake_torque_nm", "BMEP_kpa", "scientific_validation",
}
_METRICS = {
    "brake_power_kw": ("Potencia de freno", "kW"),
    "brake_torque_nm": ("Torque de freno", "N·m"),
    "BMEP_kpa": ("BMEP", "kPa"),
}


def _required_decimal(value: str, label: str, *, positive: bool = False) -> Decimal:
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"{label} no es un número decimal válido") from None
    if not number.is_finite() or (positive and number <= 0):
        raise ValueError(f"{label} no es finito o no es positivo")
    return number


def import_parametric_study_csv_snapshot(path: str | Path) -> dict | None:
    """Import a recognized study export without treating it as a runnable project.

    ``None`` means the CSV uses another schema and should be passed to the
    existing report importer. A recognized but invalid study CSV raises.
    Numeric cells remain text so this read-only snapshot preserves their exact
    exported decimal representation.
    """
    source = Path(path).resolve()
    raw=source.read_bytes()
    try:text=raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:raise ValueError(f"CSV paramétrico no es UTF-8: {exc}") from exc
    with io.StringIO(text,newline="") as stream:
        reader = csv.DictReader(stream)
        headers = set(reader.fieldnames or ())
        if "study_schema" not in headers or "manifest_sha256" not in headers:
            return None
        missing = sorted(_REQUIRED_COLUMNS - headers)
        if missing:
            raise ValueError(f"exportación paramétrica incompleta; faltan columnas: {', '.join(missing)}")
        rows = list(reader)
    if not rows or len(rows) > 30:
        raise ValueError("el snapshot requiere entre uno y treinta puntos")

    first = rows[0]
    if first.get("study_schema") != EXPORT_STUDY_SCHEMA:
        raise ValueError("schema de estudio paramétrico no compatible")
    study_id = first.get("study_id")
    if not study_id or any(row.get("study_id") != study_id for row in rows):
        raise ValueError("el CSV mezcla estudios o no informa su identidad")
    for key in ("project_id", "design_method", "manifest_path", "manifest_sha256",
                "baseline_engine_identity_sha256", "parameter_id", "parameter_label",
                "parameter_unit", "rpm", "scientific_validation"):
        expected = first.get(key, "")
        if any(row.get(key, "") != expected for row in rows):
            raise ValueError(f"el CSV mezcla valores incompatibles en {key}")
    manifest_hash = first.get("manifest_sha256", "").lower()
    if not _SHA256.fullmatch(manifest_hash):
        raise ValueError("SHA-256 del manifiesto ausente o inválido")
    rpm = _required_decimal(first.get("rpm", ""), "RPM", positive=True)

    points = []
    seen_indexes = set()
    for row in rows:
        try:
            point_index = int(row.get("point_index", ""))
        except (TypeError, ValueError):
            raise ValueError("índice de punto no válido") from None
        if point_index < 0 or point_index in seen_indexes:
            raise ValueError("índices de punto negativos o duplicados")
        seen_indexes.add(point_index)
        if row.get("study_schema") != EXPORT_STUDY_SCHEMA:
            raise ValueError("el CSV contiene schemas de estudio incompatibles")
        if row.get("manifest_sha256", "").lower() != manifest_hash:
            raise ValueError("los puntos no comparten el hash del manifiesto")
        if row.get("rpm") != first.get("rpm"):
            raise ValueError("los puntos no comparten la RPM del estudio")
        verified_text = row.get("source_verified", "")
        if verified_text not in {"True", "False"}:
            raise ValueError("estado de verificación de fuente no válido")
        try:
            factor_values = json.loads(row.get("factor_values_json") or "[]",
                parse_float=str,parse_int=str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"factor_values_json inválido en punto {point_index}: {exc}") from exc
        if not isinstance(factor_values, list) or any(not isinstance(item, dict) for item in factor_values):
            raise ValueError(f"valores factoriales no válidos en punto {point_index}")
        for field in ("design_value", "brake_power_kw", "brake_torque_nm", "BMEP_kpa"):
            if row.get(field, "") != "":
                _required_decimal(row[field], f"{field} del punto {point_index}")
        if verified_text == "True":
            for field in ("identity_sha256", "result_sha256"):
                if not _SHA256.fullmatch((row.get(field) or "").lower()):
                    raise ValueError(f"fuente marcada verificada sin {field} válido en punto {point_index}")
            artifact_hash=(row.get("result_artifact_sha256") or "").lower()
            if artifact_hash and not _SHA256.fullmatch(artifact_hash):
                raise ValueError(f"result_artifact_sha256 inválido en punto {point_index}")
        point = dict(row)
        point.update(point_index=point_index, rpm_exact=row.get("rpm"), rpm_decimal=str(rpm),
            factor_values=factor_values, source_verified_at_export=(verified_text == "True"),
            metric_labels=dict(_METRICS))
        points.append(point)

    return {
        "schema": SNAPSHOT_SCHEMA,
        "provenance": "CSV paramétrico exportado por Dino · snapshot externo de sólo lectura",
        "experimental_validation": first.get("scientific_validation") or "NOT_CLAIMED",
        "snapshot": {
            "source_path": str(source),
            "csv_sha256": hashlib.sha256(raw).hexdigest(),
            "csv_row_count": len(rows),
            "study_schema": first["study_schema"],
            "study_id": study_id,
            "project_id": first.get("project_id", ""),
            "design_method": first.get("design_method", ""),
            "manifest_path": first.get("manifest_path", ""),
            "manifest_sha256": manifest_hash,
            "scientific_validation": first.get("scientific_validation") or "NOT_CLAIMED",
            "read_only": True,
            "source_verification_time": "VERIFIED_AT_EXPORT_ONLY",
        },
        "snapshot_points": points,
        "point_count": len(points),
    }
