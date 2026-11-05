"""Presentation only: raw scientific codes remain in artifacts and tooltips."""
import math
import re
from PySide6.QtWidgets import QStyledItemDelegate

STATES = {
    'MAX_CYCLES_NONCONVERGED':'Límite de ciclos · no convergida',
    'INSUFFICIENT_CYCLES':'Ciclos insuficientes', 'NOT_CONVERGED':'No convergida',
    'EXPLORATORY_COMPLETE_PERIODICITY_NOT_IDENTIFIED':'Terminada · sin periodicidad identificada',
    'EXPLORATORY_PARALLEL_POINT_SWEEP':'A/B terminado · revisar resultados',
    'EXPLORATORY_CURVE_PARTIAL':'Curva exploratoria · periodicidad no confirmada',
    'EXPLORATORY_CURVE_COMPLETE':'Curva exploratoria terminada',
    'CANCELLED_CHECKPOINTED':'Cancelada · checkpoint disponible',
    'INTERRUPTED_CHECKPOINTED':'Interrumpida · checkpoint disponible',
    'NUMERICAL_INVALID':'Inválido numéricamente', 'PERIOD_1':'Periódica observada · orden 1',
    'PERIOD_2':'Periódica observada · orden 2', 'NOT_REPORTED':'No informado',
    'NOT_PERFORMED_NO_REPLAY':'No realizada · sin replay', 'NOT_PERFORMED':'No realizada',
    'NOT_CLAIMED':'No declarada', 'NOT_EVALUATED':'No evaluada',
    'NOT_IDENTIFIABLE':'No identificable', 'UNDEFINED':'No definido',
    'NO_PERIODICITY_TRANSIENT_ONLY':'Sin periodicidad · sólo transitorio',
    'DEFINED':'Definido', 'EXPLORATORY':'Exploratoria · no validada',
    'COMPLETE':'Terminada', 'RUNNING':'En ejecución', 'PASS':'Correcto',
    'CANCELLED':'Cancelado',
    'FAIL':'Falló', 'REPORTED':'Reportado', 'SYNTHETIC':'Sintético',
    'SYNTHETIC_ASSUMPTION':'Supuesto sintético', 'UNKNOWN':'Desconocido',
    'TIME_LIMIT_NONCONVERGED':'Tiempo agotado · no convergida',
    'STOPPED_ERROR':'Detenida por error', 'FAIL_CLOSED':'Fallo · ejecución detenida',
    'FAILED_CLOSED':'Fallo · ejecución detenida', 'NOT_STARTED':'No iniciada',
    'NO_CONVERGENCE_WITHIN_HORIZON':'Sin convergencia en el horizonte',
    'EXPLORATORY_TIMEOUT_CHECKPOINTED':'Tiempo agotado · checkpoint disponible',
    'EXPLORATORY_SWEEP_POINT_BUDGET_EXHAUSTED':'Presupuesto del punto agotado',
    'MANIFEST_MISSING':'Falta el manifiesto', 'MANIFEST_UNREADABLE':'Manifiesto ilegible',
    'MANIFEST_INVALID':'Manifiesto inválido', 'INCOMPLETE_METADATA':'Metadatos incompletos',
    'STATUS_NOT_REPORTED':'Estado no informado', 'ENGINEERING_ONLY_NOT_VALIDATED':'Ingeniería · no validada',
    'NO_PERIODICITY_TRANSIENT_ONLY':'Sin periodicidad · sólo transitorio',
    'TRANSIENT_ESTIMATE':'Estimación transitoria', 'INCOMPATIBLE':'Incompatible',
    'NOT_EVALUATED_EXPLORATORY':'No evaluada · modo exploratorio',
    'NO_COMPLETE_CYCLE':'No se completó un ciclo',
    'INTERNAL_CONSERVATION_NO_REPLAY':'Conservación interna · sin replay independiente',
    'MIXED_SCHEMAS':'Formatos de resultado mixtos',
    'UNKNOWN_CONFIGURATION':'Configuración desconocida',
    'COMPARABLE':'Condiciones comparables', 'EXPLORATORIO':'Exploratorio',
    'NO_PERIODICITY':'Sin periodicidad', 'RECOMPUTED':'Recalculada',
    'NOT_QUANTIFIED':'No cuantificada', 'NO_REPLAY':'Sin replay',
    'EXPLORATORY':'Exploratorio', 'NOT_CLAIMED':'No declarada',
    'NOT_PERFORMED':'No realizada', 'NOT_REPORTED':'No informada',
    'UNDEFINED':'No definida', 'DEFINED':'Definida', 'PERIOD_1':'Periódica · ciclo 1',
    'PERIOD_2':'Periódica · ciclo 2', 'NOT_CONVERGED':'No convergida',
    'INSUFFICIENT_CYCLES':'Ciclos insuficientes', 'NOT_EVALUATED':'No evaluada',
    'INTERNAL_CONSERVATION_NO_REPLAY':'Conservación interna · sin auditoría independiente',
    'ENGINEERING_EXPLORATORY':'Exploratoria de ingeniería', 'HISTORICAL_IMPL2':'Histórico sintético',
    'IMPORTED_EXTERNAL':'Importado', 'EXPLORATORY_CURVE_PARTIAL':'Curva exploratoria parcial',
    'NOT_VALIDATED':'No validada', 'NOT_APPLICABLE':'No aplica',
    'HISTORICAL_LEGACY_SUMMARY':'Resumen histórico heredado',
}

_INTERNAL_CODE=re.compile(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b")
_SNAKE_KEY=re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
FIELD_LABELS={
    'classification':'Clasificación','hard_failures':'Fallos críticos',
    'schema':'Formato de datos','warning_policy':'Política de advertencias',
    'warnings':'Advertencias','status':'Estado','periodicity':'Periodicidad',
    'conservation':'Conservación','relative':'Relativo','absolute':'Absoluto',
    'producer_sha256':'Hash SHA-256 del productor','solver_sha256':'Hash SHA-256 del solver',
    'configuration_sha256':'Hash SHA-256 de configuración','experimental_validation':'Validación experimental',
    'audit_status':'Estado de auditoría','cycles_completed':'Ciclos completados',
    'audit':'Auditoría','cycle':'Ciclo','point':'Punto','result':'Resultado',
}
_KEY_WORDS={
    'hard':'críticos','failures':'fallos','failure':'fallo','warning':'advertencia',
    'warnings':'advertencias','policy':'política','schema':'formato','classification':'clasificación',
    'status':'estado','relative':'relativo','absolute':'absoluto','cycle':'ciclo','cycles':'ciclos',
    'completed':'completados','producer':'productor','solver':'solver','configuration':'configuración',
    'experimental':'experimental','validation':'validación','audit':'auditoría','periodicity':'periodicidad',
    'conservation':'conservación','hash':'hash','sha256':'SHA-256','point':'punto','result':'resultado',
    'error':'error','errors':'errores','gate':'puerta','gates':'puertas','limit':'límite','budget':'presupuesto',
    'rpm':'RPM','engine':'motor','measurement':'medición','identity':'identidad','reason':'motivo',
}
_TEXT_LABELS={
    'warnings require explanation and do not override physical validity':
        'Las advertencias requieren explicación y no prevalecen sobre la validez física',
}


def format_number(value, significant=6, *, signed=False):
    """Compact, consistent UI formatting; never use this for persisted/exported data."""
    if isinstance(value,bool):return str(value)
    try:number=float(value)
    except (TypeError,ValueError,OverflowError):return str(value)
    if not math.isfinite(number):return str(value)
    if isinstance(value,int) or number.is_integer():
        integer=int(number)
        if abs(integer)<10**significant:
            return f"{integer:+d}" if signed else str(integer)
    spec=f"{ '+' if signed else ''}.{int(significant)}g"
    return format(number,spec)


def display_value(value, significant=6):
    if value is None:return "—"
    if isinstance(value,(int,float)) and not isinstance(value,bool):return format_number(value,significant)
    if isinstance(value,(dict,list,tuple)):
        def render(item):
            if item is None:return None
            if isinstance(item,(int,float)) and not isinstance(item,bool):return format_number(item,significant)
            if isinstance(item,dict):return {field_label(key):render(child) for key,child in item.items()}
            if isinstance(item,(list,tuple)):return [render(child) for child in item]
            if isinstance(item,str):return state_label(item)
            return item
        import json
        return json.dumps(render(value),ensure_ascii=False,sort_keys=True,separators=(", ",": "))
    return state_label(value)

def state_label(value):
    if value is None:return 'No informado'
    text=str(value)
    for code in sorted(STATES,key=len,reverse=True):text=text.replace(code,STATES[code])
    for phrase,label in _TEXT_LABELS.items():text=text.replace(phrase,label)
    # Artifacts keep unknown enum values exactly. On ordinary UI surfaces show
    # a neutral localized label instead of leaking an untranslated token.
    text=_INTERNAL_CODE.sub('Estado técnico no clasificado',text)
    if _SNAKE_KEY.fullmatch(text):return field_label(text)
    return text


def field_label(value):
    """Localize technical metadata keys while retaining originals in tooltips."""
    text=str(value)
    prefix,separator,suffix=text.rpartition(' · ')
    if separator and (_SNAKE_KEY.fullmatch(suffix) or suffix in FIELD_LABELS):
        return f"{prefix} · {field_label(suffix)}"
    if text in FIELD_LABELS:return FIELD_LABELS[text]
    if _SNAKE_KEY.fullmatch(text):
        words=[_KEY_WORDS.get(part) for part in text.split('_')]
        if all(words):return ' '.join(words).capitalize()
        return 'Dato técnico sin traducción'
    return state_label(text)

class EngineeringNumberDelegate(QStyledItemDelegate):
    """Round paint text only; EditRole/source precision stays untouched."""
    def displayText(self,value,locale):
        return format_number(value)

class PortRoleDelegate(QStyledItemDelegate):
    def displayText(self,value,locale):
        return {'transfer':'Transfer.','intake':'Admisión','exhaust':'Escape'}.get(str(value),str(value))
