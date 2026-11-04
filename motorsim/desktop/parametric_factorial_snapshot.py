"""Read-only importer for Dino's provenance-bound 2x2 factorial CSV export."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re


SNAPSHOT_SCHEMA = "DINO_PARAMETRIC_FACTORIAL_CSV_SNAPSHOT_V1"
EXPORT_SCHEMA = "DINO_PARAMETRIC_FACTORIAL_EXPORT_V1"
_STUDY_SCHEMA = "DINO_PARAMETRIC_DESIGN_STUDY_V1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
EXPORT_FIELDS = (
    "csv_schema","record_type","study_schema","study_id","project_id","design_method",
    "manifest_path","manifest_sha256","baseline_engine_identity_sha256","scientific_validation",
    "rpm","point_index","design_label","parameter_id","parameter_label","parameter_unit",
    "factor_values_json","factor_a_id","factor_a_label","factor_a_value","factor_a_unit",
    "factor_b_id","factor_b_label","factor_b_value","factor_b_unit","run_id","source_run_id",
    "source_project_id","execution_status","classification","periodicity","cycles_completed",
    "source_path","engine_identity_sha256","identity_sha256","result_sha256",
    "result_artifact_sha256","source_verified","brake_power_kw","brake_power_status",
    "brake_power_qualification","brake_torque_nm","brake_torque_status",
    "brake_torque_qualification","BMEP_kpa","BMEP_status","BMEP_qualification","metric_id",
    "metric_label","metric_unit","contrast_term","contrast_value","contrast_unit",
    "contrast_status","contrast_formula","contrast_reason","contrast_source_run_ids_json",
    "contrast_source_result_sha256s_json")
_CONTRAST_METRICS = {"brake_power", "brake_torque", "BMEP"}
_POINT_METRICS = {
    "brake_power_kw": "brake_power_qualification",
    "brake_torque_nm": "brake_torque_qualification",
    "BMEP_kpa": "BMEP_qualification",
}


def _decimal(value: str, label: str, *, positive: bool = False) -> Decimal:
    try:
        number=Decimal(value)
    except (InvalidOperation,TypeError):
        raise ValueError(f"{label} no es un decimal válido") from None
    if not number.is_finite() or (positive and number<=0):
        raise ValueError(f"{label} no es finito o no es positivo")
    return number


def _sha(value: str | None, label: str, *, required: bool = True) -> str | None:
    normalized=(value or "").lower()
    if not normalized and not required:return None
    if not _SHA256.fullmatch(normalized):raise ValueError(f"{label} no es un SHA-256 válido")
    return normalized


def _json_array(value: str, label: str) -> list:
    try:parsed=json.loads(value)
    except (json.JSONDecodeError,TypeError) as exc:raise ValueError(f"{label} no es JSON válido: {exc}") from exc
    if not isinstance(parsed,list):raise ValueError(f"{label} debe ser una lista JSON")
    return parsed


def _current_manifest_status(path: str, expected_sha: str, study_id: str) -> str:
    try:
        raw=Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected_sha:return "CHANGED"
        manifest=json.loads(raw.decode("utf-8"))
    except FileNotFoundError:return "UNAVAILABLE"
    except (OSError,UnicodeDecodeError,json.JSONDecodeError):return "UNAVAILABLE_OR_INVALID"
    if manifest.get("schema")!=_STUDY_SCHEMA or manifest.get("study_id")!=study_id:
        return "IDENTITY_MISMATCH"
    return "CURRENT_HASH_AND_IDENTITY_MATCH"


def _current_source_status(point: dict) -> str:
    source=point.get("source_path") or ""
    if not source or not Path(source).is_dir():return "SOURCE_UNAVAILABLE"
    try:
        result_raw=(Path(source)/"result.json").read_bytes()
        result=json.loads(result_raw.decode("utf-8"))
        run=json.loads((Path(source)/"run.json").read_text(encoding="utf-8"))
    except (OSError,UnicodeDecodeError,json.JSONDecodeError):return "SOURCE_UNAVAILABLE_OR_INVALID"
    digest=hashlib.sha256(result_raw).hexdigest()
    run_id=point.get("source_run_id") or point.get("run_id")
    identity=point.get("identity_sha256") or point.get("engine_identity_sha256")
    if (digest!=point.get("result_sha256") or digest!=point.get("result_artifact_sha256") or
            digest!=run.get("result_sha256") or result.get("schema")!="DINO_ENGINEERING_RUN_V1" or
            result.get("status")!="COMPLETE" or result.get("bindings",{}).get("run_id")!=run_id or
            result.get("bindings",{}).get("identity_sha256")!=identity):
        return "SOURCE_CHANGED_OR_IDENTITY_MISMATCH"
    return "CURRENT_HASH_AND_IDENTITY_MATCH"


def import_parametric_factorial_csv_snapshot(path: str | Path) -> dict | None:
    """Return a validated read-only snapshot, ``None`` for another CSV format.

    Exact exported cell strings are retained for display and audit. A recognized
    but malformed factorial export is rejected rather than falling through to
    a generic historical-result importer.
    """
    source=Path(path).resolve();raw=source.read_bytes()
    try:text=raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:raise ValueError(f"CSV factorial no es UTF-8: {exc}") from exc
    with io.StringIO(text,newline="") as stream:
        reader=csv.DictReader(stream)
        fields=tuple(reader.fieldnames or ())
        if "csv_schema" not in fields:return None
        if fields!=EXPORT_FIELDS:
            raise ValueError("encabezados u orden no coinciden con DINO_PARAMETRIC_FACTORIAL_EXPORT_V1")
        rows=list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV factorial contiene columnas o celdas incompletas")
    if len(rows)!=13:
        raise ValueError("el snapshot factorial requiere exactamente 13 filas de datos")
    if any(row.get("csv_schema")!=EXPORT_SCHEMA for row in rows):
        raise ValueError("schema CSV factorial no compatible")
    if any(row.get("source_verified")!="True" for row in rows):
        raise ValueError("el CSV debe conservar el estado de verificación al exportar")
    points=[row for row in rows if row.get("record_type")=="POINT"]
    contrasts=[row for row in rows if row.get("record_type")=="CONTRAST"]
    if len(points)!=4 or len(contrasts)!=9 or len(points)+len(contrasts)!=len(rows):
        raise ValueError("el CSV debe contener cuatro puntos y nueve contrastes, sin otros tipos de fila")
    metadata_fields=("study_schema","study_id","project_id","design_method","manifest_path",
        "manifest_sha256","baseline_engine_identity_sha256","scientific_validation","rpm",
        "parameter_id","parameter_label","parameter_unit")
    first=rows[0]
    for name in metadata_fields:
        if any(row.get(name)!=first.get(name) for row in rows):
            raise ValueError(f"el CSV mezcla metadatos en {name}")
    if first["study_schema"]!=_STUDY_SCHEMA or first["design_method"]!="FACTORIAL_2X2_V1":
        raise ValueError("el estudio no corresponde al schema factorial 2×2 exportable")
    if not first["study_id"] or not first["project_id"] or not first["scientific_validation"]:
        raise ValueError("faltan identidad de estudio, proyecto o clasificación científica")
    manifest_sha=_sha(first["manifest_sha256"],"SHA-256 del manifiesto")
    baseline_sha=_sha(first["baseline_engine_identity_sha256"],"identidad SHA-256 de baseline")
    rpm=_decimal(first["rpm"],"RPM",positive=True)
    factor_a_id=first["factor_a_id"];factor_b_id=first["factor_b_id"]
    if not factor_a_id or not factor_b_id or factor_a_id==factor_b_id:
        raise ValueError("los dos factores deben tener identificadores distintos")
    for point in points:
        for field in ("factor_a_id","factor_a_label","factor_a_unit","factor_b_id","factor_b_label","factor_b_unit"):
            if point.get(field)!=first.get(field):
                raise ValueError(f"los puntos no comparten metadatos factoriales en {field}")
    seen_indexes=set();combos=set();source_ids=[];source_hashes=[]
    for point in points:
        try:index=int(point["point_index"])
        except (TypeError,ValueError):raise ValueError("índice factorial no válido") from None
        if index<0 or index in seen_indexes:raise ValueError("índices de puntos factoriales duplicados o negativos")
        seen_indexes.add(index)
        if point["source_verified"]!="True":raise ValueError(f"la fuente del punto {index} no estaba verificada al exportar")
        for field in ("factor_a_value","factor_b_value"):_decimal(point[field],field)
        combo=(_decimal(point["factor_a_value"],"factor A"),_decimal(point["factor_b_value"],"factor B"))
        if combo in combos:raise ValueError("la matriz contiene combinaciones factoriales duplicadas")
        combos.add(combo)
        if point["factor_a_id"]!=factor_a_id or point["factor_b_id"]!=factor_b_id:
            raise ValueError("un punto cambia la identidad de sus factores")
        if not point["source_run_id"] or not point["run_id"]:
            raise ValueError("un punto carece de identidad de corrida fuente")
        for field in ("engine_identity_sha256","identity_sha256","result_sha256","result_artifact_sha256"):
            _sha(point.get(field),f"{field} del punto {index}")
        for field,status_field,qualification_field in (
            ("brake_power_kw","brake_power_status","brake_power_qualification"),
            ("brake_torque_nm","brake_torque_status","brake_torque_qualification"),
            ("BMEP_kpa","BMEP_status","BMEP_qualification")):
            value=point.get(field,"");qualification=point.get(qualification_field)
            if value:_decimal(value,f"{field} del punto {index}")
            if qualification not in {"PERIOD_1_DEFINED","WITHHELD_NONPERIODIC","UNDEFINED_OR_INVALID"}:
                raise ValueError(f"calificación {qualification_field} desconocida en punto {index}")
            if value and qualification!="PERIOD_1_DEFINED":
                raise ValueError(f"métrica {field} tiene valor pese a no estar calificada PERIOD_1_DEFINED")
            if qualification=="PERIOD_1_DEFINED" and not value:
                raise ValueError(f"métrica {field} calificada PERIOD_1_DEFINED no conserva valor")
            if qualification=="WITHHELD_NONPERIODIC" and value:
                raise ValueError(f"métrica no periódica {field} debe permanecer vacía")
            if qualification=="PERIOD_1_DEFINED" and point.get("periodicity")!="PERIOD_1":
                raise ValueError(f"métrica {field} está definida pero la periodicidad no es PERIOD_1")
            if qualification=="WITHHELD_NONPERIODIC" and point.get("periodicity")=="PERIOD_1":
                raise ValueError(f"métrica {field} está retenida aunque el punto se declara PERIOD_1")
            if point.get("periodicity")!="PERIOD_1" and qualification!="WITHHELD_NONPERIODIC":
                raise ValueError(f"métrica {field} no indica WITHHELD_NONPERIODIC para un punto no periódico")
        source_ids.append(point["source_run_id"]);source_hashes.append(point["result_sha256"])
        try:factors=json.loads(point.get("factor_values_json") or "[]",parse_float=str,parse_int=str)
        except json.JSONDecodeError as exc:raise ValueError(f"factor_values_json inválido: {exc}") from exc
        if not isinstance(factors,list) or any(not isinstance(item,dict) for item in factors):
            raise ValueError("factor_values_json debe contener una lista de objetos")
        factor_map={item.get("parameter_id"):item for item in factors}
        if set(factor_map)!={factor_a_id,factor_b_id}:
            raise ValueError("factor_values_json no identifica exactamente los dos factores")
        if (_decimal(str(factor_map[factor_a_id].get("value")),"valor JSON del factor A")!=combo[0] or
                _decimal(str(factor_map[factor_b_id].get("value")),"valor JSON del factor B")!=combo[1]):
            raise ValueError("los niveles factoriales JSON no coinciden con sus columnas CSV")
        point["point_index_int"]=index
        point["factor_values"]=factors
        point["source_verified_at_export"]=True
        point["current_source_verification"]=_current_source_status(point)
    levels_a={combo[0] for combo in combos};levels_b={combo[1] for combo in combos}
    if seen_indexes!={0,1,2,3} or len(levels_a)!=2 or len(levels_b)!=2 or len(combos)!=4:
        raise ValueError("los puntos no forman los cuatro niveles distintos de una matriz 2×2")
    contrast_keys=set();contrast_sources_missing=False
    expected_ids=set(source_ids);expected_hashes=set(source_hashes)
    if len(expected_ids)!=4 or len(expected_hashes)!=4:
        raise ValueError("las cuatro filas POINT deben conservar corridas y resultados fuente distintos")
    for row in contrasts:
        key=(row.get("metric_id"),row.get("contrast_term"))
        if row.get("metric_id") not in _CONTRAST_METRICS or not row.get("contrast_term") or key in contrast_keys:
            raise ValueError("identidad de contraste desconocida o duplicada")
        contrast_keys.add(key)
        if row.get("contrast_status") not in {"DESCRIPTIVE_DEFINED","UNAVAILABLE"}:
            raise ValueError("estado de contraste no compatible")
        if row.get("contrast_status")=="DESCRIPTIVE_DEFINED" and not row.get("contrast_value"):
            raise ValueError("contraste declarado disponible sin valor")
        if row.get("contrast_status")=="UNAVAILABLE" and row.get("contrast_value"):
            raise ValueError("contraste no disponible debe conservar valor vacío")
        if row.get("contrast_value"):_decimal(row["contrast_value"],"valor de contraste")
        if not row.get("contrast_formula"):
            raise ValueError("contraste sin definición de fórmula")
        ids=_json_array(row.get("contrast_source_run_ids_json",""),"fuentes de contraste")
        hashes=_json_array(row.get("contrast_source_result_sha256s_json",""),"hashes fuente de contraste")
        if (len(ids)==4 and len(hashes)==4 and all(value is None for value in ids) and
                all(value is None for value in hashes)):
            # Preserve a known V1 exporter omission; do not fabricate bindings.
            row["contrast_source_binding_status"]="NOT_PRESENT_IN_EXPORTED_CONTRAST_ROW"
            contrast_sources_missing=True
        elif (len(ids)==4 and len(hashes)==4 and set(ids)==expected_ids and
                set(map(str.lower,hashes))==expected_hashes):
            row["contrast_source_binding_status"]="MATCHES_POINT_ROWS"
        else:raise ValueError("el contraste no referencia las cuatro fuentes POINT o declara un binding parcial")
    if (len(contrast_keys)!=9 or {metric for metric,_ in contrast_keys}!=_CONTRAST_METRICS or
            any(sum(metric==item[0] for item in contrast_keys)!=3 for metric in _CONTRAST_METRICS)):
        raise ValueError("la matriz de contrastes no contiene tres términos para cada métrica")
    manifest_status=_current_manifest_status(first["manifest_path"],manifest_sha,first["study_id"])
    point_rows=[]
    for point in sorted(points,key=lambda item:item["point_index_int"]):
        point_rows.append(dict(point))
    contrast_rows=sorted(contrasts,key=lambda item:(item["metric_id"],item["contrast_term"]))
    if any(point.get("periodicity")!="PERIOD_1" for point in points):
        if any(row.get("contrast_status")!="UNAVAILABLE" or row.get("contrast_value") for row in contrast_rows):
            raise ValueError("un estudio con puntos no PERIOD_1 no puede declarar contrastes factoriales disponibles")
    csv_sha=hashlib.sha256(raw).hexdigest()
    return {
        "schema":SNAPSHOT_SCHEMA,
        "provenance":"CSV factorial exportado por Dino · snapshot externo de sólo lectura",
        "experimental_validation":first["scientific_validation"],
        "snapshot":{"source_path":str(source),"csv_sha256":csv_sha,"csv_row_count":len(rows),
            "csv_schema":EXPORT_SCHEMA,"study_schema":first["study_schema"],"study_id":first["study_id"],
            "project_id":first["project_id"],"design_method":first["design_method"],
            "manifest_path":first["manifest_path"],"manifest_sha256":manifest_sha,
            "manifest_current_verification":manifest_status,
            "baseline_engine_identity_sha256":baseline_sha,"rpm_exact":first["rpm"],"rpm_decimal":str(rpm),
            "scientific_validation":first["scientific_validation"],"source_verification_time":"VERIFIED_AT_EXPORT_ONLY",
            "contrast_source_bindings":"MISSING_IN_EXPORTED_CONTRAST_ROWS" if contrast_sources_missing else "MATCH_POINT_ROWS",
            "read_only":True,"factor_a":{"id":factor_a_id,"label":first["factor_a_label"],"unit":first["factor_a_unit"]},
            "factor_b":{"id":factor_b_id,"label":first["factor_b_label"],"unit":first["factor_b_unit"]}},
        "snapshot_points":point_rows,"snapshot_contrasts":contrast_rows,
        "point_count":len(point_rows),"contrast_count":len(contrast_rows),
    }
