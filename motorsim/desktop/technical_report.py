"""Self-contained engineering reports from already imported Desktop results.

This module is presentation/export only. It never recomputes or changes results.
"""
from __future__ import annotations

from datetime import datetime, timezone
import html
import json
import math
from pathlib import Path

from .presentation import format_number, state_label


METRICS = (
    ("Potencia de freno", "brake_power", "kW"),
    ("Torque de freno", "brake_torque", "N·m"),
    ("BMEP", "BMEP", "kPa"),
)
PERIODIC = {"PERIOD_1", "PERIOD_2"}
COLORS = ("#167d9a", "#d16a32", "#6a8d3b", "#8856a7", "#c04468", "#586879")
CONDITION_FIELDS = (
    "fuel_id", "afr_kg_air_per_kg_fuel", "mesh_resolution",
    "total_finite_volume_cells", "cycles_requested", "solver_identity_sha256",
    "implementation_identity_sha256", "periodicity_contract",
)


def _safe_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def _metric_value(row, metric):
    value = row.get(metric)
    if row.get(metric + "_status") != "DEFINED" or not _safe_number(value):
        return None
    return float(value)


def _reportable(row, metric):
    periodicity = row.get("periodicity")
    if periodicity is None and row.get("classification") in PERIODIC:
        periodicity = row.get("classification")
    return periodicity in PERIODIC and _metric_value(row, metric) is not None


def _condition_status(left, right):
    different = [key for key in CONDITION_FIELDS
                 if left.get(key) is not None and right.get(key) is not None
                 and left.get(key) != right.get(key)]
    missing = [key for key in CONDITION_FIELDS
               if left.get(key) is None or right.get(key) is None]
    if different:
        return "Campos distintos: " + ", ".join(different)
    if missing:
        return "No verificable; faltan: " + ", ".join(missing)
    return "Coinciden los campos de operación informados"


def _esc(value):
    if value is None:
        return "No informado"
    return html.escape(str(value), quote=True)


def _chart_svg(rows, variants, label, metric, unit):
    eligible = [row for row in rows if _reportable(row, metric)]
    width, height = 760, 330
    left, top, right, bottom = 72, 34, 22, 58
    plot_w, plot_h = width - left - right, height - top - bottom
    if not eligible:
        return (f'<section><h3>{_esc(label)}</h3><p class="empty">'
                'No hay puntos clasificados PERIOD_1/PERIOD_2 con la métrica definida.</p></section>')
    rpms = [float(row["rpm"]) for row in eligible]
    vals = [_metric_value(row, metric) for row in eligible]
    xmin, xmax = min(rpms), max(rpms)
    ymin, ymax = min(vals), max(vals)
    if xmax == xmin:
        xmin -= 1; xmax += 1
    if ymax == ymin:
        pad = max(abs(ymax) * .05, 1e-9); ymin -= pad; ymax += pad
    else:
        pad = (ymax - ymin) * .08; ymin -= pad; ymax += pad
    x = lambda value: left + (float(value) - xmin) / (xmax - xmin) * plot_w
    y = lambda value: top + (ymax - float(value)) / (ymax - ymin) * plot_h
    parts = [f'<section><h3>{_esc(label)}</h3><svg role="img" aria-label="{_esc(label)} por RPM" '
             f'viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
             f'<rect width="{width}" height="{height}" fill="#fff"/>',
             f'<path d="M{left} {top}V{top+plot_h}H{left+plot_w}" fill="none" stroke="#526273"/>']
    for index in range(5):
        fy = top + plot_h * index / 4
        value = ymax - (ymax - ymin) * index / 4
        parts.append(f'<path d="M{left} {fy:.2f}H{left+plot_w}" stroke="#e1e7ec"/>')
        parts.append(f'<text x="{left-8}" y="{fy+4:.2f}" text-anchor="end">{_esc(format_number(value))}</text>')
        rpm = xmin + (xmax - xmin) * index / 4
        fx = left + plot_w * index / 4
        parts.append(f'<text x="{fx:.2f}" y="{top+plot_h+22}" text-anchor="middle">{_esc(format_number(rpm))}</text>')
    parts.append(f'<text x="{left+plot_w/2}" y="{height-10}" text-anchor="middle">RPM</text>')
    parts.append(f'<text transform="translate(17 {top+plot_h/2}) rotate(-90)" text-anchor="middle">{_esc(unit)}</text>')
    for index, variant in enumerate(variants):
        color = COLORS[index % len(COLORS)]
        points = [row for row in eligible if str(row.get("variant_id")) == variant]
        for row in points:
            cx, cy = x(row["rpm"]), y(_metric_value(row, metric))
            parts.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="5" fill="{color}"><title>'
                         f'{_esc(variant)} · {_esc(format_number(row["rpm"]))} RPM · '
                         f'{_esc(format_number(_metric_value(row, metric)))} {unit}</title></circle>')
        lx = left + index * min(190, plot_w / max(len(variants), 1))
        parts.append(f'<circle cx="{lx+5:.2f}" cy="{top-12}" r="5" fill="{color}"/>')
        parts.append(f'<text x="{lx+15:.2f}" y="{top-8}">{_esc(variant)}</text>')
    parts.append('</svg><p class="note">Marcadores = puntos disponibles. No hay interpolación. '
                 'La clasificación periódica observada no equivale a validación experimental.</p></section>')
    return "".join(parts)


def render_technical_report(dataset: dict, *, source_kind: str,
                            selected_variants=None, source_path=None,
                            active_project_id=None, generated_at=None,
                            design_study_manifest=None,
                            design_study_manifest_path=None,
                            factorial_effects=None) -> str:
    """Render exact selected result records and an explicit evidence boundary."""
    points = dataset.get("points") if isinstance(dataset, dict) else None
    if not isinstance(points, list) or not points:
        raise ValueError("No hay puntos cargados para documentar.")
    variants = sorted({str(row.get("variant_id") or "Variante no informada") for row in points})
    selected = set(str(value) for value in (selected_variants or variants))
    variants = [name for name in variants if name in selected]
    rows = [row for row in points if str(row.get("variant_id") or "Variante no informada") in selected]
    if not rows:
        raise ValueError("La selección actual no contiene puntos para documentar.")

    kind_labels = {
        "HISTORICAL_IMPL2": "Datos históricos sintéticos; no son mediciones experimentales.",
        "LEGACY_HISTORICAL": "Resumen histórico heredado; conserva los campos presentes en el artefacto.",
        "EXPLORATORY": "Corridas exploratorias; los transitorios no se presentan como prestaciones definitivas.",
        "IMPORTED_EXTERNAL": "Resultados importados; su origen se limita a la procedencia declarada en el artefacto.",
    }
    origin = kind_labels.get(source_kind, "Origen no clasificado por la interfaz; consultar procedencia original.")
    validation = dataset.get("experimental_validation", "NOT_REPORTED")
    generated_at = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    if source_path:
        source_path = Path(source_path)
        source_entries = [source_path]
        if source_path.suffix.lower() == ".csv" and source_path.with_suffix(".json").is_file():
            source_entries.append(source_path.with_suffix(".json"))
    else:
        source_entries = [Path(path) for path in dataset.get("source_paths", [])
                          if isinstance(path, str)]
    source_rows = []
    for path in source_entries:
        try:
            digest = __import__("hashlib").sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        except OSError:
            digest = None
        source_rows.append(f"<tr><td>{_esc(path)}</td><td>{digest or 'No disponible'}</td></tr>")
    if not source_rows:
        source_rows.append("<tr><td>Ruta de origen no conservada por el importador</td><td>No disponible</td></tr>")
    study_html = ""
    if design_study_manifest is not None:
        manifest = design_study_manifest
        if not isinstance(manifest, dict) or manifest.get("schema") != "DINO_PARAMETRIC_DESIGN_STUDY_V1":
            raise ValueError("El manifiesto de estudio no tiene un esquema reconocido.")
        is_rpm_envelope=manifest.get("design_method")=="RPM_ENVELOPE_V1"
        rpm_groups={group.get("index"):group for group in manifest.get("groups",[]) if isinstance(group,dict)}
        parameter = manifest.get("parameter") or {}
        study_rows = []
        for point in manifest.get("points", []):
            value = point.get("value")
            shown_value = format_number(value) if _safe_number(value) else "No informado"
            factors = point.get("factor_values")
            if isinstance(factors,list) and factors:
                shown_value = " · ".join(
                    f"{_esc(item.get('label') or item.get('parameter_id'))}="
                    f"{_esc(format_number(item.get('value')) if _safe_number(item.get('value')) else 'No informado')} "
                    f"{_esc(item.get('unit') or '')}" for item in factors if isinstance(item,dict))
            identity_sha = point.get("engine_identity_sha256") or "No disponible"
            source_run = point.get("source_run_id") or point.get("historical_source_run_id") or point.get("run_id")
            design_index=point.get("design_index")
            rpm_group=rpm_groups.get(design_index,{}) if is_rpm_envelope else {}
            sweep_path=point.get("sweep_manifest") or rpm_group.get("sweep_manifest")
            sweep_digest=point.get("sweep_manifest_sha256") or rpm_group.get("sweep_manifest_sha256")
            study_rows.append("<tr>" + "".join((
                f"<td>{_esc(point.get('index',design_index))}</td>",
                f"<td>{_esc(point.get('status') or 'No ejecutado')}</td>",
                f"<td>{_esc(format_number(point.get('rpm',manifest.get('rpm'))) if _safe_number(point.get('rpm',manifest.get('rpm'))) else 'No informada')}</td>",
                f"<td>{_esc(state_label(point.get('classification') or point.get('status') or 'NOT_REPORTED'))}</td>",
                f"<td>{_esc(state_label(point.get('periodicity') or 'NOT_EVALUATED'))}</td>",
                f"<td>{_esc(point.get('cycles_completed') if point.get('cycles_completed') is not None else '—')}</td>",
                f"<td>{shown_value if isinstance(factors,list) and factors else _esc(shown_value)+' '+_esc(point.get('unit') or parameter.get('unit') or '')}</td>",
                f"<td>{_esc(source_run or 'No informado')}</td>",
                f"<td>{_esc(point.get('historical_source_project_id') or 'No informado')}</td>",
                f"<td><code>{_esc(point.get('run_directory') or 'No informada')}</code></td>",
                f"<td><code>{_esc(point.get('result_sha256') or 'No disponible')}</code></td>",
                f"<td><code>{_esc(point.get('result_artifact_sha256') or 'No disponible')}</code></td>",
                f"<td><code>{_esc(sweep_path or 'No informada')}</code></td>",
                f"<td><code>{_esc(sweep_digest or 'No disponible')}</code></td>",
                f"<td>{'Sí' if point.get('reused_verified') else 'No'}</td>",
                f"<td><code>{_esc(identity_sha)}</code></td>")) + "</tr>")
        manifest_path = Path(design_study_manifest_path) if design_study_manifest_path else None
        manifest_digest = None
        if manifest_path:
            try:
                manifest_raw=manifest_path.read_bytes()
                manifest_digest=__import__("hashlib").sha256(manifest_raw).hexdigest()
                if is_rpm_envelope and json.loads(manifest_raw.decode("utf-8"))!=manifest:
                    raise ValueError("El manifiesto RPM cambió desde que se abrió; vuelva a cargar el estudio antes de exportar.")
                if is_rpm_envelope:
                    for group in manifest.get("groups",[]):
                        sweep_path=group.get("sweep_manifest")
                        sweep_digest=group.get("sweep_manifest_sha256")
                        if group.get("status")=="COMPLETE" and (not sweep_path or not sweep_digest):
                            raise ValueError("Un diseño RPM terminado carece de ruta/hash de manifiesto de barrido.")
                        if sweep_path and sweep_digest:
                            sweep_raw=Path(sweep_path).read_bytes()
                            actual=__import__("hashlib").sha256(sweep_raw).hexdigest()
                            if actual!=sweep_digest:
                                raise ValueError("Cambió el hash del manifiesto de barrido; vuelva a cargar el estudio antes de exportar.")
            except OSError as exc:
                if is_rpm_envelope:raise ValueError(f"No se pudo verificar el manifiesto RPM: {exc}") from exc
        elif is_rpm_envelope:
            raise ValueError("El informe de envolvente RPM necesita la ruta del manifiesto de origen.")
        manifest_origin = (f"<p>Manifiesto: <code>{_esc(manifest_path)}</code> · SHA-256 actual: "
                           f"<code>{_esc(manifest_digest or 'No disponible')}</code></p>" if manifest_path else
                           "<p>Manifiesto adjuntado como objeto por la interfaz; ruta original no informada.</p>")
        study_raw = html.escape(json.dumps(manifest, ensure_ascii=False, allow_nan=False,
                                           sort_keys=True, indent=2), quote=False)
        envelope_summary=""
        if is_rpm_envelope:
            values=manifest.get("values",[]);rpms=manifest.get("rpms",[])
            envelope_summary=("<h3>Envolvente geometría × RPM · observaciones exactas</h3>"
                f"<p>Método <code>RPM_ENVELOPE_V1</code> · diseños guardados: {_esc(len(values))} · "
                f"RPM exactas: {_esc(', '.join(format_number(value) for value in rpms))} · "
                f"puntos guardados: {_esc(len(manifest.get('points',[])))}. "
                "Cada fila es una observación del manifiesto. No se interpolan puntos ni se calculan resúmenes de rendimiento desde el manifiesto; las métricas sólo aparecen en resultados importados individualmente y periódicos. "
                f"Validación científica: <strong>{_esc(state_label(manifest.get('scientific_validation','NOT_CLAIMED')))}</strong>.</p>")
        factorial_html=""
        if manifest.get("design_method")=="FACTORIAL_2X2_V1":
            if (not isinstance(factorial_effects,dict) or
                    factorial_effects.get("schema")!="DINO_PARAMETRIC_FACTORIAL_EFFECTS_V1" or
                    factorial_effects.get("study_id")!=manifest.get("study_id")):
                factorial_effects={"status":"UNAVAILABLE","reason":"No se proporcionó un contraste con fuentes verificadas.","metrics":[]}
            effect_rows=[]
            for metric in factorial_effects.get("metrics",[]):
                for effect in metric.get("effects",[]):
                    value=effect.get("value")
                    shown=(f"{format_number(value,signed=True)} {_esc(effect.get('unit') or metric.get('unit') or '')}"
                        if _safe_number(value) else "—")
                    effect_rows.append("<tr>"+"".join((f"<td>{_esc(metric.get('label'))}</td>",
                        f"<td>{_esc(effect.get('term'))}</td>",f"<td>{shown}</td>",
                        f"<td>{_esc(metric.get('reason') or factorial_effects.get('reason') or 'Descriptivo · no validado')}</td>",
                        f"<td><code>{_esc(effect.get('formula'))}</code></td>"))+"</tr>")
            if not effect_rows:
                effect_rows.append(f"<tr><td colspan=\"5\">{_esc(factorial_effects.get('reason') or 'Contrastes no disponibles.')}</td></tr>")
            factor_names=" × ".join(str(axis.get("label") or axis.get("id")) for axis in manifest.get("parameter",{}).get("axes",[]))
            effect_state=("Descriptivos disponibles · no validados" if factorial_effects.get("status")=="AVAILABLE"
                else "No disponibles")
            factorial_html=("<h3>Contrastes factoriales 2×2 · descriptivos</h3>"
                f"<p>Diseño { _esc(factor_names or 'dos factores') }. Los efectos principales usan la media de cada nivel frente al otro; "
                "la interacción es la diferencia de diferencias indicada en la fórmula. Sólo se calculan con cuatro artifacts verificados, "
                "condiciones compatibles, métricas definidas y periodicidad PERIOD_1. No implican causalidad ni validación predictiva. "
                f"Estado: <strong>{_esc(effect_state)}</strong> · "
                f"{_esc(factorial_effects.get('reason') or '')}</p>"
                "<table><thead><tr><th>Métrica</th><th>Contraste</th><th>Valor</th><th>Estado</th><th>Definición exacta</th></tr></thead>"
                f"<tbody>{''.join(effect_rows)}</tbody></table>")
        study_html = ("<h2>Estudio paramétrico asociado</h2>"
            f"<p>Estudio <code>{_esc(manifest.get('study_id'))}</code>; parámetro "
            f"<strong>{_esc(parameter.get('label') or parameter.get('id') or 'No informado')}</strong>; "
            f"estado {_esc(state_label(manifest.get('status')))}. Los puntos conservan su clasificación de ejecución; "
            "la finalización del estudio no implica periodicidad ni validación científica.</p>"
            f"{manifest_origin}{envelope_summary}{factorial_html}<table><thead><tr><th>Punto</th><th>Estado de ejecución</th>"
            "<th>RPM</th><th>Clasificación</th><th>Periodicidad</th><th>Ciclos</th><th>Valor(es)</th>"
            f"<th>Run de origen</th><th>Proyecto de origen</th><th>Ruta de resultado</th>"
            f"<th>Resultado SHA-256</th><th>Artefacto SHA-256</th><th>Manifiesto sweep</th>"
            f"<th>Manifiesto sweep SHA-256</th><th>Reuso verificado</th>"
            f"<th>Identidad de motor SHA-256</th></tr></thead><tbody>{''.join(study_rows)}</tbody></table>"
            f"<details><summary>Manifiesto paramétrico original adjunto (JSON)</summary><pre>{study_raw}</pre></details>")
    source_sha = dataset.get("source_sha256")
    source_hash_html = f"<p>Hash de origen registrado: <code>{_esc(source_sha)}</code></p>" if source_sha else ""

    body_rows = []
    identity_rows = []
    for row in sorted(rows, key=lambda item: (str(item.get("variant_id")),
                                               float(item.get("rpm") or 0), str(item.get("run_id") or ""))):
        metric_cells = []
        for _, metric, unit in METRICS:
            value = _metric_value(row, metric)
            metric_cells.append(f"<td>{_esc(format_number(value) if value is not None else state_label(row.get(metric+'_status') or 'UNDEFINED'))}{(' ' + unit) if value is not None else ''}</td>")
        periodicity = row.get("periodicity") or row.get("classification")
        transient = row.get("transient_estimates")
        transient_note = " · estimación transitoria disponible" if isinstance(transient, dict) and transient else ""
        body_rows.append("<tr>" + "".join([
            f"<td>{_esc(row.get('variant_id'))}</td>",
            f"<td>{_esc(format_number(row.get('rpm')))} RPM</td>",
            f"<td>{_esc(state_label(row.get('classification')))}</td>",
            f"<td>{_esc(state_label(periodicity))}{transient_note}</td>",
            f"<td>{_esc(state_label(row.get('audit_status') or 'NOT_REPORTED'))}</td>",
            f"<td>{_esc(row.get('cycles_completed') if row.get('cycles_completed') is not None else '—')}</td>",
            *metric_cells,
        ]) + "</tr>")
        identity_rows.append("<tr>" + "".join(f"<td>{_esc(row.get(key))}</td>" for key in (
            "variant_id", "rpm", "run_id", "point_id", "artifact_directory",
            "result_sha256", "primary_sha256", "point_configuration_sha256",
        )) + "</tr>")

    comparisons = []
    for left_index, left_name in enumerate(variants):
        for right_name in variants[left_index + 1:]:
            left_rows = {row.get("rpm"): row for row in rows if str(row.get("variant_id")) == left_name}
            right_rows = {row.get("rpm"): row for row in rows if str(row.get("variant_id")) == right_name}
            for rpm in sorted(left_rows.keys() & right_rows.keys(), key=float):
                left, right = left_rows[rpm], right_rows[rpm]
                for label, metric, unit in METRICS:
                    if _reportable(left, metric) and _reportable(right, metric):
                        delta = _metric_value(right, metric) - _metric_value(left, metric)
                        comparisons.append(f"<tr><td>{_esc(left_name)} → {_esc(right_name)}</td>"
                            f"<td>{_esc(format_number(rpm))} RPM</td><td>{_esc(label)}</td>"
                            f"<td>{_esc(format_number(delta, signed=True))} {unit}</td>"
                            f"<td>{_esc(_condition_status(left, right))}</td></tr>")
    comparison_html = "".join(comparisons) or '<tr><td colspan="5">No hay pares A/B con RPM exacta común y métricas definidas en puntos periódicos observados.</td></tr>'
    chart_html = "".join(_chart_svg(rows, variants, label, metric, unit)
                         for label, metric, unit in METRICS[:2])
    exact_records = json.dumps(rows, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2)
    raw_record_html = html.escape(exact_records, quote=False)
    active_project = f"<p>Proyecto abierto al exportar: <code>{_esc(active_project_id)}</code>. " \
                     "Este contexto no reasigna la procedencia de las corridas.</p>" if active_project_id else ""
    provenance = dataset.get("provenance", "No informada")
    schema = dataset.get("schema", "No informado")
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe técnico Dino 2T</title><style>
body{{font:15px/1.5 "Segoe UI",Arial,sans-serif;color:#202b36;max-width:1180px;margin:24px auto;padding:0 20px}}
h1,h2,h3{{color:#173d57}}.boundary{{border-left:5px solid #c18420;background:#fff6df;padding:12px 16px}}
table{{border-collapse:collapse;width:100%;margin:14px 0 24px;font-size:13px}}th,td{{border:1px solid #ccd5dc;padding:7px;text-align:left;vertical-align:top}}
th{{background:#edf2f6}}code,pre{{font-family:Consolas,monospace}}pre{{overflow:auto;background:#f3f5f7;padding:12px;white-space:pre-wrap;word-break:break-word}}
svg{{width:100%;height:auto;border:1px solid #d4dbe1}}svg text{{font:12px Arial;fill:#273746}}.note,.muted{{color:#536273;font-size:13px}}.empty{{padding:24px;background:#f3f5f7}}
@media print{{body{{max-width:none;margin:0}}details{{break-before:page}}}}
</style></head><body>
<h1>Informe técnico de resultados · Dino 2T</h1>
<div class="boundary"><strong>Límite de evidencia.</strong> {_esc(origin)} Validación experimental: <strong>{_esc(state_label(validation))}</strong>. La observación de periodicidad no valida predicción física. Los marcadores de desempeño incluyen sólo filas PERIOD_1/PERIOD_2 con métrica definida; los transitorios permanecen identificados y fuera de esos gráficos.</div>
<p>Generado UTC: {_esc(generated_at)} · Formato de datos: <code>{_esc(schema)}</code> · Procedencia declarada: {_esc(provenance)}</p>
{active_project}{source_hash_html}<h2>Origen y reproducibilidad</h2><table><thead><tr><th>Archivo fuente</th><th>SHA-256 actual</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table>
<p>Las filas completas seleccionadas se incluyen al final sin redondear. Las tablas y gráficos de este informe son una vista legible de esos datos; no recalculan el solver.</p>
{study_html}
<h2>Resultados por variante y RPM</h2><table><thead><tr><th>Variante</th><th>Condición</th><th>Estado</th><th>Periodicidad</th><th>Auditoría</th><th>Ciclos</th><th>Potencia</th><th>Torque</th><th>BMEP</th></tr></thead><tbody>{''.join(body_rows)}</tbody></table>
<h2>Identidad y procedencia por punto</h2><table><thead><tr><th>Variante</th><th>RPM</th><th>Run ID</th><th>Point ID</th><th>Carpeta de artifacts</th><th>Resultado SHA-256</th><th>Primario SHA-256</th><th>Configuración SHA-256</th></tr></thead><tbody>{''.join(identity_rows)}</tbody></table>
<h2>Comparación entre variantes</h2><p class="muted">Sólo RPM exactas comunes. Δ = segunda variante menos primera; es un contraste descriptivo, no una atribución causal. No se interpolan puntos. Las diferencias y ausencias en los campos de operación se indican por fila. Se incluyen métricas definidas únicamente en resultados periódicos observados.</p>
<table><thead><tr><th>Par</th><th>RPM</th><th>Métrica</th><th>Δ descriptivo</th><th>Consistencia de condiciones informadas</th></tr></thead><tbody>{comparison_html}</tbody></table>
<h2>Visualización de puntos periódicos observados</h2>{chart_html}
<details><summary>Registros originales exactos seleccionados (JSON)</summary><pre>{raw_record_html}</pre></details>
<footer class="muted">Dino 2T Desktop · documento local autosuficiente · no implica validación experimental ni recomendación comercial.</footer>
</body></html>'''


def write_technical_report(path, dataset: dict, **kwargs) -> Path:
    path = Path(path)
    document = render_technical_report(dataset, **kwargs)
    path.write_text(document, encoding="utf-8")
    return path


def render_study_comparison_report(comparison: dict) -> str:
    """Render a hash-bound comparison of verified saved-study observations."""
    if (not isinstance(comparison,dict) or
            comparison.get("schema")!="DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1" or
            not isinstance(comparison.get("studies"),list) or len(comparison["studies"])<2):
        raise ValueError("La comparación de estudios no tiene un esquema verificable.")
    studies=[]
    point_rows=[]
    for study in comparison["studies"]:
        if study.get("baseline_engine_identity_sha256")!=comparison.get("baseline_engine_identity_sha256"):
            raise ValueError("La comparación contiene baselines incompatibles.")
        studies.append("<tr>"+"".join((f"<td>{_esc(study.get('study_id'))}</td>",
            f"<td>{_esc(study.get('source_project_id'))}</td>",
            f"<td><code>{_esc(study.get('manifest_path'))}</code></td>",
            f"<td><code>{_esc(study.get('manifest_sha256'))}</code></td>"))+"</tr>")
        for point in study.get("points",[]):
            metrics=point.get("metrics",{})
            factor=point.get("factor_values") or []
            design=(" · ".join(f"{_esc(row.get('label') or row.get('parameter_id'))}="
                f"{_esc(format_number(row.get('value')) if _safe_number(row.get('value')) else 'No informado')} "
                f"{_esc(row.get('unit') or '')}" for row in factor if isinstance(row,dict))
                if factor else f"{_esc((study.get('parameter') or {}).get('label') or 'Diseño')}="
                f"{_esc(format_number(point.get('value')) if _safe_number(point.get('value')) else 'No informado')} "
                f"{_esc(point.get('unit') or (study.get('parameter') or {}).get('unit') or '')}")
            cells=[study.get("study_id"),design,point.get("rpm"),point.get("status"),
                point.get("classification"),point.get("periodicity"),point.get("cycles_completed"),
                point.get("source_run_id"),point.get("engine_identity_sha256"),point.get("identity_sha256"),
                point.get("result_sha256"),point.get("result_artifact_sha256"),point.get("run_directory"),
                "Sí" if point.get("source_verified") else "No"]
            metric_cells=[]
            for metric,(_,unit) in _STUDY_REPORT_METRICS.items():
                value=metrics.get(metric)
                metric_cells.append(f"<td>{_esc(format_number(value) if _safe_number(value) else '—')}{(' '+_esc(unit)) if _safe_number(value) else ''}</td>")
            point_rows.append("<tr>"+"".join(f"<td>{_esc(value if value is not None else 'No informado')}</td>" for value in cells)+"".join(metric_cells)+"</tr>")
    pair_rows=[]
    for pair in comparison.get("pairs",[]):
        for metric,(label,unit) in _STUDY_REPORT_METRICS.items():
            detail=pair.get("metrics",{}).get(metric,{})
            delta=detail.get("delta")
            pair_rows.append("<tr>"+"".join((f"<td>{_esc(pair.get('study_a'))}</td>",
                f"<td>{_esc(pair.get('point_a',{}).get('run_id'))}</td>",
                f"<td>{_esc(pair.get('study_b'))}</td>",
                f"<td>{_esc(pair.get('point_b',{}).get('run_id'))}</td>",
                f"<td>{_esc(format_number(pair.get('rpm')))} RPM</td>",f"<td>{_esc(label)}</td>",
                f"<td>{_esc(format_number(delta,signed=True) if _safe_number(delta) else '—')}{(' '+_esc(unit)) if _safe_number(delta) else ''}</td>",
                f"<td>{_esc(pair.get('pairing'))}</td>"))+"</tr>")
    unpaired_rows=[]
    for item in comparison.get("unpaired",[]):
        point=item.get("point",{})
        unpaired_rows.append("<tr>"+"".join((f"<td>{_esc(item.get('study_id'))}</td>",
            f"<td>{_esc(point.get('run_id'))}</td>",f"<td>{_esc(format_number(point.get('rpm')))} RPM</td>",
            f"<td>{_esc(state_label(point.get('classification') or point.get('status')))}</td>",
            f"<td>{_esc(state_label(point.get('periodicity') or 'NOT_EVALUATED'))}</td>",
            f"<td>{_esc(point.get('engine_identity_sha256'))}</td>",f"<td>{_esc(item.get('reason'))}</td>"))+"</tr>")
    payload=html.escape(json.dumps(comparison,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False),quote=False)
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Comparación paramétrica · Dino 2T</title>
<style>body{{font:15px Segoe UI,Arial,sans-serif;color:#172536;margin:28px;max-width:1500px}}h1,h2{{color:#173852}}.notice{{padding:14px;background:#fff3dc;border-left:5px solid #cc7b18}}table{{border-collapse:collapse;width:100%;margin:12px 0 24px;font-size:12px}}th,td{{border:1px solid #becbd7;padding:6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}th{{background:#e9f0f5}}code{{font-size:11px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f6f8;padding:16px}}footer{{color:#526477}}</style></head><body>
<h1>Comparación de estudios paramétricos · Dino 2T</h1>
<p class="notice"><strong>Límite de evidencia.</strong> { _esc(comparison.get('notice')) } La validación científica no está reclamada. Las diferencias son contrastes descriptivos entre puntos observados; no se interpolan, ajustan ni agregan.</p>
<p>Baseline común: <code>{_esc(comparison.get('baseline_engine_identity_sha256'))}</code> · generación UTC: {_esc(datetime.now(timezone.utc).isoformat(timespec='seconds'))}</p>
<h2>Manifiestos seleccionados</h2><table><thead><tr><th>Estudio</th><th>Proyecto fuente</th><th>Ruta del manifiesto</th><th>SHA-256 del manifiesto</th></tr></thead><tbody>{''.join(studies)}</tbody></table>
<h2>Puntos y procedencia</h2><table><thead><tr><th>Estudio</th><th>Diseño</th><th>RPM</th><th>Estado ejecución</th><th>Clasificación</th><th>Periodicidad</th><th>Ciclos</th><th>Run fuente</th><th>Motor SHA-256</th><th>Corrida SHA-256</th><th>Resultado SHA-256</th><th>Artifact SHA-256</th><th>Ruta</th><th>Fuente verificada</th><th>Potencia</th><th>Torque</th><th>BMEP</th></tr></thead><tbody>{''.join(point_rows)}</tbody></table>
<h2>Contrastes exactos</h2><p>Los pares requieren RPM y todos los campos operativos informados compatibles. Δ = estudio B menos A. Un resultado queda vacío si falta o si no es periódico y definido.</p><table><thead><tr><th>Estudio A</th><th>Run A</th><th>Estudio B</th><th>Run B</th><th>RPM</th><th>Métrica</th><th>Δ</th><th>Regla de pareo</th></tr></thead><tbody>{''.join(pair_rows) or '<tr><td colspan="8">No hay pares compatibles exactos.</td></tr>'}</tbody></table>
<h2>Puntos sin contraparte</h2><table><thead><tr><th>Estudio</th><th>Run ID</th><th>RPM</th><th>Clasificación</th><th>Periodicidad</th><th>Motor SHA-256</th><th>Motivo</th></tr></thead><tbody>{''.join(unpaired_rows) or '<tr><td colspan="7">Todos los puntos aparecen en al menos un pareo.</td></tr>'}</tbody></table>
<h2>Datos reproducibles</h2><details><summary>Objeto completo de comparación, puntos y source manifests</summary><pre>{payload}</pre></details>
<footer>Dino Desktop · exportación descriptiva. Los resultados transitorios no representan prestaciones periódicas; la periodicidad tampoco constituye validación experimental.</footer></body></html>'''


_STUDY_REPORT_METRICS={"brake_power":("Potencia de freno","kW"),
    "brake_torque":("Torque de freno","N·m"),"BMEP":("BMEP","kPa")}


def write_study_comparison_report(path, comparison: dict) -> Path:
    path=Path(path)
    path.write_text(render_study_comparison_report(comparison),encoding="utf-8")
    return path
