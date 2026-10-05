# MotorSim — Modo autónomo de ingeniería (`MOTORSIM_AUTONOMOUS_ENGINEERING_TEAM`)

Reglas detalladas de la ORDEN VIGENTE de `AGENTS.md`. Ante conflicto, prevalece
`AGENTS.md`; el estado científico vigente se lee allí y en
`results/2t-commercial-core-20261002/program-status.json`.

## 1. Objetivos

1. `GENERAL_PURPOSE_2T_SIMULATION_CORE_VERIFIED` (sección 9).
2. Después: `MOTORSIM_2T_COMMERCIAL_CORE_READY` (sección 10).

El problema principal no es la falta de features aisladas sino la integración
end-to-end: convertir las capabilities probadas en un único camino
físico/numérico consistente.

## 2. Flujo de trabajo

`problema → orchestrator → investigación → síntesis → implementación →
verificación → revisión adversarial → regresión → integración → siguiente tarea`

Roles (subagentes si existen; si no, pasadas secuenciales declaradas como
autorrevisión):

- **Orchestrator / tech lead**: roadmap, dependencias, cola, integración, merge.
- **Numerical / physics**: Euler cuasi-1D, Riemann, CFL, características,
  fronteras, conservación, SSPRK2, termodinámica.
- **Engine architecture**: interfaces de componentes, estado integrado, grafo
  de etapas, puertos, ductos, válvulas, cárter, cilindro, admisión/escape; sin
  duplicación.
- **Implementation**: workstreams independientes en paralelo; un solo escritor
  por zona del núcleo a la vez.
- **Verification**: unitarios, fixtures analíticos, integración, negativos,
  conservación, restart/replay, evidencia malformada, regresiones.
- **Adversarial reviewer**: intentar romper cada capability. Buscar: expected
  circular, estado stale, etapa SSPRK equivocada, términos de ledger faltantes,
  bool-como-número, NaN/inf, unidades, orientación, especie donante, summary
  como autoridad, fallback oculto, factores de ciclo 2T, estado faltante en
  restart, desajuste trayectoria/terminal.
- **Contract / regression guardian**: P4–P9, evidencia histórica, runtime
  bindings, umbrales preregistrados. Ninguna capability reinterpreta un
  contrato histórico.
- **Evidence / documentation**: OpenSpec, provenance, receipts, program status.

## 3. Arranque de cada sesión

1. `git status`, `git rev-parse HEAD`, `git rev-parse origin/main`,
   `git log --oneline --decorate -40`, `git diff --check`. Usar el HEAD real.
2. Leer el campo `queue` de
   `results/2t-commercial-core-20261002/program-status.json` y la sección 15
   de este documento.
3. Verificar que el SHA-256 de
   `openspec/changes/p9-experimental-validation/specs/p9-experimental-validation/spec.md`
   siga siendo
   `79fbe9b88d26fc4af5083d65d468f59c9208535f0ab389d2f3cb9a7654b88a4d`.
4. Inspeccionar archivos untracked. `motorsim/integrated_2t.py` y
   `tests/test_integrated_2t.py` son trabajo en curso: revisarlos y retomarlos
   o documentar por qué no; no borrarlos. Los directorios
   `results/kt100-hybrid-model-fixture-v2-harness-20261002*` se preservan sin
   stage.

## 4. Cola y presupuesto

- La cola vive en `program-status.json` → `queue`. Cada item tiene: `id`,
  `description`, `dependencies`, `state` (`READY`, `IN_PROGRESS`,
  `BLOCKED_LOCAL`, `REVIEW`, `DONE`), `blocker`, `commits`, `evidence`,
  `next_action`. Se actualiza en cada commit significativo.
- Al quedar una tarea `BLOCKED_LOCAL`, tomar otra `READY`. Reevaluar bloqueos
  cuando una nueva capability pueda resolverlos.
- Presupuesto (estimar antes con corrida corta/profiling): diagnóstico
  ≤10 min; fixture/integración ≤30 min por configuración; campaña científica
  larga ≤60 min continuos, hasta 120 min sólo si es gate-critical, con
  checkpoint/restart usable, progreso persistido y sin alternativa más barata.
  Proyección mayor: `PERFORMANCE_BLOCKED_LOCAL`; perfilar y optimizar sólo con
  transformaciones que preserven la semántica, verificando equivalencia. No
  reducir precisión, CFL ni umbrales para cumplir el presupuesto.
- Preregistración: diseñar, documentar, tests estructurales y commit de
  preregistración; recién después la campaña decisoria, en otro commit.
- Si la sesión se interrumpe, `AGENTS.md`, este documento y
  `program-status.json` commiteados deben bastar para continuar.

## 5. Prioridad de workstreams (el orchestrator reordena por dependencias)

- **A — Fundación de integración**: grafo SSPRK2 común; estado integrado único;
  ledgers globales; esquema de evidencia primaria; checkpoint/restart/replay.
- **B — Intercambio de gases**: admisión/reed/cárter; arquitectura de N
  transfers; escape + cámara de expansión; frontera externa generalizada.
- **C — Termoquímica**: cuatro especies; combustible/AFR; combustión V2;
  térmico; cárter V2.
- **D — Performance**: métricas de barrido; trabajo indicado/IMEP; pérdidas
  mecánicas/FMEP; BMEP/potencia al freno; caudal de combustible; ISFC/BSFC.
- **E — Componentes de producto**: puertos genéricos; reed V1 completo;
  powervalve; plenum/airbox/boost bottle; collector de outputs; importador
  experimental.
- **F — Generalidad**: Fixture A; Fixture B; regresiones P4–P8 completas;
  KT100 solo tras resolver la capability bloqueante; segundo caso documentado.

Diferido hasta cerrar el núcleo (solo interfaces): rotary valve,
multicilindro, turbo, supercharger, opposed piston, uniflow, vehículo, GUI.

## 6. Requisitos técnicos

### Grafo SSPRK2 común
Un único grafo de actualización. Por etapa: geometría, áreas de puertos,
reconstrucción, estados de frontera, flujos Riemann, admisión, cárter,
transfers, cilindro, escape, especies, fuente de combustión, fuente térmica,
ledgers, estado aceptado. Investigar lecturas stale, actualizaciones
duplicadas, orden y splitting inconsistente. Sin integraciones ad hoc fuera del
grafo.

### Estado integrado único
Serializable y suficiente para continuar exactamente:
- Físico: cilindro, cárter, ductos de admisión/transfer/escape, válvulas, reed,
  powervalve, reservoir/plenum, estado conservativo, especies, combustión,
  térmico.
- Acumuladores: masa, energía, especies, entrega fresca, cortocircuito,
  combustible entregado, quemado/no quemado, calor liberado, calor a pared,
  trabajo, pérdidas mecánicas.
- Numérico: tiempo, ángulo, ciclo, etapa SSPRK, dt, CFL, estado del detector de
  periodicidad.

### Ledgers globales
Independientes de los summaries locales; recalculables por ciclo:
- Masa: inicial + entrada externa − salida externa + fuentes contractuales = final.
- Energía: inicial + flujos de entalpía + combustión − calor a pared − trabajo
  + términos contractuales = final.
- Especies: `fresh_air`, `fuel`, `residual`, `burned`.

«Cada componente conserva» no prueba que conserve el motor completo.

### Evidencia primaria
Reconstruible offline: trayectoria → etapa/estado aceptado → terminal de ciclo
→ conservación → periodicidad → trabajo → checkpoint → restart → replay →
digest → summary. Prohibido: PASS almacenado como autoridad, prueba summary
contra summary, residuo sin ledger primario, digest sin preimagen, terminal sin
binding a la trayectoria.

### Reed / cárter
Flujo completo admisión → reed → cárter con dinámica o comportamiento estático,
área, fuerza de presión, especie donante, flujo directo y reverso, ledgers de
masa, energía y especies. No aceptar el reed solo por tests aislados.

### N transfers
Capability nueva para N rutas (al menos primary, secondary y boost) con
geometría, timing, área, Cd, ducto, donante, especies y conservación propios.
No limitar el núcleo a los dos transfers históricos de P5-C.

### Escape
Puerto, header, diffuser, belly, baffle, stinger y frontera externa
participando del motor completo; powervalve y transferencia de calor cuando
corresponda.

### Combustible / P6
Cadena cerrada: entregado → especie fuel → atrapado → combustión → quemado →
contabilidad de no quemado. AFR, phi y caudal se derivan de esa misma
evidencia; no un modelo de combustible separado de P6.

### Combustión
P7 histórico intacto. Capability nueva reutilizable: Wiebe simple/doble,
timing, duración, CA10/50/90, eficiencia, mapas RPM/carga. Un modelo
parametrizado no es predictivo.

### Térmico
Culata, pared de cilindro, pistón, cárter, paredes de transfer y escape. Todo
calor aparece en el ledger de energía, sin doble conteo.

### Performance mecánica
Presión → p-dV → trabajo indicado → IMEP → par/potencia indicados → pérdidas →
FMEP → BMEP → par/potencia al freno; con combustible, ISFC/BSFC. Tests
obligatorios de los factores de ciclo 2T.

### Collector de outputs único
- Por ángulo: presiones de cilindro/cárter/ductos, temperatura, especies,
  liberación de calor, calor a pared, áreas de puertos, caudal másico, Mach.
- Por ciclo/RPM: trabajo, potencia, par, IMEP/FMEP/BMEP, delivery ratio,
  trapping, scavenging y charging efficiency, entrega fresca, cortocircuito,
  AFR, caudal de combustible, ISFC/BSFC, presión pico y ángulo del pico.
- Termo: P-V, lazo de bombeo, balance de energía.

## 7. Reservoir boundary (bloqueo actual)

Aplicar el protocolo de la sección 8 a `No consistent reservoir inflow branch`
(ver `docs/gasdynamic/generalized_reservoir_boundary_v2_debt.md`). No aceptar
de nuevo la excepción como conclusión. Investigar: estructura característica,
ecuaciones de rama, interpretación del reservoir, magnitudes totales/estáticas,
orientación, entrada y salida subsónicas, inversión, estado casi sónico,
reconstrucción primitiva, etapa SSPRK, área efectiva, especie donante, energía
y admisibilidad.

Resoluciones permitidas:
- **A — Bug**: corregir si es inequívoco y proteger los resultados históricos.
- **B — Limitación de capability**: si V1 es válida pero limitada y existe una
  extensión física estándar clara, crear `RESERVOIR_BOUNDARY_V2` como
  capability nueva, sin tocar V1. La semántica se preregistra y commitea antes
  de cualquier campaña.
- **C — Ambigüedad científica**: solo si hay varias formulaciones plausibles
  con consecuencias materiales y sin criterio de elección:
  `RESERVOIR_BOUNDARY_V2_SCIENTIFIC_DECISION_REQUIRED`. Escalar y continuar
  los workstreams independientes.

Forensics ejecutado el 2026-10-05: V1 usa el invariante saliente de Euler y
resuelve la entrada sub-sónica isentrópica desde el reservoir en reposo. Para
la rama evaluada, `f(w)=w+2a(w)/(gamma-1)` es creciente en
`[-a_sonic,0]`, con extremos `J_choke` y `J_rest`; por eso `J+ > J_rest` no
posee raíz en el dominio contractual. El fixture de 100 kPa, 301 K y
`u=-0.001 m/s` no prueba un bug del solver. Las formulaciones alternativas
(Riemann con estado exterior prescrito o característica con una política de
choking/transición explícita) pueden cambiar caudal, energía y reflexión; V2
queda clasificada como ambigüedad material a la espera de que se agoten las
tareas independientes. KT100 y los recibos originales siguen congelados.

Como trabajo independiente prioritario, la integración ahora admite un único
plenum finito en la entrada del ducto de admisión: el mismo helper P3 se evalúa
en ambas etapas, los incrementos internos son opuestos, las especies usan el
donante real, el nodo participa del inventario/CFL/restart y la salida V2 puede
trazar presión, temperatura, masa y composición. Esto no habilita una nueva
frontera atmosférica ni resuelve la selección de V2.

Alcance acústico del enlace: el volumen intercambia mediante la interfaz P3
ideal y sin masa; `NetworkConnection.effective_length_m` permanece como dato de
geometría/provenance y no se aplica como inertancia ni propagación acústica en
este camino. La documentación primaria de NASA describe tanto fronteras por
estado de Riemann como fronteras subsónicas basadas en estado de estancamiento
([Cart3D](https://www.nas.nasa.gov/publications/software/docs/cart3d/pages/howto/samples_power/README.html),
[Wind-US](https://www.grc.nasa.gov/www/winddocs/user/bc.html)); los tratamientos
de caudal estrangulado dependen además del estado total y del régimen
([NASA mass-flow choking](https://www.grc.nasa.gov/www/k-12/BGP/mflchk.html)).
Estas referencias documentan alternativas existentes, pero no seleccionan la
semántica de una futura frontera MotorSim ni cambian el bloqueo científico V2.

La integración se generalizó luego a volúmenes finitos en endpoints externos
distintos: intake-left y exhaust-right. El grafo reusa P3 en ambas etapas, y el
estado V7 incorpora ambos volúmenes en configuración, CFL, conservación,
checkpoint/replay, primary cycle y output V2. Una revisión adversarial puntual
no encontró defectos de orientación, balance, restart ni muestras de salida.
V7 no conserva compatibilidad de restore con V6, y no admite conexiones
volumen-a-volumen ni más de un volumen en la misma cara.

## 8. Protocolo ante bloqueos no triviales

No devolver el bloqueo automáticamente al humano. Investigaciones paralelas:
- **Forensics**: reproducir y extraer el estado exacto del fallo.
- **Domain expert**: reconstruir ecuaciones y algoritmo.
- **Skeptic**: buscar un bug ordinario antes de aceptar física nueva.
- **Contract guardian**: impacto sobre contratos cerrados.

Luego: hipótesis → evidencia → contradicciones → experimentos → síntesis.

Para conocimiento externo, priorizar textbooks, papers, métodos numéricos
documentados y literatura de solvers; registrar rationale y referencias. Si no
hay acceso a red, usar la documentación del repo y la teoría estándar, y
registrar `EXTERNAL_RESEARCH_UNAVAILABLE` indicando qué conclusión se obtuvo
sin verificación externa. No inventar citas. No introducir una formulación porque
«parece funcionar».

## 9. `GENERAL_PURPOSE_2T_SIMULATION_CORE_VERIFIED`

Al menos dos fixtures distintos end-to-end con: estado integrado, SSPRK2,
admisión, cárter, N transfers, cilindro, escape/cámara, frontera, cuatro
especies, barrido, combustible, combustión, térmico, ledgers globales,
convergencia periódica (P1/P2/no convergencia clasificados correctamente),
CFL, admisibilidad, performance indicada y al freno, checkpoint, restart,
replay, evidencia primaria, auditoría offline y outputs de ingeniería.

- **Fixture A**: motor sintético con reed, cárter, ≥3 transfers, cámara de
  expansión, cuatro especies, combustible, combustión, térmico y pérdidas
  mecánicas; múltiples ciclos completos.
- **Fixture B**: significativamente distinto (por ejemplo admisión por puerto
  de pistón, otro layout de transfers, otro escape). Sin hardcodes del núcleo
  para A.

## 10. `MOTORSIM_2T_COMMERCIAL_CORE_READY`

Además de la sección 9: config/schema reutilizable, sin hardcodes de fixture,
puertos genéricos integrados, componentes de admisión/escape reutilizables,
outputs estables, protección de regresiones, documentación/provenance y al
menos dos fixtures integrados independientes. No requiere P9 experimental,
GUI, multicilindro ni turbo.

## 11. KT100 y referencias reales

- KT100 no es el fixture principal de desarrollo. Preservar
  `KT100_REFERENCE_CASE_V1` y su provenance (DOCUMENTED,
  DERIVED_FROM_DOCUMENTED, SYNTHETIC_ASSUMPTION, UNKNOWN). Una sola campaña
  nueva, solo con el motor integrado funcionando y la capability de frontera
  resuelta. Sin ajustar parámetros; su éxito no es necesario para la sección 9.
- Honda CR250R u otro motor permanece `DOCUMENTAL_REFERENCE` hasta tener
  información suficiente. No inventar parámetros reales.

## 12. Regresiones y revisión

- Tras cambios productivos sustanciales, correr las regresiones apropiadas.
  Antes de un cierre global, reejecutar la suite amplia P4–P8; no depender de
  resultados históricos.
- Si una modificación cambia un runtime binding científico histórico,
  identificar el impacto de inmediato. No reinterpretar evidencia antigua.
- Revisión adversarial tras cada workstream grande; independiente (read-only)
  cuando exista. El implementador no autorratifica cambios científicos
  significativos.

## 13. Escalamiento al humano

Solo si se cumple todo: ≥2 alternativas científicas legítimas; cambian
materialmente física o resultados; contratos, teoría, evidencia y tests no
resuelven; elegir constituye una nueva política científica. La consulta incluye
opción A, opción B, consecuencias, evidencia y recomendación técnica. Mientras
se espera, continuar todo lo independiente.

No escalar: APIs, nombres, refactors, schemas, organización de tests,
serialización, performance, bugs, diagnósticos numéricos, Git, documentación,
fallos de implementación recuperables.

## 14. Reporte

Sin reportes por feature ni por subagente. Entregar solo cuando: (A) se
alcance la sección 10, o la sección 9 con el resto acotado; (B) exista una
decisión científica humana genuina; o (C) se agoten las tareas independientes
con un hard stop global real.

El informe final incluye: HEAD inicial y final; arquitectura; workstreams;
decisiones científicas; bloqueos resueltos y pendientes; SSPRK2 común; estado
integrado; ledgers; reservoir boundary; admisión/reed; cárter; transfers;
escape/cámara; especies; barrido; combustible; combustión; térmico; pérdidas
mecánicas; performance indicada/al freno; convergencia periódica; checkpoint;
restart; replay; evidencia/auditor; outputs; Fixture A; Fixture B; KT100;
segunda referencia; regresiones P4–P8; estado y hash P9; OpenSpec; Git LFS;
tests; commits; brechas frente a un simulador 2T comercial; clasificación
final de readiness.

Checks de cierre global: suite amplia P4–P8 reejecutada, OpenSpec strict,
`git diff --check`, `git lfs fsck` y hash P9.

---

# Estado vivo

Las secciones siguientes las mantiene el equipo autónomo. Las secciones 1–14
son reglas: no reescribirlas para facilitar trabajo; un cambio de regla se
registra como decisión en la sección 17.

## 15. Objetivo actual

`AUDIT_REMEDIATION_MODE`: incorporar y reconciliar
`docs/gasdynamic/audit_8cdf66e.md` con HEAD `3d10f79`, preservando el trabajo
posterior a `8cdf66e`. Cerrar las prioridades 1 `AUD-01`…`AUD-07` antes de toda
capability nueva. El primer trabajo activo es la fuerza de pared de puertos
cerrados/parciales; `AUD-11` aplica en paralelo el protocolo forense reservoir.
La fábrica `MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V1` y su ajuste de callback
siguen incorporados; solo cubren slider-crank y puertos explícitos. KT100 sigue
congelado.

## 16. Arquitectura vigente

`IntegratedEngine2T` avanza cámara, ductos, especies, reed estática, fuentes
térmicas/P7 y volúmenes finitos opcionales en los endpoints intake-left y
exhaust-right en las mismas dos etapas SSPRK2. Los intercambios de red usan el
helper Riemann P3 existente y la composición real del donante; inventario
global, CFL, checkpoint y output reconstruible incluyen cada nodo. Los
enlaces son ideales y sin masa: su longitud efectiva se serializa, pero no
representa inertancia ni propagación acústica. El checkpoint actual es V7;
V6 no es compatible para restore. `MOTORSIM_INTEGRATED_ENGINE_2T_CONFIG_V1`
reconstruye el subconjunto cuyo estado geométrico completo deriva de
`SliderCrankChambers2T` y `IntegratedPortBinding2T`. En ese caso el callback de
geometría del constructor no se consulta; configuraciones con geometría
arbitraria definida únicamente por callbacks siguen fuera del contrato. La
identidad canónica se comprueba antes de exportar/restaurar y la deriva viva se
rechaza.

## 17. Decisiones científicas

| Fecha | Decisión | Alternativas | Evidencia | Revisión |
|---|---|---|---|---|
| 2026-10-05 | El enlace integrado finito de admisión reutiliza P3 ideal; no se añade una frontera atmosférica ni una nueva política de reservoir | Integrar solo el endpoint existente; tratar longitud efectiva como acústica sería una capability distinta | 99 pruebas focales integradas/P5-C/P6/P7/red/reed/puertos PASS; estado primario/output de un ciclo y conservation rebuild verificados | Revisión adversarial de solo lectura sin defecto en el delta; no es revisión completa del motor |
| 2026-10-05 | Generalizar volúmenes integrados a caras externas intake-left y exhaust-right conserva el helper P3 y el ledger existente; no añade aristas internas de red | Mantener un solo nodo de admisión; o modelar redes internas/acústica como otra capability | 100 pruebas integradas/P5-C/P6/P7/red/reed/puertos PASS; replay V7 de dos nodos, ciclo completo, outputs muestreados contra el estado y ledgers globales | Revisión adversarial de solo lectura sin defecto; punctual, no review total del motor |
| 2026-10-05 | La configuración V1 serializa sólo geometría reconstruible desde modelos explícitos. Si slider-crank y binding de puertos resuelven todos los campos, el callback legado queda ignorado y no es parte de la identidad | Ejecutar también el callback podría introducir efectos laterales o fallos que la configuración no puede reproducir; callbacks arbitrarios requerirían otro contrato | JSON canónico y snapshot inicial exactos, guard de deriva y cinco pruebas focales; la regresión integrada amplia actual está registrada en `program-status.json` | Revisión independiente read-only del delta; acotada a la ruta geométrica, no aceptación del motor completo |

## 18. Convenciones

Sin cambios a P4–P9, contratos, umbrales ni parámetros científicos. Artefactos
sintéticos siguen etiquetados y no sustituyen validación experimental.
`effective_length_m` es geometría/provenance, no una longitud activa en la
interfaz P3 ideal. Todo cambio de semántica de reservoir requiere capability y
contrato propios.

## 19. Blockers abiertos

- Reservoir boundary: `KT100_HYBRID_V2_BLOCKED_BY_RESERVOIR_BOUNDARY_CAPABILITY`
  (`docs/gasdynamic/generalized_reservoir_boundary_v2_debt.md`).
- Reed dinámica integrada: revisión de dominio encontró decisiones materiales
  aún sin contrato. La ecuación existente es
  `m*x'' + c*x' + k*x = Δp*Ap`; entre impactos
  `dE_reed/dt = Δp*Ap*x' - c*x'^2` y cada impacto disipa
  `0.5*m*(1-e^2)*(v^-)^2`. No está definido cómo discretizar presión variable
  dentro de SSPRK2/impactos, cómo localizar presión/trabajo en gas upstream vs
  cárter, ni dónde depositar disipación de damper/impacto. La revisión concluye
  que se requiere decisión de modelado; no integrar por splitting ni inferir
  esas asignaciones.
- AFR estequiométrica y enlace de `Q_F` con LHV siguen sin definición; las
  cantidades dependientes permanecen UNDEFINED. El pseudo-especie fuel al
  cierre exacto de escape no equivale al total de combustible atrapado; no
  inferir ese total desde el inventario global terminal ni desde la captura de
  reactivos de P7.
- El núcleo integrado/comercial sigue parcial, sintético y sujeto a
  `CONDITIONAL_ON_P4`; no hay validación experimental.
- La configuración canónica cubre sólo slider-crank y puertos genéricos
  explícitos; no serializa geometría arbitraria de callback. La auditoría
  externa añade prioridades 1 abiertas: fuerza de
  pared (A1), presión inicial de cámaras del fixture (A2), composición externa
  independiente en admisión/escape (A3), redondeo de especies y retries del
  harness (A4), productores versionados de evidencia (C1), reconciliación de
  claims de revisión (C5) y normalización durable (C8/C9). A1–A3 invalidan para
  aceptación la evidencia de ciclo A/B ya archivada; conservarla y marcarla
  supersedida. La reed dinámica, combustible, reservoir V2, generalidad de
  Fixture B y validación experimental siguen siendo límites adicionales. La
  auditoría independiente cubre `ab92aee..8cdf66e`; las revisiones posteriores
  de cambios locales necesitan recibos propios.
