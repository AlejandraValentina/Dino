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

Pendiente de la primera sesión autónoma. Primer blocker a investigar:
`No consistent reservoir inflow branch` (sección 7).

## 16. Arquitectura vigente

Pendiente.

## 17. Decisiones científicas

| Fecha | Decisión | Alternativas | Evidencia | Revisión |
|---|---|---|---|---|

## 18. Convenciones

Pendiente.

## 19. Blockers abiertos

- Reservoir boundary: `KT100_HYBRID_V2_BLOCKED_BY_RESERVOIR_BOUNDARY_CAPABILITY`
  (`docs/gasdynamic/generalized_reservoir_boundary_v2_debt.md`).
