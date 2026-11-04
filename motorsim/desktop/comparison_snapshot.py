"""Strict read-only importer for exported cross-study comparison CSV snapshots."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


SNAPSHOT_SCHEMA = "DINO_PARAMETRIC_CROSS_STUDY_CSV_SNAPSHOT_V1"
EXPORT_SCHEMA = "DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1"
_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
EXPORT_FIELDS = (
    "comparison_schema","baseline_engine_identity_sha256","row_type",
    "study_a_id","study_a_manifest_path","study_a_manifest_sha256","point_a_index","point_a_run_id",
    "point_a_source_run_id","point_a_design_value","point_a_design_unit","point_a_factor_values_json",
    "point_a_classification","point_a_periodicity","point_a_cycles_completed","point_a_engine_identity_sha256",
    "point_a_identity_sha256","point_a_result_sha256","point_a_result_artifact_sha256","point_a_run_directory","point_a_source_verified",
    "study_b_id","study_b_manifest_path","study_b_manifest_sha256","point_b_index","point_b_run_id",
    "point_b_source_run_id","point_b_design_value","point_b_design_unit","point_b_factor_values_json",
    "point_b_classification","point_b_periodicity","point_b_cycles_completed","point_b_engine_identity_sha256",
    "point_b_identity_sha256","point_b_result_sha256","point_b_result_artifact_sha256","point_b_run_directory","point_b_source_verified",
    "rpm","pairing_status","pairing_reason","brake_power_a_kw","brake_power_b_kw","brake_power_delta_kw",
    "brake_torque_a_nm","brake_torque_b_nm","brake_torque_delta_nm","BMEP_a_kpa","BMEP_b_kpa",
    "BMEP_delta_kpa","scientific_validation")
_METRICS = ("brake_power_a_kw","brake_power_b_kw","brake_power_delta_kw",
            "brake_torque_a_nm","brake_torque_b_nm","brake_torque_delta_nm",
            "BMEP_a_kpa","BMEP_b_kpa","BMEP_delta_kpa")


def _sha(value: str, label: str, *, optional: bool = False) -> str:
    if optional and not value:
        return value
    if not _SHA256.fullmatch(value or ""):
        raise ValueError(f"{label} no es un SHA-256 válido")
    return value.lower()


def _decimal(value: str, label: str, *, optional: bool = False) -> Decimal | None:
    if optional and value == "":
        return None
    try:
        number = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValueError(f"{label} no es un decimal válido") from None
    if not number.is_finite():
        raise ValueError(f"{label} debe ser finito")
    return number


def _source_status(row: dict, side: str) -> str:
    if row[f"point_{side}_source_verified"] != "True":
        return "NO_VERIFICADA_AL_EXPORTAR"
    run_dir = row[f"point_{side}_run_directory"]
    try:
        source = Path(run_dir)
        manifest_raw = Path(row[f"study_{side}_manifest_path"]).read_bytes()
        manifest = json.loads(manifest_raw.decode("utf-8"))
        if hashlib.sha256(manifest_raw).hexdigest() != row[f"study_{side}_manifest_sha256"]:
            return "MANIFIESTO_CAMBIADO"
        if manifest.get("schema") != "DINO_PARAMETRIC_DESIGN_STUDY_V1" or manifest.get("study_id") != row[f"study_{side}_id"]:
            return "IDENTIDAD_DE_MANIFIESTO_NO_COINCIDE"
        result_raw = (source / "result.json").read_bytes()
        result = json.loads(result_raw.decode("utf-8"))
        run = json.loads((source / "run.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "FUENTE_NO_DISPONIBLE"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "FUENTE_NO_DISPONIBLE_O_INVALIDA"
    digest = hashlib.sha256(result_raw).hexdigest()
    if (digest != row[f"point_{side}_result_sha256"].lower() or
            digest != row[f"point_{side}_result_artifact_sha256"].lower() or
            digest != run.get("result_sha256") or
            result.get("bindings", {}).get("run_id") != row[f"point_{side}_source_run_id"] or
            result.get("bindings", {}).get("identity_sha256") != row[f"point_{side}_identity_sha256"].lower()):
        return "ARTIFACT_CAMBIADO_O_IDENTIDAD_NO_COINCIDE"
    return "HASH_E_IDENTIDAD_ACTUALES_COINCIDEN"


def import_cross_study_comparison_csv_snapshot(path: str | Path) -> dict | None:
    """Return a validated, immutable-in-meaning snapshot; ``None`` for other CSVs."""
    source = Path(path).resolve()
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"CSV de comparación no es UTF-8: {exc}") from exc
    with io.StringIO(text, newline="") as stream:
        reader = csv.DictReader(stream)
        fields = tuple(reader.fieldnames or ())
        if "comparison_schema" not in fields:
            return None
        if fields != EXPORT_FIELDS:
            raise ValueError("encabezados u orden no coinciden con DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1")
        rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV de comparación vacío o con columnas/celdas incompletas")
    if any(row["comparison_schema"] != EXPORT_SCHEMA for row in rows):
        raise ValueError("schema CSV de comparación no compatible")
    baseline = _sha(rows[0]["baseline_engine_identity_sha256"], "identidad SHA-256 baseline")
    scientific = rows[0]["scientific_validation"]
    if not scientific or any(row["scientific_validation"] != scientific for row in rows):
        raise ValueError("la clasificación científica falta o cambia entre filas")
    study_ids: set[str] = set()
    study_bindings: dict[str, tuple[str,str]] = {}
    for row_index, row in enumerate(rows, 1):
        if row["baseline_engine_identity_sha256"].lower() != baseline:
            raise ValueError("la comparación mezcla identidades baseline")
        row_type = row["row_type"]
        if row_type not in {"EXACT_PAIR", "UNPAIRED"}:
            raise ValueError(f"tipo de fila desconocido en fila {row_index}")
        if row["pairing_status"] not in {"EXACT_RPM_AND_OPERATING_CONTEXT", "NO_EXACT_COMPATIBLE_PAIR"}:
            raise ValueError(f"estado de pareo desconocido en fila {row_index}")
        if row_type == "EXACT_PAIR" and row["pairing_status"] != "EXACT_RPM_AND_OPERATING_CONTEXT":
            raise ValueError(f"fila pareada con estado incompatible en fila {row_index}")
        if row_type == "UNPAIRED" and row["pairing_status"] != "NO_EXACT_COMPATIBLE_PAIR":
            raise ValueError(f"fila sin pareja con estado incompatible en fila {row_index}")
        rpm = _decimal(row["rpm"], f"RPM fila {row_index}")
        if rpm <= 0:
            raise ValueError(f"RPM no positiva en fila {row_index}")
        if row_type == "EXACT_PAIR" and (row["study_a_id"] == row["study_b_id"] or not row["study_a_id"] or not row["study_b_id"]):
            raise ValueError(f"identidades de estudios incompatibles en fila {row_index}")
        if row_type == "UNPAIRED" and bool(row["study_a_id"]) == bool(row["study_b_id"]):
            raise ValueError(f"una fila sin pareja debe contener exactamente una fuente en fila {row_index}")
        for side in ("a", "b"):
            study_id = row[f"study_{side}_id"]
            if not study_id:
                if any(row[f"point_{side}_{name}"] for name in (
                        "index","run_id","source_run_id","classification","periodicity","result_sha256",
                        "result_artifact_sha256","run_directory","source_verified")):
                    raise ValueError(f"campos de punto huérfanos del estudio {side.upper()} en fila {row_index}")
                continue
            study_ids.add(study_id)
            _sha(row[f"study_{side}_manifest_sha256"], f"hash de manifiesto {side.upper()}")
            if not row[f"study_{side}_manifest_path"]:
                raise ValueError(f"falta ruta del manifiesto {side.upper()} en fila {row_index}")
            binding=(row[f"study_{side}_manifest_path"],row[f"study_{side}_manifest_sha256"].lower())
            if study_id in study_bindings and study_bindings[study_id]!=binding:
                raise ValueError(f"la identidad del manifiesto de {study_id} cambia entre filas")
            study_bindings[study_id]=binding
            try:
                factors = json.loads(row[f"point_{side}_factor_values_json"])
            except json.JSONDecodeError:
                raise ValueError(f"factores no son JSON válidos en fila {row_index}") from None
            if not isinstance(factors, list):
                raise ValueError(f"factores deben ser una lista en fila {row_index}")
            _decimal(row[f"point_{side}_design_value"], f"valor de diseño {side.upper()} fila {row_index}")
            try:
                index = int(row[f"point_{side}_index"])
                cycles = int(row[f"point_{side}_cycles_completed"])
            except ValueError:
                raise ValueError(f"índice o ciclos inválidos en fila {row_index}") from None
            if index < 0 or cycles < 0 or not row[f"point_{side}_run_id"] or not row[f"point_{side}_source_run_id"]:
                raise ValueError(f"identidad/índice/ciclos de punto inválidos en fila {row_index}")
            if row[f"point_{side}_source_verified"] not in {"True", "False"}:
                raise ValueError(f"calificación de fuente inválida en fila {row_index}")
            for key in ("engine_identity_sha256","identity_sha256","result_sha256","result_artifact_sha256"):
                _sha(row[f"point_{side}_{key}"], f"{key} del punto {side.upper()} fila {row_index}")
        for metric in _METRICS:
            _decimal(row[metric], f"{metric} fila {row_index}", optional=True)
        # The exporter only exposes response metrics for paired PERIOD_1 endpoints.
        if row_type == "UNPAIRED" and any(row[name] for name in _METRICS):
            raise ValueError(f"fila sin pareja contiene métricas de comparación en fila {row_index}")
        if row_type == "EXACT_PAIR":
            periodic = all(row[f"point_{side}_periodicity"] == "PERIOD_1" for side in ("a", "b"))
            if not periodic and any(row[name] for name in _METRICS):
                raise ValueError(f"métricas visibles para extremos no PERIOD_1 en fila {row_index}")
    if not 2 <= len(study_ids) <= 4:
        raise ValueError("la comparación debe conservar entre dos y cuatro estudios")

    source_statuses = {}
    for index, row in enumerate(rows):
        statuses = {}
        for side in ("a", "b"):
            if row[f"study_{side}_id"]:
                status = _source_status(row, side)
                if row[f"point_{side}_source_verified"] == "True" and status in {
                        "MANIFIESTO_CAMBIADO", "IDENTIDAD_DE_MANIFIESTO_NO_COINCIDE",
                        "ARTIFACT_CAMBIADO_O_IDENTIDAD_NO_COINCIDE"}:
                    raise ValueError(f"la fuente marcada verificada ya no coincide: fila {index + 1}, estudio {side.upper()} ({status})")
                statuses[side] = status
        source_statuses[index] = statuses
    return {
        "schema": SNAPSHOT_SCHEMA,
        "source_path": str(source),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "baseline_engine_identity_sha256": baseline,
        "scientific_validation": scientific,
        "rows": rows,
        "source_statuses": source_statuses,
        "study_ids": sorted(study_ids),
        "read_only": True,
    }
