"""Reproducible single-factor design studies over existing Dino configurations.

This adapter creates immutable per-point engine documents and delegates every
solver run to the Desktop engineering workflow. It adds no physics model.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any

from .engine_configuration import identity, validate
from .engine_variants import escape_sections, partitioned_escape_counts, stretch_partitioned_escape

SCHEMA = "DINO_PARAMETRIC_DESIGN_STUDY_V1"
MAX_DESIGN_POINTS = 5
MAX_STUDY_BUDGET_SECONDS = 600


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical(value)); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        try: Path(name).unlink(missing_ok=True)
        except OSError: pass


def study_directory(artifact_root: str | Path, project_id: str, study_id: str) -> Path:
    for value, label in ((project_id, "project_id"), (study_id, "study_id")):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value):
            raise ValueError(f"{label} must be a safe path component")
    root = Path(artifact_root).resolve()
    target = (root / "design-studies-v1" / project_id / study_id).resolve()
    if root not in target.parents:
        raise ValueError("resolved design-study path escaped the artifact root")
    return target


def _verified_historical_match(artifact_root: Path, design_point: dict, *, rpm: float,
                               max_cycles: int, memory_limit_mib: int,
                               exclude: Path | None = None,
                               history_references: list | None = None) -> dict | None:
    """Find a completed exact-identity engineering run and verify it via importer."""
    from .engineering_workflow import import_desktop_runs
    from .engine_configuration import implementation_source_hashes
    run_root = artifact_root / "exploratory-workflow-v1"
    expected = design_point["preflight"]
    candidates = []
    if run_root.is_dir():
        candidates.extend(path for project_dir in sorted(run_root.iterdir()) if project_dir.is_dir()
                          for path in sorted(project_dir.iterdir()) if path.is_dir())
    reference_by_path = {}
    for reference in history_references or []:
        if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
            continue
        path = Path(reference["path"]).expanduser()
        if not path.is_absolute():path = artifact_root / path
        path = path.resolve()
        candidate = path.parent if path.name == "result.json" else path
        if candidate.is_dir():
            candidates.append(candidate)
            reference_by_path.setdefault(candidate, []).append(reference)
    unique = sorted({path.resolve() for path in candidates}, key=lambda path: str(path).casefold())
    for candidate in unique:
            if exclude is not None and candidate.resolve() == exclude.resolve():
                continue
            result_path = candidate / "result.json"
            manifest_path = candidate / "run.json"
            if not result_path.is_file() or not manifest_path.is_file():
                continue
            try:
                raw = json.loads(result_path.read_text(encoding="utf-8"))
                run = json.loads(manifest_path.read_text(encoding="utf-8"))
                bindings = raw.get("bindings", {})
                preflight = raw.get("preflight", {})
                result_hash = run.get("result_sha256")
                if not result_hash or result_hash != _sha_bytes(result_path.read_bytes()):
                    continue
                references = reference_by_path.get(candidate, [])
                if references and not any(
                        ref.get("identity_sha256") == bindings.get("identity_sha256") and
                        ref.get("artifact_sha256") == _sha_bytes(result_path.read_bytes())
                        for ref in references):
                    continue
                if (raw.get("schema") != "DINO_ENGINEERING_RUN_V1" or
                        raw.get("status") != "COMPLETE" or
                        bindings.get("identity_sha256") != expected.get("identity_sha256") or
                        raw.get("source_hashes") != implementation_source_hashes() or
                        preflight.get("rpm") != rpm or
                        preflight.get("max_cycles") != max_cycles or
                        preflight.get("memory_limit_mib") != memory_limit_mib):
                    continue
                imported = import_desktop_runs([candidate])["points"]
                if len(imported) != 1:
                    continue
                record = imported[0]
                if (record.get("run_id") != bindings.get("run_id") or
                        record.get("rpm") != rpm or
                        record.get("cycles_requested") != max_cycles or
                        record.get("implementation_identity_sha256") is None):
                    continue
                return {"status": raw["status"], "classification": raw.get("classification"),
                    "periodicity": raw.get("periodicity"), "cycles_completed": raw.get("cycles_completed"),
                    "artifact_directory": str(candidate), "result_sha256": result_hash,
                    "identity_sha256": bindings["identity_sha256"],
                    "elapsed_seconds": raw.get("elapsed_seconds", 0), "reused_verified": True,
                    "historical_source_run_id": bindings.get("run_id"),
                    "historical_source_project_id": bindings.get("project_id"),
                    "historical_source_reference": bool(references),
                    "history_reuse_policy": "EXACT_IDENTITY_OPERATING_POINT_SOURCES_ARTIFACTS_V1"}
            except Exception:
                # Damaged or unsupported history is never eligible for reuse.
                continue
    return None


def available_parameters(engine: dict) -> list[dict]:
    """List only explicit native fields with a consistency-preserving adapter."""
    validate(engine)
    options=[]
    try:
        sections = escape_sections(engine)
        partitioned_escape_counts(engine)  # recognize existing faces; never refine
        options.extend({"id": f"exhaust.section.{index}.length_mm",
             "label": f"Escape · {row['name']} · longitud",
             "unit": "mm", "baseline": float(row["length_mm"]),
             "section_index": index, "adapter": "PARTITIONED_LENGTH_EDIT_V1"}
            for index, row in enumerate(sections))
    except (KeyError, StopIteration, ValueError):
        # A different supported axis may still be available on this engine.
        pass
    native=engine["native_configuration"]
    binding=native.get("port_binding",{}).get("port_set")
    if isinstance(binding,dict):
        for port in binding.get("ports",[]):
            if port.get("role")=="transfer":
                fields=(("top_mm","mm","altura desde PMS"),
                    ("height_mm","mm","altura"),("width_mm","mm","ancho"),
                    ("discharge_coefficient","adimensional","coeficiente de descarga"))
            elif port.get("role")=="intake":
                # Intake opening timing/full-area summaries remain unchanged;
                # only its existing discharge coefficient is an exposed axis.
                fields=(("discharge_coefficient","adimensional","coeficiente de descarga"),)
            else:
                # Exhaust summaries also bind power-valve positions; keep those
                # axes out until every displayed state can be regenerated.
                fields=()
            for field,unit,label in fields:
                value=port.get(field)
                if type(value) in (int,float) and math.isfinite(float(value)):
                    options.append({"id":f"port:{port['id']}:{field}",
                        "label":f"Lumbrera · {port.get('name',port['id'])} · {label}",
                        "unit":unit,"baseline":float(value),"port_id":port["id"],
                        "field":field,"adapter":"PORT_FIELD_EDIT_V1"})
    crankcase=native.get("slider_crank",{}).get("crankcase",{})
    volume=crankcase.get("volume_bdc_cm3")
    if type(volume) in (int,float) and math.isfinite(float(volume)):
        options.append({"id":"crankcase.volume_bdc_cm3",
            "label":"Cárter · volumen en PMI","unit":"cm³","baseline":float(volume),
            "adapter":"CRANKCASE_BDC_VOLUME_EDIT_V1"})
    return options


def _apply_parameter(engine: dict, parameter: dict, value: float) -> dict:
    if type(value) not in (int, float) or not math.isfinite(float(value)) or value <= 0:
        raise ValueError("el parámetro debe ser un valor finito positivo en su unidad declarada")
    adapter=parameter.get("adapter")
    if adapter=="PARTITIONED_LENGTH_EDIT_V1":
        sections = escape_sections(engine)
        index = parameter["section_index"]
        if type(index) is not int or not 0 <= index < len(sections):
            raise ValueError("índice de sección fuera de la geometría de escape")
        sections[index]["length_mm"] = float(value)
        result = stretch_partitioned_escape(engine, sections)
    elif adapter=="PORT_FIELD_EDIT_V1":
        from .two_stroke_ports import DuctBinding,PortDefinition,TwoStrokePortSet
        result=deepcopy(engine);native=result["native_configuration"]
        binding=native["port_binding"]["port_set"]
        ports=deepcopy(binding["ports"])
        matches=[port for port in ports if port.get("id")==parameter["port_id"]]
        if len(matches)!=1 or parameter["field"] not in {"top_mm","height_mm","width_mm","discharge_coefficient"}:
            raise ValueError("la definición de lumbrera no coincide con el adaptador guardado")
        if matches[0].get(parameter["field"]) is None:
            raise ValueError("el campo de lumbrera no está declarado explícitamente")
        matches[0][parameter["field"]]=float(value)
        rebuilt=TwoStrokePortSet(binding["stroke_mm"],binding["rod_length_mm"],
            tuple(DuctBinding.from_dict(row) for row in binding["ducts"]),
            tuple(PortDefinition.from_dict(row) for row in ports)).to_dict()
        native["port_binding"]["port_set"]=rebuilt
        native["geometry_identity"]["ports"]=deepcopy(rebuilt)
        transfers=[port for port in rebuilt["ports"] if port["role"]=="transfer"]
        if transfers:
            native["geometry_identity"]["transfer_effective_width_mm"]=math.fsum(
                port["width_mm"] for port in transfers)
            if parameter["field"]=="top_mm":
                port_set=TwoStrokePortSet.from_dict(rebuilt)
                openings=[]
                for port in port_set.ports:
                    if port.role!="transfer":continue
                    transitions=[]
                    for event in sorted({float(angle)%360.0 for angle in port_set.event_angles(port)}):
                        left=port_set.area_at(port,(event-1e-4)%360.0)
                        right=port_set.area_at(port,(event+1e-4)%360.0)
                        if left<=1e-9<right:transitions.append(event)
                    if len(transitions)!=1:
                        raise ValueError("no se pudo identificar una apertura de transferencia unívoca")
                    openings.extend(transitions)
                if openings:native["geometry_identity"]["transfer_opens_atdc_deg"]=min(openings)
        if parameter["field"]=="discharge_coefficient" and matches[0]["role"]=="intake":
            port_set=TwoStrokePortSet.from_dict(rebuilt)
            intake=next(port for port in port_set.ports if port.id==parameter["port_id"])
            native["geometry_identity"]["inlet_window_effective_area_mm2"] = max(
                port_set.area_at(intake,angle) for angle in range(361))
        from .engine_configuration import sha256
        result["native_configuration_sha256"]=sha256(native)
        result["provenance"]={**result["provenance"],"parametric_port_adapter":"PORT_FIELD_EDIT_V1"}
    elif adapter=="CRANKCASE_BDC_VOLUME_EDIT_V1":
        from .crankcase import CrankcaseGeometry
        from .integrated_2t import SliderCrankChambers2T
        result=deepcopy(engine);native=result["native_configuration"]
        cc=native["slider_crank"]["crankcase"];cc["volume_bdc_cm3"]=float(value)
        crank=CrankcaseGeometry.from_dict(cc)
        geometry=native["geometry_identity"]
        geometry["crankcase_volume_bdc_cc"]=float(value)
        geometry["crankcase_compression_ratio"]=crank.compression_ratio
        volumes=SliderCrankChambers2T(crank,native["slider_crank"]["cylinder_compression_ratio"]).resolve(
            0.0,native["reference_rpm"])
        for name,volume in (("crankcase",volumes[0]),("cylinder",volumes[1])):
            masses=native["initial_chambers"]["species"][name]
            total=math.fsum(masses)
            target=native["initial_chambers"][name][0]*volume
            if total<=0 or target<=0:
                raise ValueError(f"el inventario inicial de {name} no es positivo")
            native["initial_chambers"]["species"][name]=[mass*target/total for mass in masses]
        from .engine_configuration import sha256
        result["native_configuration_sha256"]=sha256(native)
        result["provenance"]={**result["provenance"],"parametric_crankcase_adapter":"CRANKCASE_BDC_VOLUME_EDIT_V1"}
    else:
        raise ValueError("adaptador paramétrico no compatible")
    validate(result)
    return result


def prepare_design_study(engine: dict, *, parameter_id: str, values: list[float],
                         rpm: float, max_cycles: int, point_budget_seconds: float,
                         total_budget_seconds: float, memory_limit_mib: int = 1024,
                         project_id: str, variant_label: str = "base",
                         study_id: str | None = None) -> dict:
    """Validate all design points without taking a solver step."""
    validate(engine)
    options = {item["id"]: item for item in available_parameters(engine)}
    if parameter_id not in options:
        raise ValueError("parámetro no compatible con los adaptadores paramétricos disponibles")
    if not isinstance(values, list) or not 2 <= len(values) <= MAX_DESIGN_POINTS:
        raise ValueError(f"un estudio requiere de 2 a {MAX_DESIGN_POINTS} valores")
    numeric = [float(value) for value in values]
    if any(not math.isfinite(value) or value <= 0 for value in numeric):
        raise ValueError("todos los valores del estudio deben ser finitos y positivos")
    if len(set(numeric)) != len(numeric):
        raise ValueError("los valores del estudio deben ser únicos")
    parameter = options[parameter_id]
    if parameter["baseline"] not in numeric:
        raise ValueError("incluí el valor baseline del diseño para que las diferencias tengan referencia")
    if type(rpm) not in (int, float) or not math.isfinite(rpm) or rpm <= 0:
        raise ValueError("RPM debe ser finito y positivo")
    if type(max_cycles) is not int or not 1 <= max_cycles <= 111:
        raise ValueError("el horizonte debe estar entre 1 y 111 ciclos")
    if type(point_budget_seconds) not in (int, float) or not 1 <= point_budget_seconds <= 600:
        raise ValueError("presupuesto por punto debe estar entre 1 y 600 s")
    if type(total_budget_seconds) not in (int, float) or not len(values) <= total_budget_seconds <= MAX_STUDY_BUDGET_SECONDS:
        raise ValueError(f"presupuesto agregado debe cubrir todos los puntos y no superar {MAX_STUDY_BUDGET_SECONDS} s")
    if type(memory_limit_mib) is not int or not 256 <= memory_limit_mib <= 4096:
        raise ValueError("memoria debe estar entre 256 y 4096 MiB")
    from .exploratory_workflow import preflight
    points=[]
    for index,value in enumerate(numeric):
        document=_apply_parameter(engine,parameter,value)
        document["provenance"]={**document["provenance"],"parametric_study":{
            "schema":"DINO_PARAMETRIC_POINT_PROVENANCE_V1",
            "parent_engine_identity_sha256":identity(engine),
            "parameter_id":parameter_id,"value":value,"unit":parameter["unit"],
            "classification":"SYNTHETIC_ASSUMPTION"}}
        displacement=document.get("native_configuration",{}).get("geometry_identity",{}).get("displacement_cc")
        if (type(displacement) not in (int,float) or not math.isfinite(float(displacement))
                or displacement <= 0):
            raise ValueError("el flujo de ingeniería requiere geometry_identity.displacement_cc explícito; no se infiere ni se completa automáticamente")
        check=preflight(document,rpm=rpm,max_cycles=max_cycles,
                        budget_seconds=float(point_budget_seconds),memory_limit_mib=memory_limit_mib)
        points.append({"index":index,"value":value,"unit":parameter["unit"],
            "baseline":math.isclose(value,parameter["baseline"],rel_tol=0,abs_tol=1e-12),
            "engine_identity_sha256":identity(document),"preflight":check,
            "engine_document":document})
    study_id=study_id or "ds-"+_sha_bytes(_canonical({"project":project_id,"parameter":parameter_id,
        "values":numeric,"baseline_identity":identity(engine),"time_ns":time.time_ns()}))[:20]
    # Validate all artifact path components before users authorize computation.
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", project_id):
        raise ValueError("project_id must be a safe path component")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", study_id):
        raise ValueError("study_id must be a safe path component")
    return {"schema":SCHEMA,"study_id":study_id,"project_id":project_id,
        "variant_label":variant_label,"parameter":parameter,"values":numeric,
        "baseline_engine_identity_sha256":identity(engine),"rpm":float(rpm),
        "max_cycles":max_cycles,"point_budget_seconds":float(point_budget_seconds),
        "total_budget_seconds":float(total_budget_seconds),"memory_limit_mib":memory_limit_mib,
        "mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED",
        "periodicity":"EVALUATED_PER_POINT_BY_EXISTING_DETECTOR",
        "points":points}


def prepare_factorial_design_study(engine: dict, *, factors: list[dict],
                         rpm: float, max_cycles: int, point_budget_seconds: float,
                         total_budget_seconds: float, memory_limit_mib: int = 1024,
                         project_id: str, variant_label: str = "base",
                         study_id: str | None = None) -> dict:
    """Prepare an immutable two-factor, two-level matrix using existing adapters."""
    if not isinstance(factors,list) or len(factors)!=2:
        raise ValueError("un estudio factorial requiere exactamente dos factores")
    plans=[]
    for factor in factors:
        if not isinstance(factor,dict) or set(factor)!={"parameter_id","values"}:
            raise ValueError("cada factor requiere parameter_id y dos valores")
        values=factor["values"]
        if not isinstance(values,list) or len(values)!=2:
            raise ValueError("cada factor requiere exactamente baseline y un nivel alternativo")
        plans.append(prepare_design_study(engine,parameter_id=factor["parameter_id"],
            values=values,rpm=rpm,max_cycles=max_cycles,point_budget_seconds=point_budget_seconds,
            total_budget_seconds=total_budget_seconds,memory_limit_mib=memory_limit_mib,
            project_id=project_id,variant_label=variant_label,study_id="factor-check"))
    if plans[0]["parameter"]["id"]==plans[1]["parameter"]["id"]:
        raise ValueError("los dos factores deben ser parámetros distintos")
    axes=[{"parameter":plan["parameter"],"values":plan["values"]} for plan in plans]
    combos=[(a,b) for a in axes[0]["values"] for b in axes[1]["values"]]
    if total_budget_seconds<4*point_budget_seconds:
        raise ValueError("el presupuesto agregado debe cubrir los cuatro diseños factoriales")
    from .exploratory_workflow import preflight
    points=[]
    for index,(left,right) in enumerate(combos):
        document=deepcopy(engine)
        selected=[(axes[0]["parameter"],left),(axes[1]["parameter"],right)]
        for parameter,value in selected:
            document=_apply_parameter(document,parameter,value)
        factor_values=[{"parameter_id":parameter["id"],"label":parameter["label"],
            "value":value,"unit":parameter["unit"],
            "baseline":math.isclose(value,parameter["baseline"],rel_tol=0,abs_tol=1e-12)}
            for parameter,value in selected]
        point_label=" · ".join(f"{item['label']}={item['value']:g} {item['unit']}" for item in factor_values)
        document["provenance"]={**document["provenance"],"parametric_study":{
            "schema":"DINO_PARAMETRIC_FACTORIAL_POINT_V1",
            "parent_engine_identity_sha256":identity(engine),"factors":factor_values,
            "classification":"SYNTHETIC_ASSUMPTION"}}
        displacement=document.get("native_configuration",{}).get("geometry_identity",{}).get("displacement_cc")
        if type(displacement) not in (int,float) or not math.isfinite(float(displacement)) or displacement<=0:
            raise ValueError("el flujo de ingeniería requiere geometry_identity.displacement_cc explícito; no se infiere ni se completa automáticamente")
        check=preflight(document,rpm=rpm,max_cycles=max_cycles,
            budget_seconds=float(point_budget_seconds),memory_limit_mib=memory_limit_mib)
        points.append({"index":index,"value":float(index),"unit":"factorial",
            "label":point_label,"factor_values":factor_values,
            "baseline":all(item["baseline"] for item in factor_values),
            "engine_identity_sha256":identity(document),"preflight":check,"engine_document":document})
    parameter={"id":"factorial-2x2","label":"2×2 · ".join(axis["parameter"]["label"] for axis in axes),
        "unit":"","axes":[axis["parameter"] for axis in axes]}
    numeric_values=[[item["value"] for item in point["factor_values"]] for point in points]
    study_id=study_id or "ds-"+_sha_bytes(_canonical({"project":project_id,"axes":axes,
        "baseline_identity":identity(engine),"time_ns":time.time_ns()}))[:20]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}",project_id):
        raise ValueError("project_id must be a safe path component")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}",study_id):
        raise ValueError("study_id must be a safe path component")
    return {"schema":SCHEMA,"design_method":"FACTORIAL_2X2_V1","study_id":study_id,
        "project_id":project_id,"variant_label":variant_label,"parameter":parameter,
        "factors":axes,"values":numeric_values,"baseline_engine_identity_sha256":identity(engine),
        "rpm":float(rpm),"max_cycles":max_cycles,"point_budget_seconds":float(point_budget_seconds),
        "total_budget_seconds":float(total_budget_seconds),"memory_limit_mib":memory_limit_mib,
        "mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED",
        "periodicity":"EVALUATED_PER_POINT_BY_EXISTING_DETECTOR","points":points}


def prepare_design_rpm_envelope(engine: dict, *, parameter_id: str, values: list[float],
                         rpms: list[int], max_cycles: int, point_budget_seconds: float,
                         total_budget_seconds: float, memory_limit_mib: int = 1024,
                         project_id: str, variant_label: str = "base",
                         artifact_root: str | Path, study_id: str | None = None) -> dict:
    """Preflight a bounded geometry × RPM matrix using existing sweep adapters."""
    from .power_curve import plan_rpm_range
    if not isinstance(rpms,list) or not 2 <= len(rpms) <= 6:
        raise ValueError("la envolvente requiere de 2 a 6 RPM explícitas")
    if any(type(value) is not int for value in rpms):
        raise ValueError("los RPM de la envolvente deben ser enteros")
    try:grid=plan_rpm_range(rpms[0],rpms[-1],rpms[1]-rpms[0])
    except ValueError as exc:
        raise ValueError("los RPM deben formar una cuadrícula ascendente uniforme y alcanzar exactamente el valor final") from exc
    if grid!=rpms:
        raise ValueError("los RPM deben formar una cuadrícula ascendente uniforme y explícita")
    if not isinstance(values,list) or not 2 <= len(values) <= MAX_DESIGN_POINTS:
        raise ValueError(f"la envolvente admite de 2 a {MAX_DESIGN_POINTS} diseños")
    if len(values)*len(rpms)>30:
        raise ValueError("una envolvente se limita a 30 combinaciones diseño × RPM")
    if type(point_budget_seconds) not in (int,float) or not 1 <= point_budget_seconds <= 600:
        raise ValueError("el presupuesto por combinación debe estar entre 1 y 600 s")
    minimum=float(len(values)*len(rpms)*point_budget_seconds)
    if (type(total_budget_seconds) not in (int,float) or
            minimum > total_budget_seconds or total_budget_seconds > MAX_STUDY_BUDGET_SECONDS):
        raise ValueError(f"el presupuesto agregado debe cubrir las {len(values)*len(rpms)} combinaciones y no superar {MAX_STUDY_BUDGET_SECONDS} s")
    # The existing design adapter constructs consistent engine variants. The
    # first RPM here is only a zero-step geometry preflight; each full RPM grid
    # is then preflighted with the existing power-curve adapter below.
    geometry=prepare_design_study(engine,parameter_id=parameter_id,values=values,
        rpm=rpms[0],max_cycles=max_cycles,point_budget_seconds=point_budget_seconds,
        total_budget_seconds=float(total_budget_seconds),memory_limit_mib=memory_limit_mib,
        project_id=project_id,variant_label=variant_label,study_id=study_id)
    from .power_curve_sweep import prepare_power_curve
    root=Path(artifact_root).expanduser().resolve()
    per_design_budget=float(total_budget_seconds)/len(geometry["points"])
    groups=[]
    for index,design in enumerate(geometry["points"]):
        curve=prepare_power_curve(design["engine_document"],project_id=project_id,
            variant_label=f"{variant_label} · {geometry['parameter']['label']}={design['value']:g} {design['unit']}",
            artifact_root=root,start_rpm=rpms[0],stop_rpm=rpms[-1],step_rpm=rpms[1]-rpms[0],
            max_cycles=max_cycles,point_budget_seconds=float(point_budget_seconds),
            total_budget_seconds=per_design_budget,memory_limit_mib=memory_limit_mib)
        if curve["rpms"]!=rpms:
            raise ValueError("barrido backend cambió la cuadrícula RPM solicitada")
        groups.append({"index":index,"value":design["value"],"unit":design["unit"],
            "baseline":design["baseline"],"engine_identity_sha256":design["engine_identity_sha256"],
            "sweep_id":f"{geometry['study_id']}-d{index:02d}",
            "curve_identity_sha256":curve["identity_sha256"],
            "point_preflights":curve["point_preflights"]})
    immutable={"design_method":"RPM_ENVELOPE_V1","study_id":geometry["study_id"],
        "project_id":project_id,"variant_label":variant_label,"parameter":geometry["parameter"],
        "values":geometry["values"],"rpms":rpms,
        "baseline_engine_identity_sha256":geometry["baseline_engine_identity_sha256"],
        "max_cycles":max_cycles,"point_budget_seconds":float(point_budget_seconds),
        "total_budget_seconds":float(total_budget_seconds),"memory_limit_mib":memory_limit_mib,
        "artifact_root":str(root),"mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED",
        "periodicity":"EVALUATED_PER_POINT_BY_EXISTING_DETECTOR"}
    return {"schema":"DINO_PARAMETRIC_RPM_ENVELOPE_PREPARED_V1",**immutable,
        "baseline_engine_document":deepcopy(engine),"design_points":geometry["points"],
        "groups":groups,"immutable_spec_sha256":_sha_bytes(_canonical(immutable)),
        "combination_count":len(values)*len(rpms),"per_design_budget_seconds":per_design_budget}


def load_prepared_rpm_envelope(manifest_path: str | Path) -> dict:
    """Reload and re-preflight a saved envelope before checkpoint continuation."""
    path=Path(manifest_path).resolve()
    if path.name!="study.json":raise ValueError("seleccioná el study.json de la envolvente RPM")
    manifest=json.loads(path.read_text(encoding="utf-8"))
    prepared_path=path.parent/"prepared.json";raw=prepared_path.read_bytes()
    if _sha_bytes(raw)!=manifest.get("prepared_spec_sha256"):
        raise ValueError("configuración preparada de envolvente no coincide con su hash")
    prepared=json.loads(raw.decode("utf-8"))
    if prepared.get("schema")!="DINO_PARAMETRIC_RPM_ENVELOPE_PREPARED_V1" or prepared.get("study_id")!=manifest.get("study_id"):
        raise ValueError("identidad de envolvente guardada inválida")
    rebuilt=prepare_design_rpm_envelope(prepared["baseline_engine_document"],
        parameter_id=prepared["parameter"]["id"],values=prepared["values"],rpms=prepared["rpms"],
        max_cycles=prepared["max_cycles"],point_budget_seconds=prepared["point_budget_seconds"],
        total_budget_seconds=prepared["total_budget_seconds"],memory_limit_mib=prepared["memory_limit_mib"],
        project_id=prepared["project_id"],variant_label=prepared["variant_label"],
        artifact_root=prepared["artifact_root"],study_id=prepared["study_id"])
    if _canonical(rebuilt)!=_canonical(prepared):
        raise ValueError("preflight o identidad de la envolvente RPM cambió")
    if manifest.get("immutable_spec_sha256")!=prepared["immutable_spec_sha256"]:
        raise ValueError("contrato inmutable de envolvente no coincide")
    return prepared


def run_design_rpm_envelope(prepared: dict, *, cancel_event=None, progress=None,
                            resume: bool = False, reuse_runs=()) -> dict:
    """Run/resume each design through the existing bounded RPM sweep runner."""
    from .power_curve_sweep import run_power_curve
    if prepared.get("schema")!="DINO_PARAMETRIC_RPM_ENVELOPE_PREPARED_V1":
        raise ValueError("unsupported RPM envelope schema")
    immutable={key:prepared[key] for key in ("design_method","study_id","project_id","variant_label",
        "parameter","values","rpms","baseline_engine_identity_sha256","max_cycles",
        "point_budget_seconds","total_budget_seconds","memory_limit_mib","artifact_root",
        "mode","scientific_validation","periodicity")}
    if _sha_bytes(_canonical(immutable))!=prepared.get("immutable_spec_sha256"):
        raise ValueError("RPM envelope prepared contract/hash mismatch")
    validate(prepared["baseline_engine_document"])
    if identity(prepared["baseline_engine_document"])!=prepared["baseline_engine_identity_sha256"]:
        raise ValueError("RPM envelope baseline engine identity mismatch")
    if (len(prepared.get("design_points",[]))!=len(prepared["values"]) or
            len(prepared.get("groups",[]))!=len(prepared["values"])):
        raise ValueError("RPM envelope design group count mismatch")
    for index,(design,group) in enumerate(zip(prepared["design_points"],prepared["groups"])):
        validate(design["engine_document"])
        engine_identity=identity(design["engine_document"])
        if (engine_identity!=design.get("engine_identity_sha256") or
                engine_identity!=group.get("engine_identity_sha256") or
                group.get("index")!=index or group.get("value")!=design.get("value") or
                group.get("baseline")!=design.get("baseline") or
                group.get("sweep_id")!=f"{prepared['study_id']}-d{index:02d}" or
                group.get("curve_identity_sha256")!=engine_identity or
                [row.get("rpm") for row in group.get("point_preflights",[])]!=prepared["rpms"] or
                any(row.get("status")!="PASS" or row.get("solver_steps")!=0 or
                    not isinstance(row.get("identity_sha256"),str) or len(row["identity_sha256"])!=64 or
                    any(char not in "0123456789abcdef" for char in row["identity_sha256"])
                    for row in group.get("point_preflights",[]))):
            raise ValueError("RPM envelope prepared design/preflight identity mismatch")
    target=study_directory(prepared["artifact_root"],prepared["project_id"],prepared["study_id"])/"rpm-envelope"
    if target.exists() and not resume and any(target.iterdir()):
        raise FileExistsError("RPM envelope output directory already contains files; explicit resume is required")
    target.mkdir(parents=True,exist_ok=True)
    prepared_path=target/"prepared.json";manifest_path=target/"study.json"
    payload=_canonical(prepared)
    if manifest_path.exists():
        if not resume:raise FileExistsError("RPM envelope exists; explicit resume is required")
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        if (not prepared_path.is_file() or prepared_path.read_bytes()!=payload or
                manifest.get("schema")!=SCHEMA or manifest.get("design_method")!="RPM_ENVELOPE_V1" or
                manifest.get("prepared_spec_sha256")!=_sha_bytes(payload) or
                manifest.get("immutable_spec_sha256")!=prepared["immutable_spec_sha256"]):
            raise ValueError("RPM envelope resume rejected: immutable design or prepared bytes differ")
        expected_manifest={"project_id":prepared["project_id"],"variant_label":prepared["variant_label"],
            "parameter":prepared["parameter"],"values":prepared["values"],"rpms":prepared["rpms"],
            "baseline_engine_identity_sha256":prepared["baseline_engine_identity_sha256"],
            "max_cycles":prepared["max_cycles"],"point_budget_seconds":prepared["point_budget_seconds"],
            "total_budget_seconds":prepared["total_budget_seconds"],"memory_limit_mib":prepared["memory_limit_mib"]}
        if any(manifest.get(key)!=value for key,value in expected_manifest.items()):
            raise ValueError("RPM envelope manifest identity/baseline/grid mismatch")
    else:
        if resume:raise FileNotFoundError("cannot resume RPM envelope without its manifest")
        _atomic_json(prepared_path,prepared)
        manifest={"schema":SCHEMA,"design_method":"RPM_ENVELOPE_V1","study_id":prepared["study_id"],
            "project_id":prepared["project_id"],"variant_label":prepared["variant_label"],
            "parameter":prepared["parameter"],"values":prepared["values"],"rpms":prepared["rpms"],
            "baseline_engine_identity_sha256":prepared["baseline_engine_identity_sha256"],
            "immutable_spec_sha256":prepared["immutable_spec_sha256"],
            "prepared_spec_sha256":_sha_bytes(payload),"max_cycles":prepared["max_cycles"],
            "point_budget_seconds":prepared["point_budget_seconds"],
            "total_budget_seconds":prepared["total_budget_seconds"],
            "memory_limit_mib":prepared["memory_limit_mib"],"mode":"EXPLORATORY",
            "scientific_validation":"NOT_CLAIMED","periodicity":"EVALUATED_PER_POINT_BY_EXISTING_DETECTOR",
            "status":"PREPARED","elapsed_seconds":0.0,"groups":[],"points":[]}
    existing={row["index"]:row for row in manifest.get("groups",[])}
    if len(existing)!=len(manifest.get("groups",[])) or set(existing)-set(range(len(prepared["groups"]))):
        raise ValueError("RPM envelope resume rejected: duplicate/out-of-range design group")
    sweep_root=Path(prepared["artifact_root"])/"dino-power-curve-v1"/prepared["project_id"]
    for index,row in existing.items():
        expected=prepared["groups"][index]
        if (row.get("sweep_id")!=expected["sweep_id"] or
                row.get("engine_identity_sha256")!=expected["engine_identity_sha256"] or
                row.get("value")!=expected["value"] or row.get("baseline")!=expected["baseline"]):
            raise ValueError("RPM envelope resume rejected: saved design group identity mismatch")
        series=sweep_root/expected["sweep_id"]/"series.json"
        saved_path=row.get("sweep_manifest")
        if saved_path:
            if Path(saved_path).resolve()!=series.resolve() or not series.is_file() or _sha_bytes(series.read_bytes())!=row.get("sweep_manifest_sha256"):
                raise ValueError("RPM envelope resume rejected: nested sweep manifest path/hash mismatch")
        elif row.get("status")=="COMPLETE":
            raise ValueError("RPM envelope resume rejected: completed design lacks its sweep manifest binding")
    stop_reason="ALL_DESIGNS_FINISHED"
    manifest["status"]="RUNNING";_atomic_json(manifest_path,manifest)
    for group in prepared["groups"]:
        saved=existing.get(group["index"],{})
        if cancel_event is not None and cancel_event.is_set():
            stop_reason="CANCELLED";break
        row={"index":group["index"],"value":group["value"],"unit":group["unit"],
            "baseline":group["baseline"],"engine_identity_sha256":group["engine_identity_sha256"],
            "sweep_id":group["sweep_id"],"status":"RUNNING"}
        existing[group["index"]]=row;manifest["groups"]=[existing[i] for i in sorted(existing)]
        manifest["status"]="RUNNING";_atomic_json(manifest_path,manifest)
        document=prepared["design_points"][group["index"]]["engine_document"]
        curve=run_power_curve(document,project_id=prepared["project_id"],
            variant_label=f"{prepared['study_id']} · {prepared['parameter']['label']}={group['value']:g} {group['unit']}",
            artifact_root=prepared["artifact_root"],start_rpm=prepared["rpms"][0],
            stop_rpm=prepared["rpms"][-1],step_rpm=prepared["rpms"][1]-prepared["rpms"][0],
            max_cycles=prepared["max_cycles"],point_budget_seconds=prepared["point_budget_seconds"],
            total_budget_seconds=prepared["per_design_budget_seconds"],
            memory_limit_mib=prepared["memory_limit_mib"],sweep_id=group["sweep_id"],
            resume=bool(saved.get("status") not in {None,"NOT_STARTED"}),
            cancel_event=cancel_event,reuse_runs=reuse_runs,
            progress=(lambda detail,g=group: progress({**detail,"study_id":prepared["study_id"],
                "design_index":g["index"]+1,"design_count":len(prepared["groups"]),
                "design_value":g["value"]}) if progress else None))
        row.update(status=curve.get("status"),classification=curve.get("classification"),
            curve_availability=curve.get("curve_availability"),
            sweep_manifest=str(Path(curve["artifact_directory"])/"series.json"),
            elapsed_seconds=curve.get("elapsed_seconds",0),points=[])
        sweep_manifest_path=Path(curve["artifact_directory"])/"series.json"
        if not sweep_manifest_path.is_file():
            raise ValueError("RPM sweep runner returned without its manifest")
        row["sweep_manifest"]=str(sweep_manifest_path)
        row["sweep_manifest_sha256"]=_sha_bytes(sweep_manifest_path.read_bytes())
        for point in curve.get("points",[]):
            flat={"run_id":point.get("run_id"),"design_index":group["index"],
                "value":group["value"],"unit":group["unit"],"baseline":group["baseline"],
                "rpm":point.get("rpm"),"status":point.get("status"),
                "classification":point.get("classification"),"periodicity":point.get("periodicity"),
                "cycles_completed":point.get("cycles_completed"),
                "engine_identity_sha256":point.get("identity_sha256"),
                "result_artifact_sha256":point.get("result_artifact_sha256"),
                "run_directory":point.get("run_directory"),"sweep_manifest":str(sweep_manifest_path)}
            row["points"].append(flat)
        existing[group["index"]]=row;manifest["groups"]=[existing[i] for i in sorted(existing)]
        manifest["points"]=[point for index in sorted(existing) for point in existing[index].get("points",[])]
        manifest["elapsed_seconds"]=sum(float(item.get("elapsed_seconds",0)) for item in existing.values())
        if progress:progress({"study_id":prepared["study_id"],"design_index":group["index"]+1,
            "design_count":len(prepared["groups"]),"status":row["status"],"elapsed_seconds":manifest["elapsed_seconds"]})
        complete=curve.get("status")=="COMPLETE"
        _atomic_json(manifest_path,manifest)
        if not complete:
            stop_reason="CANCELLED" if cancel_event is not None and cancel_event.is_set() else "POINT_INCOMPLETE"
            break
    complete=(len(existing)==len(prepared["groups"]) and all(row.get("status")=="COMPLETE" for row in existing.values()))
    manifest["status"]="COMPLETE" if complete else "CANCELLED" if stop_reason=="CANCELLED" else "PARTIAL"
    manifest["stop_reason"]=stop_reason;manifest["updated_unix"]=time.time()
    _atomic_json(manifest_path,manifest)
    curve_available=(complete and all(row.get("curve_availability")=="EXPLORATORY_CURVE_AVAILABLE"
        for row in existing.values()))
    return {"schema":"DINO_PARAMETRIC_DESIGN_STUDY_RESULT_V1","study_id":prepared["study_id"],
        "status":manifest["status"],"classification":"EXPLORATORY_PARAMETRIC_RPM_ENVELOPE",
        "mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED","periodicity":"PER_POINT",
        "elapsed_seconds":manifest["elapsed_seconds"],"points":manifest["points"],
        "design_study_manifest":str(manifest_path),"bindings":{"project_id":prepared["project_id"]},
        "curve_availability":"EXPLORATORY_CURVE_AVAILABLE" if curve_available else "EXPLORATORY_CURVE_PARTIAL"}


def run_design_study(prepared: dict, *, artifact_root: str | Path,
                     cancel_event=None, progress=None, resume: bool = False,
                     additional_budget_seconds: float = 0,
                     history_references: list | None = None) -> dict:
    """Run bounded points serially, preserving checkpoints and manifest on interruption."""
    from .engineering_workflow import run as run_engineering, import_desktop_runs
    if prepared.get("schema") != SCHEMA:
        raise ValueError("unsupported design-study schema")
    root=Path(artifact_root).resolve();target=study_directory(root,prepared["project_id"],prepared["study_id"])
    manifest_path=target/"study.json"
    immutable={k:v for k,v in prepared.items() if k!="points"}
    immutable_hash=_sha_bytes(_canonical(immutable))
    if target.exists():
        if not resume or not manifest_path.is_file():
            raise FileExistsError("study already exists; select explicit resume to reuse its checkpoints")
        manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("immutable_spec_sha256")!=immutable_hash:
            raise ValueError("resume rejected: study design, baseline, operating point or limits changed")
        if additional_budget_seconds < 0 or additional_budget_seconds > MAX_STUDY_BUDGET_SECONDS:
            raise ValueError("resume budget extension must be between 0 and 600 seconds")
        manifest["total_budget_seconds"]+=float(additional_budget_seconds)
        manifest["effective_point_budget_seconds"]+=float(additional_budget_seconds)
        if manifest["total_budget_seconds"]>2*MAX_STUDY_BUDGET_SECONDS:
            raise ValueError("cumulative study budget is capped at 1200 seconds")
    else:
        target.mkdir(parents=True,exist_ok=False)
        prepared_path=target/"prepared.json"
        _atomic_json(prepared_path,prepared)
        manifest={"schema":SCHEMA,"study_id":prepared["study_id"],"project_id":prepared["project_id"],
            "variant_label":prepared["variant_label"],"status":"PREPARED",
            "created_unix":time.time(),"updated_unix":time.time(),
            "immutable_spec_sha256":immutable_hash,"baseline_engine_identity_sha256":prepared["baseline_engine_identity_sha256"],
            "parameter":prepared["parameter"],"values":prepared["values"],"rpm":prepared["rpm"],
            "max_cycles":prepared["max_cycles"],"point_budget_seconds":prepared["point_budget_seconds"],
            "effective_point_budget_seconds":prepared["point_budget_seconds"],
            "total_budget_seconds":prepared["total_budget_seconds"],"memory_limit_mib":prepared["memory_limit_mib"],
            "prepared_spec_sha256":_sha_bytes(prepared_path.read_bytes()),
            "mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED",
            "periodicity":"EVALUATED_PER_POINT_BY_EXISTING_DETECTOR","elapsed_seconds":0.0,
            "points":[{"index":row["index"],"value":row["value"],"unit":row["unit"],
                "label":row.get("label"),"factor_values":row.get("factor_values"),
                "baseline":row["baseline"],"engine_identity_sha256":row["engine_identity_sha256"],
                "run_id":f"{prepared['study_id']}-p{row['index']:02d}","status":"NOT_STARTED",
                "elapsed_seconds":0.0} for row in prepared["points"]]}
    started=time.monotonic();elapsed_before=float(manifest.get("elapsed_seconds",0))
    def remaining_budget():
        return max(0,float(manifest["total_budget_seconds"])-elapsed_before-(time.monotonic()-started))
    manifest["status"]="RUNNING";manifest["updated_unix"]=time.time();_atomic_json(manifest_path,manifest)
    stop_reason=None
    for index,design_point in enumerate(prepared["points"]):
        row=manifest["points"][index]
        run_dir=root/"exploratory-workflow-v1"/prepared["project_id"]/row["run_id"]
        if row.get("status") in {"COMPLETE","CACHED"}:
            completed_dir=Path(row.get("run_directory") or run_dir)
            try:
                raw=json.loads((completed_dir/"result.json").read_text(encoding="utf-8"))
                run_manifest=json.loads((completed_dir/"run.json").read_text(encoding="utf-8"))
                verified=import_desktop_runs([completed_dir])["points"]
                point_identity=raw.get("bindings",{}).get("identity_sha256")
                if (raw.get("status")!="COMPLETE" or len(verified)!=1 or
                        point_identity!=design_point["preflight"]["identity_sha256"] or
                        row.get("engine_identity_sha256")!=design_point["engine_identity_sha256"] or
                        (row.get("result_sha256") and run_manifest.get("result_sha256")!=row.get("result_sha256")) or
                        (row.get("result_artifact_sha256") and
                         _sha_bytes((completed_dir/"result.json").read_bytes())!=row.get("result_artifact_sha256"))):
                    raise ValueError("completed point identity/artifact does not match the saved design")
                artifact_sha=_sha_bytes((completed_dir/"result.json").read_bytes())
                row.update(solver_status="COMPLETE",identity_sha256=point_identity,
                    result_sha256=run_manifest.get("result_sha256"),result_artifact_sha256=artifact_sha,
                    run_directory=str(completed_dir),classification=raw.get("classification"),
                    periodicity=raw.get("periodicity"),cycles_completed=raw.get("cycles_completed"),
                    elapsed_seconds=raw.get("elapsed_seconds",row.get("elapsed_seconds",0)),reused_verified=True,
                    source_run_id=raw.get("bindings",{}).get("run_id"),
                    status="CACHED" if completed_dir.resolve()!=run_dir.resolve() else "COMPLETE")
                continue
            except Exception as exc:
                row.update(status="FAILED_CLOSED",failure=f"completed point verification failed: {type(exc).__name__}: {exc}")
                stop_reason="FAILED_CLOSED";_atomic_json(manifest_path,manifest);break
        if cancel_event is not None and cancel_event.is_set():
            stop_reason="CANCELLED";break
        remaining=remaining_budget()
        if remaining<=0:
            stop_reason="BUDGET_EXHAUSTED";break
        row["status"]="RUNNING";_atomic_json(manifest_path,manifest)
        if (run_dir/"result.json").is_file() and (run_dir/"run.json").is_file():
            try:
                raw=json.loads((run_dir/"result.json").read_text(encoding="utf-8"))
                run_manifest=json.loads((run_dir/"run.json").read_text(encoding="utf-8"))
                if raw.get("status")!="COMPLETE":raise ValueError("incomplete point requires checkpoint resume")
                verified=import_desktop_runs([run_dir])["points"]
                if len(verified)!=1 or verified[0].get("point_configuration_sha256") is None:
                    raise ValueError("completed point did not contain one verifiable record")
                if raw.get("bindings",{}).get("identity_sha256")!=design_point["preflight"]["identity_sha256"]:
                    raise ValueError("existing point identity differs from the requested design")
                result={"status":raw["status"],"classification":raw["classification"],
                    "periodicity":raw["periodicity"],"cycles_completed":raw["cycles_completed"],
                    "artifact_directory":str(run_dir),"result_sha256":run_manifest["result_sha256"],
                    "identity_sha256":raw["bindings"]["identity_sha256"],"elapsed_seconds":raw.get("elapsed_seconds",0),
                    "reused_verified":True}
            except Exception:
                result=None
        else:result=None
        if result is None:
            result=_verified_historical_match(root,design_point,rpm=prepared["rpm"],
                max_cycles=prepared["max_cycles"],memory_limit_mib=prepared["memory_limit_mib"],
                exclude=run_dir,history_references=history_references)
        if result is None:
            point_remaining=max(0,float(manifest["effective_point_budget_seconds"])-float(row.get("elapsed_seconds",0)))
            if point_remaining<=0:
                row["status"]="POINT_BUDGET_EXHAUSTED";stop_reason="POINT_BUDGET_EXHAUSTED";break
            budget=min(point_remaining,remaining)
            try:
                point_label=design_point.get("label") or f"{prepared['parameter']['label']}={design_point['value']:g} {design_point['unit']}"
                result=run_engineering(design_point["engine_document"],project_id=prepared["project_id"],
                    run_id=row["run_id"],artifact_root=root,rpm=prepared["rpm"],
                    max_cycles=prepared["max_cycles"],budget_seconds=max(1.0,budget),
                    memory_limit_mib=prepared["memory_limit_mib"],
                    resume=run_dir.exists(),cancel_event=cancel_event,
                    variant_label=f"{prepared['study_id']} · {point_label}",
                    progress=(lambda detail, i=index, n=len(prepared["points"]): progress({"study_id":prepared["study_id"],"point_index":i+1,"point_count":n,"value":prepared["points"][i].get("label",prepared["points"][i]["value"]),"rpm":prepared["rpm"],"solver_progress":detail}) if progress else None))
            except Exception as exc:
                row.update(status="FAILED_CLOSED",failure=f"{type(exc).__name__}: {exc}")
                result=None;stop_reason="FAILED_CLOSED"
        if result is not None:
            status=result.get("status")
            result_path=Path(result.get("artifact_directory") or run_dir)/"result.json"
            artifact_sha=_sha_bytes(result_path.read_bytes()) if result_path.is_file() else None
            row.update(status=("CACHED" if result.get("reused_verified") and result.get("historical_source_run_id")
                               else "COMPLETE" if status=="COMPLETE" else status or "UNKNOWN"),
                solver_status=status,classification=result.get("classification"),
                periodicity=result.get("periodicity"),cycles_completed=result.get("cycles_completed"),
                run_directory=str(result.get("artifact_directory") or run_dir),
                identity_sha256=(result.get("identity_sha256") or
                    result.get("bindings",{}).get("identity_sha256")),
                result_sha256=result.get("result_sha256"),
                result_artifact_sha256=artifact_sha,
                # Engineering workflow reports cumulative wall time across its
                # checkpointed invocations, so adding the saved value again
                # would double-count resumed points and exhaust their budget.
                elapsed_seconds=float(result.get("elapsed_seconds",row.get("elapsed_seconds",0))),
                reused_verified=bool(result.get("reused_verified",False)),
                historical_source_run_id=result.get("historical_source_run_id"),
                historical_source_project_id=result.get("historical_source_project_id"),
                history_reuse_policy=result.get("history_reuse_policy"),
                historical_source_reference=result.get("historical_source_reference",False),
                source_run_id=result.get("historical_source_run_id") or row.get("run_id"))
            if status!="COMPLETE":
                stop_reason=("CANCELLED" if cancel_event is not None and cancel_event.is_set()
                             else "POINT_INCOMPLETE")
                _atomic_json(manifest_path,manifest);break
        manifest["elapsed_seconds"]=elapsed_before+(time.monotonic()-started)
        manifest["updated_unix"]=time.time();_atomic_json(manifest_path,manifest)
        if stop_reason=="FAILED_CLOSED":break
        if progress:progress({"study_id":prepared["study_id"],"point_index":index+1,
            "point_count":len(prepared["points"]),"value":design_point.get("label",design_point["value"]),"status":row["status"]})
    else:stop_reason="ALL_POINTS_FINISHED"
    manifest["elapsed_seconds"]=elapsed_before+(time.monotonic()-started)
    all_finished=all(row.get("status") in {"COMPLETE","CACHED"} for row in manifest["points"])
    manifest["status"]="COMPLETE" if all_finished else "CANCELLED" if stop_reason=="CANCELLED" else "PARTIAL"
    manifest["stop_reason"]=stop_reason;manifest["updated_unix"]=time.time();_atomic_json(manifest_path,manifest)
    return {"schema":"DINO_PARAMETRIC_DESIGN_STUDY_RESULT_V1","study_id":prepared["study_id"],
        "status":manifest["status"],"classification":"EXPLORATORY_PARAMETRIC_STUDY",
        "mode":"EXPLORATORY","scientific_validation":"NOT_CLAIMED","periodicity":"PER_POINT",
        "elapsed_seconds":manifest["elapsed_seconds"],"points":[dict(row) for row in manifest["points"]],
        "parallel_manifest":str(manifest_path),"design_study_manifest":str(manifest_path),
        "bindings":{"project_id":prepared["project_id"]},
        "curve_availability":"EXPLORATORY_CURVE_PARTIAL"}


def load_prepared_study(manifest_path: str | Path) -> dict:
    """Rebuild the saved zero-step study only when its immutable files verify."""
    manifest_path=Path(manifest_path).resolve()
    if manifest_path.name!="study.json":raise ValueError("seleccioná el study.json de un estudio paramétrico")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    prepared_path=manifest_path.parent/"prepared.json"
    payload=prepared_path.read_bytes()
    if _sha_bytes(payload)!=manifest.get("prepared_spec_sha256"):
        raise ValueError("el diseño guardado no coincide con el hash del manifiesto")
    prepared=json.loads(payload)
    if prepared.get("schema")!=SCHEMA or prepared.get("study_id")!=manifest.get("study_id"):
        raise ValueError("identidad del estudio guardado inválida")
    for row in prepared.get("points",[]):
        validate(row["engine_document"])
        if identity(row["engine_document"])!=row.get("engine_identity_sha256"):
            raise ValueError("configuración de un punto del estudio modificada")
        from .exploratory_workflow import preflight
        check=preflight(row["engine_document"],rpm=prepared["rpm"],
            max_cycles=prepared["max_cycles"],budget_seconds=prepared["point_budget_seconds"],
            memory_limit_mib=prepared["memory_limit_mib"])
        if check.get("identity_sha256")!=row.get("preflight",{}).get("identity_sha256"):
            raise ValueError("preflight de un punto ya no coincide con su identidad guardada")
    immutable={k:v for k,v in prepared.items() if k!="points"}
    if _sha_bytes(_canonical(immutable))!=manifest.get("immutable_spec_sha256"):
        raise ValueError("la especificación inmutable del estudio no coincide")
    return prepared
