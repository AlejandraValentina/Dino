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
