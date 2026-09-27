# P8 wide-RPM indicated performance

## ADDED Requirements

### Requirement: bounded RPM contract
La implementación MUST aceptar sólo RPM enteros en [2500, 15000], usar
`omega_deg_s = 6*rpm` y completar una ventana de 360 grados equivalente a
`60/rpm` segundos, con CFL y cortes de eventos exactos.

#### Scenario: domain and timing
Given 2500, 5000, 8000, 11000 and 15000 rpm, each run uses the exact angular
rate and cycle duration; values outside the range or non-integers are rejected.

### Requirement: authoritative full topology
La campaña MUST reutilizar la mecánica/configuración 2T aprobada y la topología
atmósfera-intake-crankcase-transfer-cylinder-exhaust-atmósfera con P6/P7.
No MUST inventar geometría, timing, leyes ni soporte recurrente.

#### Scenario: provenance
Given an existing approved reference configuration, the evidence records its
exact provenance and all five anchors use it; otherwise closure is blocked by
`P8_SCIENTIFIC_CONTRACT_REQUIRED`.

### Requirement: indicated metrics and sign
La implementación MUST calcular trabajo de cilindro `integral(p dV)`, potencia,
par y pmax sobre la misma ventana, y probar previamente el signo con una cámara
cerrada. Debe registrar calor prescrito, residuales de masa/energía/especies,
masa fresca entregada y short-circuit definidos por P6/P7.

#### Scenario: work formulas
Given known work and rpm, power equals `W*rpm/60` and torque equals `W/(2*pi)`;
expansion is positive and compression negative under the verified convention.

### Requirement: admissibility and determinism gates
Cada anclaje final MUST completar sin NaN/Inf ni estados inadmisibles, conservar
las tolerancias existentes, registrar CFL mínimo/máximo y pasos, y pasar replay
determinista, restart dentro de un ciclo, suma de especies P6 y admisibilidad de
fuente P7. No se permite clipping silencioso ni retirar un anclaje fallido.

#### Scenario: five-point evidence
Given all five anchors, the JSON records per-RPM metrics and gates plus exact
window, initialization, contract version, regression counts and limitations.

### Requirement: conditional evidence
La evidencia MUST declarar `steady_state=false`,
`periodic_convergence=NOT_GRANTED_BY_P4`, `metric_semantics=BOUNDED_TRANSIENT_INDICATED`,
`conditional_on_p4=true`, `experimental_validation=NOT_PERFORMED` e
`independent_review=INDEPENDENT_REVIEW_PENDING`. No afirma validación ni P9.

#### Scenario: conditional closure
Given passing bounded gates, closure is `P8_WIDE_RPM_PERFORMANCE_VERIFIED_CONDITIONAL`
and `P8_READY_FOR_P9_DATA`, while P4 remains blocked and P9 remains stopped.

