# MotorSim 2T Commercial Core — estado global

Registro del 2026-10-02. La misión continúa **sin readiness integrada**. Las
capacidades independientes tienen pruebas; siguen abiertos los enlaces entre
subsistemas que necesitan una extensión de etapas P5-C/P6 nueva y separada.
El estado durable y máquina-legible está en
`results/2t-commercial-core-20261002/program-status.json`.

## Estado por fase

| Fase | Estado | Verificado / pendiente |
|---|---|---|
| 1. Harness híbrido | Bloqueo local | Detectores, auditoría y checkpoint/restart de paso aceptado pasan con fixtures. Falta ejecutar un motor a través de ciclos completos y anclas de campaña. |
| 2. KT100 V2 | Bloqueo local congelado | No se permite reintentar ni ajustar parámetros en esta misión. |
| 3. Puertos 2T | Geometría implementada; topología parcial | Las áreas genéricas se enlazan con las dos rutas transfer ya existentes en P5-C. Una tercera ruta se rechaza. Persistencia de proyecto, GUI y topología arbitraria siguen pendientes. |
| 4. Scavenging | Métricas y adaptador geométrico implementados | Exige ciclo completo, cierre geométrico exacto, evidencia primaria y ledgers P6 concordantes. Falta comprobar métricas bajo operación periódica real. |
| 5. Reed | Componente implementado | Integración de estado mecánico en etapas P5-C/P6 bloqueada por falta de hook de estado de etapa; P5 histórico quedó intacto. |
| 6. Cámara de expansión | Componente verificado | Reutiliza malla/solver quasi-1D existente; calcula trazas y tiempos característicos, sin amplitudes de reflexión sintéticas. |
| 7. Thermal | V1 prescrito verificado | Temperatura de pared, `CONSTANT_H_V1` y ledger por ciclo; falta acoplamiento energético en las etapas del motor. |
| 8. Combustión | Wiebe prescrito V2 verificado | Sin conversión química, liberación de calor en solver ni extensión predictiva-lite. No hay parámetros defendibles para ella. |
| 9. Cárter | Geometría y link reversible parciales | Falta integración de volumen, calor, leakage y acoplamiento de admisión/transferencia en el RHS común. |
| 10. Pérdidas mecánicas | Contabilidad verificada | FMEP, IMEP/BMEP, potencia y torque indicados/al freno como cálculo aislado con inputs explícitos. |
| 11. Combustible | Contabilidad verificada; binding P6 pendiente | El modelo consume masas por especie explícitas. El evidence actual no persiste delivered fresh-air/fuel por separado; no se deriva AFR de un contador agregado. |
| 12. Powervalve | Geometría verificada | Interpolación RPM y techo móvil del escape; sin servo ni calibración inventada. |
| 13. Red de admisión | Componentes verificados; integración pendiente | Volúmenes, junction helper y estimación Helmholtz están disponibles. Falta compartir etapas SSPRK y ledger global. |
| 14. Outputs | Esquema verificado; recolector core pendiente | Units, provenance, estados undefined y no-claims. Falta reunir una trayectoria completa arbitraria desde evidencia primaria del motor. |
| 15. Importación experimental | Importador exploratorio verificado | Pressure/dyno, unidades, incertidumbre y provenance; no cambia ni habilita P9. |
| 16. Segundo caso | Referencia documental parcial | Honda CR250R 2007: campos publicados documentados, datos ausentes `null/UNKNOWN`; no listo para simulación. |

El manifiesto parcial Honda se basa en la ficha oficial
`https://hondanews.com/en-US/releases/release-707d4f21703e9943a7cb22004c34bfff-2007-honda-cr250r-specifications`.
La fuente proporciona ciclo, cilindrada declarada, diámetro/carrera,
compresión, admisión reed y válvula RC; no proporciona geometría de puertos,
biela, volumen de cárter, conductos ni estados iniciales. No se completaron
esos campos con supuestos.

## Comprobación y límites

El 2026-10-02 pasaron 204 pruebas focales para las capacidades, sus adaptadores
y los recorridos P5-B/P5-C/P6 seleccionados. OpenSpec estricto pasó para
`motorsim-2t-commercial-core` y `reference-engine-hybrid-harness`; `git diff
--check` y `git lfs fsck` también pasaron. El conjunto histórico P4–P8 de 346
pruebas estaba registrado como aprobado y no se repitió para este delta. El
contrato P9 no cambió; SHA-256:
`79fbe9b88d26fc4af5083d65d468f59c9208535f0ab389d2f3cb9a7654b88a4d`.

No se ejecutaron campañas físicas en esta continuación. La evidencia de
componentes aislados no prueba una configuración completa ni concede claims
experimentales o predictivos. El delta recibió autorrevisión, no una revisión
independiente nueva. No hubo push. Los directorios históricos r2/r3/r4/base
siguen sin stage.

## Continuación de integración end-to-end

La orden vigente autoriza un integrador nuevo sin alterar P5/P6 históricos.
El primer prototipo `motorsim.integrated_2t` usa un solo estado SSPRK2 para
crankcase/cilindro, admisión, N transfers (mínimo 3) y escape, reutiliza EOS,
malla, HLLC, interfaz P3 y selección de donor P6. Un fixture artificial
estático acredita conservación de masa/energía/cuatro especies por etapa,
flujo inverso con donor real, rechazo CFL, fuente térmica de pared desde el
estado de cada etapa, trazas y checkpoint JSON/replay: 7 pruebas focales pasan.
Esto NO es un ciclo de motor completo.

Continúan pendientes reed dinámica, admisión geométrica/reed, malla/chamber
de expansión en ciclos, fuentes de combustión, contabilidad de combustible
y brake work, scavenging a cierres exactos, periodicidad P1/P2, collector
primario completo, dos fixtures integrados y regresiones P4–P8 ejecutadas ahora.
La frontera reservoir V1 aún puede producir `No consistent reservoir inflow
branch`; no hay fallback implícito ni se reintentó KT100. El Commercial Core
permanece `MOTORSIM_2T_COMMERCIAL_CORE_PARTIAL`.

### Continuación: restauración, CFL y reed estática en etapa común

En la continuación desde `ab92aee`, se corrigió el gate de CFL para incluir el
límite área-volumen de cada celda (además de `dx/(|u|+a)`) y la tasa de
flujo saliente bruto de las cámaras 0D, sin ocultarlo con entradas simultáneas.
La revisión read-only independiente
confirmó el arreglo del CFL original y encontró una incoherencia reproducible
en reloj/volúmenes de restart; se añadió rechazo atómico si el ángulo envuelto
no corresponde al no envuelto o si el volumen guardado no coincide con la
geometría declarada al restaurar.

Se conectó el modelo existente `STATIC_REED_V1` al área de admisión en cada
stage SSPRK2 usando la diferencia de presión ducto-cárter de ese mismo stage.
El flujo de gas/especies sigue usando la interfaz compartida y el donor P6.
Las pruebas cubren la reed cerrada y abierta, conservación, backward donor,
CFL 0D/1D, reinicio y rechazo de geometría obsoleta. Suite agrupada actual:
67 pruebas aprobadas, incluida `tests/test_reed.py`; OpenSpec estricto,
`git diff --check`, `git lfs fsck` y hash P9 aprobados.

La revisión independiente fue puntual sobre el fundamento CFL, el restart y
la reed estática integrada; sus hallazgos se corrigieron y la pasada final no
encontró defectos concretos en ese alcance. No es revisión independiente de un
motor completo. El token de identidad geométrica sigue siendo un binding
declarado por el caller; la validación de volumen al ángulo restaurado no prueba
equivalencia de callbacks arbitrarios para ángulos futuros. La reed dinámica,
cámara de expansión ejecutada dentro de ciclos,
combustión, combustible integrado, desempeño al freno, evidencia periódica,
fixtures completos y regresiones amplias P4–P8 actuales siguen pendientes.
Commercial Core continúa `MOTORSIM_2T_COMMERCIAL_CORE_PARTIAL`; no se reintentó
KT100 ni se ejecutaron campañas físicas.

### Continuación: fuente prescrita P7 en el estado integrado

`IntegratedEngine2T` ahora ofrece P7 opcional por ángulo de ignición. En cada
stage SSPRK2 usa el evento P7 existente, capturado desde las cuatro especies
reales presentes en el cilindro, para convertir fresh_air/fuel a burned y sumar
el calor prescrito al RHS de energía del cilindro. No se añadieron química,
AFR, LHV ni propiedades de combustible. El ledger global de especies distingue
esa conversión interna del transporte externo; el de energía acredita el calor
P7 una sola vez junto a flujo externo, trabajo móvil y pérdidas térmicas.
El checkpoint V2 guarda evento activo e historial P7 y rechaza configuraciones
con otro ángulo de ignición. Los pasos que cruzan los límites de ignición o los
40° del evento se rechazan para que el integrador los alinee explícitamente.

La prueba focal integrada pasó 20/20 y la regresión agrupada con P5-C/P6/P7,
reed y puertos pasó 72/72. OpenSpec estricto pasó. Esto comprueba acoplamiento
P7 en trayectorias breves y restart/replay del evento, no consumo completo,
fuel-flow derivado, ciclos, rendimiento al freno ni Commercial Core completo.
La revisión independiente read-only de este delta confirmó etapas, balances,
captura transaccional y cronología de restart sin hallar defectos concretos;
no revisó el motor completo. La revisión del motor completo sigue pendiente.
Una prueba adicional vincula la malla multi-sección de `ExpansionChamber` a la
ruta exhaust del mismo integrador y comprueba que sus celdas y caras se
actualizan en los dos stages con transporte de especies y balance global.
Esto verifica el enlace de malla, no ciclos completos ni reflexión/calibración
de cámara.
El adaptador stage geometry además mapea explícitamente cada ducto genérico a
una ruta 1D y calcula aperturas existentes de puertos y powervalve según ángulo
y RPM; una prueba comprueba la identidad de esa configuración en restart. Esta
parte todavía se verifica en resolución de stage, no en un paso angular
aceptado con variación de abertura.
La revisión read-only del adapter detectó que el mapeo podía mutar después de
congelar la identidad del checkpoint; ahora el constructor copia el mapa a una
vista inmutable y la prueba rechaza mutación externa/interna. La revisión
read-only final confirmó el cierre sin encontrar otro defecto en ese alcance.

### Continuación: Fixture A de dos ciclos y reanudación

El 2026-10-02 un fixture controlado sintético completó los ciclos angulares
0→360° y 360→720° con `IntegratedEngine2T`: piston-port intake, reed estática,
cárter y cilindro slider-crank, tres transfer routes, escape por mesh
multi-sección de expansión, cuatro especies, P7 prescrito a 300° y pérdida
térmica de pared. La atmósfera usa explícitamente `(.98 fresh_air, .02 fuel,
0 residual, 0 burned)` solo como supuesto sintético del fixture; no describe
AFR, LHV ni combustible real. Los dos ciclos fueron admisibles bajo
`max_cfl=0.4` y los balances integrados globales de masa, energía y especies
cierran dentro de las tolerancias focales. El fixture registra delivery fresco
y de combustible, combustible y carga fresca expulsados durante scavenging,
fuente P7, calor de pared y trabajo indicado no vacuos.

El checkpoint tomado en 360° se restauró y la segunda vuelta reprodujo el
snapshot JSON terminal a 720° exactamente cuando el scheduler reutilizó el
grid angular absoluto de 0.5° y los mismos límites P7/ciclo. Se canonicalizó
la forma JSON del checkpoint porque listas y tuplas internas antes podían
producir snapshots distintos aun con los mismos valores. También se versionó
el estado integrado a V3 para persistir `fuel_short_circuited_kg`, calculado
desde el flujo de especie fuel del donor de escape; el contador agregado de
fresh short-circuit se conserva.

La prueba aplicó `MechanicalLossModel` al trabajo indicado medio de esos dos
ciclos y a un FMEP sintético explícito, y obtuvo brake work positivo. Eso aún
no es un collector del motor ni un resultado persistido por ciclo. No se
calcularon métricas de combustible porque faltan observables P6 exactos de
trapping/retención por cierres y una relación científicamente defendible entre
el calor prescrito P7 `Q_F` y un LHV. Tampoco se generó el record primary
compatible con `REFERENCE_PERIODIC_CONVERGENCE_V1`, por lo que P1/P2 no se
evaluó. Solo hay un fixture, dos ciclos y replay desde checkpoint; faltan dos
recorridos completos independientes, cierres geométricos exactos y collector
de ingeniería unificado. No se declara convergencia ni readiness.

Comprobación actual: 21 pruebas focales de `tests/test_integrated_2t.py` y
73 pruebas agrupadas de integrador/P5-C/P6/P7/reed/puertos aprobadas; OpenSpec
estricto, compilación del integrador y `git diff --check` pasan. La revisión de
este delta es autorrevisión puntual, no revisión independiente. El fixture usa
la frontera `nonreflecting` ya existente; `GENERALIZED_RESERVOIR_BOUNDARY_V2`
sigue sin implementación y KT100 permanece congelado. P4 sigue siendo una
dependencia condicional y P9 no se modificó.

### Continuación: donante de especie en caras internas y trayectoria de puertos

Al extender el fixture de `IntegratedPortBinding2T` desde la mera evaluación
de etapas hasta pasos SSPRK2 aceptados, apareció una pérdida inadmisible de
especie fresca durante flujo inverso interno. El diagnóstico localizó una doble
selección de donante: el integrador preseleccionaba celda donante/receptora y
después el helper P6 volvía a aplicar el signo del flujo sobre argumentos ya
reordenados. Se corrigió pasando los estados siempre en orden geométrico
izquierda/derecha para que el selector compartido elija una sola vez. La nueva
aserción contrasta cada flujo interno negativo con la composición de la celda
derecha en ambos stages usando fracciones iniciales distintas a cada lado. La
misma trayectoria compara las áreas resueltas de cada stage con el binding a
su ángulo y RPM, y confirma al menos un punto donde la powervalve cambia el
área del puerto de escape principal.

Resultado actual: el recorrido artificial a 3000 rpm completó pasos aceptados
de 0° a 90° con áreas genéricas, tres transferencias, escape auxiliar y
powervalve; `tests/test_integrated_2t.py` pasa 15/15 y la regresión agrupada
de seis módulos pasa 67/67. Esto no acredita un ciclo, cierre
geométrico, periodo ni viabilidad física de motor. La revisión independiente
read-only de este delta confirmó el donante izquierda/derecha para ambos signos,
la correspondencia de estado/flujo por stage y la resolución de áreas a ángulo
y RPM; no encontró defectos concretos. Es una revisión puntual, no de un motor
completo; se conserva separada de la autorrevisión.

### Continuación: geometría móvil de cárter y cilindro

El integrador ahora acepta el modelo existente `CrankcaseGeometry` V2 junto
con la relación de compresión del cilindro. Resuelve ambos volúmenes y sus
tasas opuestas usando el mismo ángulo y RPM de cada stage SSPRK2; el término
`-p dV/dt` permanece en el RHS de energía que ya era dueño del trabajo de
frontera móvil. La identidad del checkpoint incluye la configuración del
modelo. Una prueba de integración comprueba TDC/BDC y posición intermedia,
ambas tasas por stage, una transición móvil aceptada y los ledgers globales
de masa/energía, además de rechazar restart con compresión distinta.

Esta conexión reduce la brecha de geometría del workstream 17b, pero no cierra
la reed dinámica ni prueba ciclos completos. La ejecución focal pasó 16/16
pruebas; el grupo actual integrado/P5-C/P6/P7/reed/puertos pasó 68/68.
OpenSpec estricto, compilación Python y diff check pasaron. La revisión
independiente read-only de esta conexión sigue pendiente; no se presenta la
autorrevisión como independiente.

### Continuación: evidencia primaria, trabajo indicado y collector parcial

La evidencia primaria por ciclo ahora se reconstruye desde los stages SSPRK2
aceptados y comprueba continuidad de estado, CFL, flujos externos, fuentes P7 y
térmicas, inventarios y deltas de los ledgers del checkpoint. Al integrar el
observable de trabajo se detectó que el ledger energético guarda `-p·dV/dt`,
mientras el trabajo indicado producido es `∮p·dV`; la salida de ciclo invierte
ese signo sin alterar el balance energético del solver. También se corrigió el
signo del acumulador de masa P7 que realmente se hubiera limitado; la masa
limitada verificada para el fixture es cero. La presión inicial sintética de
cárter/cilindro se igualó con los 101325 Pa de la atmósfera, derivada de la EOS
existente.

`make_integrated_engineering_output` genera `MOTORSIM_ENGINEERING_OUTPUTS_V2`
para una trayectoria completa con hash de configuración, señales de ambas
cámaras, especies por celda y cuatro masas por especie/celda de cada ducto,
Mach/estado por celda, flujo firmado por cara, áreas/flujos de puerto, calor P7
y de pared, trabajo indicado y caudal de combustible ligado al ledger P6. El
collector reintegra los valores desde la trayectoria antes de emitir y rechaza
resúmenes corruptos. V1 queda intacto. Las pérdidas al freno requieren pasar un
`MechanicalLossModel` explícito. AFR, BSFC/ISFC y métricas de retención/scavenging
permanecen indefinidas hasta disponer de las magnitudes de entrada necesarias.

Se extendió el diagnóstico del mismo fixture A a seis ciclos, sin cambiar
solver, malla, CFL ni contrato. El ciclo 1 tiene trabajo indicado negativo; la
comparación 1→2 queda `INVALID`, y las comparaciones 2→3, 3→4, 4→5 y 5→6 son
`FAIL` bajo `REFERENCE_PERIODIC_CONVERGENCE_V1`. No se concede P1/P2. El primary
record conserva trazas completas de estados de ductos y aperturas, y V2 emite
canales tipados por ducto/celda/cara; los cierres geométricos exactos y sus
snapshots P6 siguen pendientes. V1 permanece sin cambios. La prueba focal de
integrador/output pasó 33/33 y el grupo P5-C/P6/P7/reed/ports/output pasó 85/85;
OpenSpec estricto, compilación y diff check pasaron. Las regresiones amplias
P4–P8 y revisión independiente de este delta siguen pendientes.
Fixture A sigue bloqueado para periodicidad; Fixture B y las regresiones amplias
actuales P4–P8 siguen pendientes. La revisión de este delta es autorrevisión,
no una revisión independiente del motor integrado.

### Cierres exactos y collector alineado — continuación del 2026-10-02

La evidencia primaria cambió a
`MOTORSIM_INTEGRATED_2T_CYCLE_PRIMARY_V2`. Para RPM constante, el builder usa
la geometría genérica vinculada y la posición powervalve de ese RPM, y captura
los estados terminales aceptados en los últimos cierres agregados exactos de
transferencia y escape. El fixture A agenda ambos eventos exactamente. Si el
cierre no existe o no hay una única fila SSPRK2 en el evento, el snapshot queda
`UNAVAILABLE`; no se interpola. Los ratios de scavenging solo se calculan con el
reference-charge mass explícito, sintético, de `1e-4 kg` usado en esta prueba.

Se revisó también la alineación de los canales angulares: cada muestra al inicio
de paso usa estado y RHS SSPRK2 de esa misma etapa. El último punto reevalúa
solo lectura el estado terminal aceptado; su fuente P7 se rotula como request
instantáneo anterior al limitador de un futuro paso y queda fuera de integrales
y conservación. Los outputs mantienen null/UNDEFINED si se elimina la evidencia
exacta de cierre.

El perfil auxiliar sintético de escape se corrigió para incluir un intervalo
cerrado. Su versión anterior solo alcanzaba área cero en puntos aislados, por lo
que no existía cierre agregado según la propia geometría. Se repitieron seis
ciclos completos a 3000 RPM/CFL 0.4: trabajo indicado
`[-111.5764, 17.2841, 52.2598, 57.1227, 53.2165, 50.4537] J`; todos capturaron
cierres exactos de transferencia y escape. Los ratios de scavenging calculados
con la referencia sintética explícita fueron
`[0.57136, 0.49767, 0.47893, 0.50271, 0.53278, 0.55344]`. El ciclo 1 conserva
trabajo negativo; 1→2 es INVALID y los pares siguientes no alcanzan el gate
periódico. El detector no clasifica P1/P2 ni hay convergencia. Los residuos
globales finales fueron `1.10e-18 kg` de masa y `-1.07e-12 J` de energía; los
residuos por especie permanecen dentro de `1e-18 kg`.

La trayectoria primaria y los seis outputs se conservaron comprimidos en
`results/2t-commercial-core-20261002/fixture-a-integrated-cycles-20261002-v2.json.gz`
(SHA-256 `c037c83f81796b7fb9a93bdae6b6ffff070c44e030977ef69d6329dcf1279dc2`,
60,694,798 bytes) y se asignaron a Git LFS para no guardar el blob en Git. Pasan
33/33 pruebas focales y 85/85 del grupo integrado/P5-C/P6/P7/reed/puertos/output.
La suite amplia actual seleccionada por prefijo P4–P8 pasó 300 pruebas en `.venv`
Python 3.11, con cuatro warnings de deprecación NumPy preexistentes. Siguen
pendientes revisión independiente, P1/P2, reed dinámica, boundary V2, Fixture B
y las vinculaciones defendibles de combustible/mecánica. No declarar readiness.


### Revisión independiente puntual del delta V2 — 2026-10-02

Una revisión read-only independiente comprobó la resolución de powervalve a RPM
constante, la selección de los últimos cierres agregados, el requisito de un
único endpoint aceptado exacto, la captura de `stage_states[2]`, y la alineación
de muestras de salida con el estado y RHS de su stage. Verificó además la
evaluación read-only del endpoint terminal, el rebuild de integrales, la
separación del contrato V1 y outputs V2, y la identidad del artefacto LFS. No
encontró defectos materiales en este delta. La revisión fue puntual, no acredita
convergencia P1/P2 ni un motor integrado completo.


### Continuidad y replay de Fixture A — 2026-10-02

Se compararon dos recorridos de seis ciclos completos (3000 RPM, CFL 0.4): uno
continuo y otro reanudado desde checkpoint al ciclo 3. La igualdad estructural
directa abarcó el snapshot final completo, los seis registros primarios y los
seis outputs V2. Se aceptaron 11.176 pasos; en cada ciclo se mantuvieron los
residuos globales de masa/especies en el orden de 1e-18 kg y energía en el orden
de 1e-12 J. El brake output se calculó con un modelo de pérdidas sintético y
explícito. No hay P1/P2: el trabajo del primer ciclo es negativo y los pares
posteriores siguen fallando. Esta comprobación no cambia el estado parcial.
Evidencia de comparación: `results/2t-commercial-core-20261002/fixture-a-restart-replay-audit-20261002.json`;
la trayectoria primaria permanece en el artefacto V2 LFS.


### Estado actualizado de integración — 2026-10-02

Fixture A interno sintético alcanzó `PERIOD_1` en el ciclo 16: la comparación
12→13 fue FAIL, seguida por tres PASS consecutivos 13→14, 14→15 y 15→16 bajo
`REFERENCE_PERIODIC_CONVERGENCE_V1`. Los ciclos 1–12 regenerados coincidieron
exactamente con las trayectorias primarias previas. El primer ciclo conserva
trabajo indicado negativo. Este resultado acredita periodicidad posterior del
fixture sintético; no cambia la dependencia `CONDITIONAL_ON_P4`.

Se integró además la contabilidad por trayectoria de fuel entrante, conversión
P7, short-circuit, inventario final y residual de balance; el recolector define
AFR bruto y consumos específicos solo cuando las entradas/potencias existen.
Equivalence ratio queda UNDEFINED sin estequiometría explícita; el inventario
terminal no se confunde con fuel atrapado. No se infieren LHV ni combustible
real. El estado global permanece `MOTORSIM_2T_COMMERCIAL_CORE_PARTIAL`; Fixture B
sigue gated mientras no se cierren las entradas y métricas de fuel necesarias.
Evidencia P1: `results/2t-commercial-core-20261002/fixture-a-periodicity-extension-20261002-v1.json.gz`.


### Fixture B y estado de readiness — 2026-10-02

El segundo fixture sintético, con las longitudes de cámara de expansión
aumentadas 20 %, completó 19 ciclos a 3000 RPM/CFL 0.4 y alcanzó `PERIOD_1` en
el ciclo 19. Tres comparaciones PASS consecutivas ocurrieron en 16→17, 17→18 y
18→19; ciclo 1→2 es INVALID. Los outputs V2 por ciclo se validaron con el mismo
collector y una pérdida mecánica explícita sintética. La evidencia primaria y
outputs completos están en
`results/2t-commercial-core-20261002/fixture-b-long-chamber-primary-20261002-v1.json.gz`.

Un intento alternativo de no-reed piston-port no completó el primer ciclo: el
paso en 107.651626° siguió inadmisible tras 25 reducciones, y no se atribuye a
una demostración exitosa. Ambos fixtures que sí completaron permanecen
`CONDITIONAL_ON_P4`. No hay configuración estequiométrica aprobada, por lo que
equivalence ratio no se inventa; la reed dinámica no está en el grafo SSPRK2 y
GENERALIZED_RESERVOIR_BOUNDARY_V2 sigue bloqueada por decisión científica. El
estado global permanece `MOTORSIM_2T_COMMERCIAL_CORE_PARTIAL`.


### Validación final de la tanda — 2026-10-02

La regresión integrada de 85 pruebas y la suite P4–P8 de 300 pruebas pasaron;
esta última emitió cuatro warnings de deprecación NumPy ya existentes.
OpenSpec estricto pasó. El artifact de outputs de fuel de A se reconstruyó desde
primary V2 aceptada y validó cuatro outputs; `equivalence_ratio` quedó null/
UNDEFINED sin estequiometría, y no se infirió LHV. El árbol mantiene solo los
cuatro directorios históricos KT100 como untracked; no se incluyen en el stage.
