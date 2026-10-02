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
