# Diseño del programa

Este cambio es el registro durable único de `MOTORSIM_2T_COMMERCIAL_CORE`; no
reemplaza ni edita contratos históricos. Los componentes nuevos se separarán en
módulos tipados con esquema/versionado explícito, conservarán su configuración
primaria y provenance, y se conectarán a la integración P5-C/P6 existente cuando
la topología del componente sea compatible. No se duplica el solver 1D.

El harness de referencia continúa independiente de anchors P8 y de E13
histórico. Su contrato congelado actual conserva CFL 0,4, 400 ciclos y los
umbrales ya preregistrados. El bloqueo KT100 actual ocurre en la frontera de
reservorio existente; ninguna fase posterior puede cambiarla de forma implícita
ni reclasificar los recibos r5. Las fases independientes pueden avanzar con
fixtures analíticos y evidencias propias.

Toda métrica nueva documenta ecuación, dominio, unidades, especies/ledgers de
origen y comportamiento ante denominadores cero antes de usarla en campañas.
Todo estado persistente importante prueba round-trip, restart y replay. La
configuración experimental P9 permanece pendiente de datos y se mantiene fuera
de la ejecución automática.

## Fases y dependencias

Las fases se registran en `tasks.md`. Un bloqueo local conserva su evidencia y
permite continuar fases independientes. `Commercial Core Ready` requiere la
integración completa definida por la autorización de la usuaria, incluidos dos
casos de referencia trazables; un módulo aislado no satisface ese gate.

## Geometría de puertos `GENERIC_2T_PORTS_V1`

La primera capacidad se implementa como configuración JSON independiente del
Project v6: los proyectos históricos conservan su esquema y cálculos actuales.
La configuración identifica conductos por `id`/rol y lumbreras por `id`, rol,
función geométrica, coeficiente de descarga y provenance. Una lumbrera bridged
se representa como sus aperturas individuales con un `group_id` común; las
áreas se suman por conducto sin fingir que el puente es otra ventana.

Las ventanas rectangulares usan posición axial desde PMS, positiva hacia PMI,
mm desarrollados y `piston_position` existente. Para transfer/escape,
`Aeff=Cd*w*max(0,min(h,x(theta)-top-roof_travel*position))`. Para piston-port
intake se reutiliza `intake_results`: `d=top+h-skirt`,
`Aeff=Cd*w*max(0,min(h,d-x(theta)))`. El coeficiente es una entrada positiva
finita; no se estima ni calibra. Perfil explícito: knots finitos 0–360°,
estrictamente crecientes, área no negativa, extremos idénticos; evaluación
piecewise-linear, periódica. Los perfiles explícitos se reservan a aperturas de
escape; transfer e intake conservan geometría de ventana/piston-port. Muestreo
derivado a cada grado inclusive sirve para visualización/persistencia, mientras
el evaluador continuo y los eventos exactos
son la fuente para integración futura.

La serialización incluye SHA-256 canónico de geometría/config y de perfiles
derivados; al leer se regeneran y comparan los perfiles. Estos hashes prueban
binding/integridad del artefacto, no son evidencia física. El coeficiente y el
área no se conectan al P5-C histórico en este primer tramo; integración con
topología variable requiere un adaptador nuevo y pruebas de ledgers por ducto.

## Métricas de scavenging `MOTORSIM_2T_SCAVENGING_METRICS_V1`

Se usan masas de especies P6: `F=fresh_air+fuel`, `R=residual`, `M=sum(especies)`.
Fresh delivered y fresh short-circuit proceden de los ledgers P6 por dirección.
`Fret` es la especie fresca presente en el cilindro al cierre de la última
apertura de escape; `Mref=rho_amb*pi*bore²*stroke/4`. Delivery ratio=`Fdel/Mref`;
trapping efficiency=`Fret/Fdel`; scavenging efficiency=`Fret/Mexhaust_close`;
charging efficiency=`Fret/Mref`; trapping ratio=`Fdel/Fret`; residual fraction
`=Rexhaust_close/Mexhaust_close`; purities at transfer/exhaust close are the
respective fresh mass fractions; short-circuit fraction=`Flost/Fdel`. Zero
denominators return `UNDEFINED/ZERO_DENOMINATOR`; no clipping to [0,1] and no
substitution of zero. A model output outside a familiar efficiency range remains
visible to expose ledger/state mismatch. `Fret` and `Flost` remain separately
reported masses.

The trajectory adapter accepts resolved scheduler-angle identities from the
geometry layer, requires exactly one snapshot at each closure, binds the last
snapshot to the terminal gas/species state, and recomputes fresh delivery/loss
from cumulative P6 ledgers. It rejects a missing event, nonmonotone trajectory,
terminal mismatch, bool-as-number, or stale cycle summary; it never interpolates
across a closure event.

## Reed `STATIC_REED_V1` / `DYNAMIC_REED_V1`

Each synthetic/configured petal supplies `m`, pressure area `Ap`, effective
flow width `w`, spring `k`, damping `c`, lift limit `h`, flow coefficient `Cd`,
restitution `e`, and provenance. Positive `dp = p_upstream - p_downstream`
opens the valve. Static lift is `clamp(dp*Ap/k,0,h)`; static reverse flow is
blocked. Dynamic state follows `m*x''+c*x'+k*x=dp*Ap` at constant dp during a
solver step. Use the closed-form damped linear-oscillator solution between
contacts; detect contact times from monotone intervals separated by exact
velocity extrema and bounded bisection, apply configured restitution, then
advance the remaining step. At a stop where acceleration points outward, hold
the petal there until the force releases it. `Aeff=Cd*w*x`; bank area is the
sum of petal areas. Existing `simulation.restriction` computes mass/energy/fresh
flux. Static mode gates reverse flow; dynamic mode allows transient reverse
flow while open and records no ledger itself. All coefficients are user/model
inputs with provenance; no value is fitted. The standalone state model does not
modify P5/P6 and requires a later stage-coherent integration phase.

## Expansion chamber geometry and trace adapter

`ExpansionChamber` is a typed, provenance-bearing assembly of continuous
conical sections (header, diffuser, belly, baffle cone, stinger, silencer,
tailpipe or generic cone). It uses the accepted `gas1d.mesh.segments_mesh`
builder for exact frustum volumes and shared face areas. It does not implement
a second gas solver. `map_solver_state` consumes the existing quasi-1D
primitive trajectory to expose pressure, temperature, Mach, mass flow and
left/right characteristic speeds. Optional wave decomposition is explicitly
linear, isentropic and relative to a supplied base state. Reflection timing is
an estimate obtained by integrating characteristic speeds to a named section
station; reflected amplitudes remain the solver's responsibility. Neither
trace adapter nor geometry changes P4/P5/P6 contracts or the product project
schema.

## Thermal prescribed-wall transfer `MOTORSIM_THERMAL_V1`

Each configured surface has explicit area, provenance, `CONSTANT_H_V1`
coefficient, and exactly one wall-temperature source: a fixed kelvin value or a
bounded RPM/load map with bilinear interpolation. The model evaluates
`Qdot_gas_to_wall = h*A*(Tgas-Twall)`. A cycle ledger integrates the supplied
ordered crank-angle samples by trapezoids using `dt=dCA/(6*RPM)`, reports each
surface and total signed energy, and requires a complete specified cycle. Map
extrapolation is rejected. This is prescribed-wall transfer, not a wall-capacity
model or a fitted heat-transfer correlation; upstream integration must supply
gas temperatures from the same physical solver stages and close the energy
ledger globally.
