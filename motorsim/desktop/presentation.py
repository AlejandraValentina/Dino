"""Presentation only: raw scientific codes remain in artifacts and tooltips."""
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
    'FAIL':'Falló', 'REPORTED':'Reportado', 'SYNTHETIC':'Sintético',
}

def state_label(value):
    if value is None:return 'No informado'
    text=str(value)
    for code in sorted(STATES,key=len,reverse=True):text=text.replace(code,STATES[code])
    return text

class EngineeringNumberDelegate(QStyledItemDelegate):
    """Round paint text only; EditRole/source precision stays untouched."""
    def displayText(self,value,locale):
        try:return f'{float(value):.5g}'
        except (TypeError,ValueError):return str(value)

class PortRoleDelegate(QStyledItemDelegate):
    def displayText(self,value,locale):
        return {'transfer':'Transfer.','intake':'Admisión','exhaust':'Escape'}.get(str(value),str(value))
