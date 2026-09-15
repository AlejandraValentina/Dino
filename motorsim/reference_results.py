"""Contrato pequeño de resultados del caso fijo; biblioteca estándar, sin Qt."""
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import uuid

from .adaptive import PROFILES
from .simulation import CV, Model, balances_ok
from .simulation_case import SyntheticCase
from .prototype import write_json

PROFILE = PROFILES[1]
BAND_PA = 100
MODEL_VERSION = 'four-cv-0d-prescribed-heat-v1-external-regularized-rk4-v1'
UNITS = dict(angle='deg continuous', pressure='Pa absolute', volume='m3',
             mass='kg', energy='J', time='s', temperature='K', fresh_fraction='1')
FILES = ('case.json', 'summary.json', 'samples.json')


class ResultError(ValueError):
    pass


def reference_inputs():
    model = Model(external_band_pa=BAND_PA)
    return json.loads(json.dumps(dict(case=model.case.manifest(), profile=asdict(PROFILE),
        variant=dict(external_links=[0, 5], delta_p_Pa=BAND_PA, calibrated=False),
        model_version=MODEL_VERSION, initial_state=model.initial_state()[:12])))


def new_output_path():
    root = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'.local/share')))/'MotorSim'/'Resultados'
    return root/(datetime.now().strftime('%Y%m%d-%H%M%S-')+uuid.uuid4().hex[:10])


def save_result(folder, result, status, inputs, environment):
    """El llamador crea una carpeta exclusiva; manifiesto escrito al final."""
    run_id = uuid.uuid4().hex
    compact = {k: v for k, v in result.items() if k not in ('last_two_cycles', 'partial')}
    partial = result.get('partial')
    if partial:
        compact['partial'] = {k: v for k, v in partial.items() if k != 'samples'}
    payloads = [dict(inputs=inputs), dict(status=status, result=compact, environment=environment),
                dict(cycles=result.get('last_two_cycles', []), partial=partial.get('samples', []) if partial else [])]
    hashes = {}
    for name, payload in zip(FILES, payloads):
        write_json(folder/name, dict(run_id=run_id, **payload))
        hashes[name] = hashlib.sha256((folder/name).read_bytes()).hexdigest()
    write_json(folder/'manifest.json', dict(format='motorsim-reference-result', version=1,
               model_version=MODEL_VERSION, run_id=run_id, units=UNITS, files=hashes))


def _require(condition, text):
    if not condition:
        raise ResultError(text)


def _finite(value):
    if isinstance(value, dict):
        for v in value.values():
            _finite(v)
    elif isinstance(value, list):
        for v in value:
            _finite(v)
    elif type(value) in (float, int):
        _require(math.isfinite(value), 'Valor no finito.')


def _number(value, minimum=None):
    _require(type(value) in (int, float) and math.isfinite(value), 'Se esperaba un número finito.')
    _require(minimum is None or value >= minimum, 'Número fuera de rango.')


def _vector(value, length):
    _require(isinstance(value, list) and len(value) == length, 'Dimensión de datos incorrecta.')
    for item in value:
        _number(item)


def _balances(value):
    _require(isinstance(value, dict) and set(value) == set(CV)|{'global'}, 'Volúmenes del balance incorrectos.')
    for record in value.values():
        _vector(record['normalized_m_u_f'], 3)
        _vector(record['residual_kg_j_kg'], 3)
        _require(min(record['normalized_m_u_f']) >= 0, 'Residuo normalizado negativo.')


def _cycle(cycle, index):
    _require(cycle['cycle'] == index, 'Secuencia de ciclos incorrecta.')
    _vector(cycle['state'], 12)
    _vector(cycle['Y'], 4)
    _vector(cycle['net_link_mass_kg'], 6)
    for key in ('W_C_J', 'W_K_J', 'p_max_Pa', 'F_s_kg', 'Q_J', 'converted_kg'):
        _number(cycle[key])
    _require(1000 <= cycle['p_max_Pa'] <= 2e7, 'Presión máxima fuera del dominio.')
    for j in range(4):
        m, u, f = cycle['state'][3*j:3*j+3]
        _require(m > 0 and u > 0 and 0 <= f <= m and 0 <= cycle['Y'][j] <= 1
                 and math.isclose(cycle['Y'][j], f/m, rel_tol=1e-10, abs_tol=1e-14),
                 'Inventario final no físico o incoherente.')
    for key in ('discrete', 'independent'):
        _balances(cycle[key])
    valid = balances_ok(cycle['discrete'], cycle['independent'])
    _require(type(cycle['balances_passed']) is bool and cycle['balances_passed'] == valid,
             'Estado de balances contradictorio.')
    conv = cycle['convergence']
    _require(type(conv['passed']) is bool, 'Convergencia ilegible.')
    if conv['passed']:
        _require(valid and cycle['F_s_kg'] > 0 and cycle['Q_J'] > 0, 'Convergencia sin balances/aporte.')
        for key, limit in (('m_relative', .002), ('U_relative', .002), ('Y_absolute', .002),
                           ('W_relative', .005), ('p_curve_relative', .005)):
            _number(conv[key], 0)
            _require(conv[key] <= limit, 'Convergencia fuera de criterio.')


def _samples(rows, complete, cycle=None):
    case = SyntheticCase()
    _require(isinstance(rows, list) and len(rows) <= 721, 'Muestras incorrectas.')
    if complete:
        _require(len(rows) == 721, 'Ciclo de muestras incompleto.')
    for i, row in enumerate(rows):
        for key in ('angle_deg', 'time_s', 'W_C_J', 'W_K_J', 'Q_J', 'converted_kg'):
            _number(row[key])
        _vector(row['state'], 12)
        _vector(row['V_m3'], 4)
        _require(len(row['p_T_Y']) == 4 and len(row['flows_kg_s_W_kg_s']) == 6, 'Muestras de CV/enlaces incorrectas.')
        for node in row['p_T_Y']:
            _vector(node, 3)
            _require(1000 <= node[0] <= 2e7 and 100 <= node[1] <= 4000 and 0 <= node[2] <= 1,
                     'Estado físico fuera de dominio.')
        for flow in row['flows_kg_s_W_kg_s']:
            _vector(flow, 3)
        for j in range(4):
            m, u, f = row['state'][3*j:3*j+3]
            volume = row['V_m3'][j]
            _require(m > 0 and u > 0 and 0 <= f <= m and volume > 0, 'Inventario no físico.')
            p, t, y = row['p_T_Y'][j]
            _require(math.isclose(p, (case.gamma-1)*u/volume, rel_tol=1e-10)
                     and math.isclose(t, u/(m*case.gas_r/(case.gamma-1)), rel_tol=1e-10)
                     and math.isclose(y, f/m, rel_tol=1e-10, abs_tol=1e-14), 'Unidades/estado incoherentes.')
        _require(math.isclose(row['time_s'], (row['angle_deg']-case.initial_angle_deg)/(6*case.rpm), abs_tol=1e-12), 'Tiempo/ángulo incoherente.')
        if i:
            _require(row['angle_deg'] == rows[0]['angle_deg']+.5*i, 'Ángulo discontinuo o desordenado.')
    if complete:
        _require(rows[0]['angle_deg'] == 180+360*(cycle['cycle']-1), 'Muestras de otro ciclo.')
        _require(cycle['p_max_Pa'] >= max(r['p_T_Y'][2][0] for r in rows),
                 'Presión máxima inferior a las muestras.')
        _require(rows[-1]['state'] == cycle['state'], 'Estado final no corresponde al resumen.')
        for key in ('W_C_J', 'W_K_J', 'Q_J', 'converted_kg'):
            _require(rows[-1][key] == cycle[key], 'Muestras/resumen no corresponden.')


def load_result(path):
    """Datos declarativos, nombres fijos y hashes; nunca ejecutar contenido."""
    try:
        path = Path(path)
        def read(name):
            file = path.parent/name
            _require(file.stat().st_size <= 16*1024*1024, 'Archivo demasiado grande.')
            raw = file.read_bytes()
            value = json.loads(raw)
            _require(isinstance(value, dict), 'Se esperaba un objeto JSON.')
            _finite(value)
            return raw, value
        _require(path.name == 'manifest.json', 'Elegí manifest.json del resultado.')
        _, manifest = read('manifest.json')
        _require(manifest['format'] == 'motorsim-reference-result' and type(manifest['version']) is int and manifest['version'] == 1
                 and manifest['model_version'] == MODEL_VERSION and manifest['units'] == UNITS,
                 'Formato, modelo o unidades no admitidos.')
        _require(set(manifest['files']) == set(FILES), 'Archivos vinculados incorrectos.')
        payloads = []
        for name in FILES:
            raw, value = read(name)
            _require(hashlib.sha256(raw).hexdigest() == manifest['files'][name]
                     and value['run_id'] == manifest['run_id'], 'Archivos de ejecuciones distintas o alterados.')
            payloads.append(value)
        case, summary, samples = payloads
        _require(json.dumps(case['inputs'], sort_keys=True) == json.dumps(reference_inputs(), sort_keys=True),
                 'Entradas no corresponden al caso fijo admitido.')
        status, result = summary['status'], summary['result']
        _require(status in ('converged', 'cancelled', 'not_converged', 'error'), 'Finalización desconocida.')
        _require(isinstance(result['stop'], str) and bool(result['stop']) and len(result['stop']) <= 4096, 'Motivo ilegible.')
        _number(result['seconds'], 0)
        _number(result['peak_process_MiB'], 0)
        _require(result['profile'] == asdict(PROFILE), 'Perfil incorrecto.')
        cycles = result['cycles']
        _require(isinstance(cycles, list) and len(cycles) <= 30, 'Cantidad de ciclos incorrecta.')
        for i, cycle in enumerate(cycles, 1):
            _cycle(cycle, i)
        _require(type(result['converged']) is bool and result['converged'] == (status == 'converged'), 'Estado contradictorio.')
        if status == 'converged':
            _require(len(cycles) >= 7 and all(c['cycle'] >= 5 and c['convergence']['passed'] for c in cycles[-3:]),
                     'Faltan tres ciclos de convergencia completa.')
        _require(len(samples['cycles']) == min(2, len(cycles)), 'Faltan muestras de los últimos ciclos.')
        for rows, cycle in zip(samples['cycles'], cycles[-2:]):
            _samples(rows, True, cycle)
        _samples(samples['partial'], False)
        return dict(manifest=manifest, inputs=case['inputs'], status=status, result=result,
                    samples=samples, path=path.resolve())
    except (OSError, ValueError, KeyError, TypeError, IndexError, OverflowError, RecursionError) as exc:
        raise ResultError(f'Resultado ilegible: {exc}') from exc
