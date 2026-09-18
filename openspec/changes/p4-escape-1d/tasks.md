## P4 — orden cec0f5b3
- [x] Registrar aceptación humanaP3, congelar baseline y archivar cambio aceptado.
- [x] Revisión independiente inicial de contrato de puerto y limitaciónBCexterior.
- [x] Formalizar fixtures y ejecutar P4A/E01–E05 cuantitativos; revisión independiente PASS.
- [ ] P4B/E06–E11, reflexiones, longitud, RPM, refinamiento y CFL.
- [ ] Sólo trasP4A/P4B PASS: camino híbrido, revolución cronometrada y E12–E15.
- [x] RegresionesP0/P2/P3 y revisión independiente final (confirma bloqueo, noP4PASS).
- [ ] Gate final y aceptación humana posterior. NoP5.

P3 archivado con14/19 tareas: las5 restantes son casillas históricas reservoir,
explícitamente sustituidas porR1; no se marcaron como realizadas. CierreR1 y
aceptación humana acreditados. Se preserva borrado ajeno redme.txt.

## Estado final — P4_BLOCKED_WAVE_PHYSICS / SCIENTIFIC_CHANGE_REQUIRED
P3 aceptado por la usuaria y archivado en2026-09-18-p3-acoplamiento-conservativo.
Baseline ec6ec55 y72 evidenciasP3 intactos; aceptación en docs/gasdynamic/p3_human_acceptance.json.
P4 no se archiva. No motor híbrido, convergencia periódica, potencia indicada ni
comparación entre ciclosmotor: dependen deP4B PASS que no se obtuvo. NoP5.

Implementado sólo banco experimental aislado: puerto variableideal, cara dividida
P3+pared reflectiva, integrador conjuntoSSPRK2 con eventos/CFL, adaptador de ductos
existentes, sensores/snapshots/ledgers. El camino2T_0D_BASELINE sigueintacto.
P4C/2T_0D1D_EXHAUST de motor no creado; no presentar banco como motorhíbrido.

| Gate | Resultado |
|---|---|
| E01–E05 cerrado/apertura/descarga/cierre/backflow | PASS, revisión independiente |
| E06–E09 recto/difusor/convergente/cadena | Casos individuales PASS |
| E10 longitud, incluido control a volumen idéntico | PASS |
| E11 RPM y eventos (banco, no motor) | PASS |
| Refinamiento difusor | PASS |
| Refinamiento descarga | FAIL en presión integrada y masa |
| SensibilidadCFL focal ambos bancos | PASS |
| E12–E14 motor/conservación/convergencia/comparación | NOT_RUN, bloqueados porP4B |
| E15 positividad | PASS en19 bancos; motor NOT_RUN |

Criterios congelados antes de ejecutar: no se ajustaron tras resultados.
Mayor residuo global normalizado3.378286968e-15. Puerto cerrado:m/E/F exactamente0.
Backflow al cilindro usaYlocal~.2, noYatmósfera0. Reacción axial sobre abertura
y paredcomplementaria registrada porstage. Cd1, sin calibración/pérdida añadida.
Eventos físicos90°/112.2040961°/247.7959039°/270°, Amax200mm², todos alcanzados.

## Incumplimiento de refinamiento — descarga
| N | Integral presión (Pa·s) | Intercambio masa (kg) | Arrival (s) |
|---|---:|---:|---:|
| 100 | 164.729319651 | -9.70056603322e-05 | 0.00087477247055 |
| 200 | 164.804998778 | -9.70077286939e-05 | 0.000879296215498 |
| 400 | 164.899734482 | -9.70099933774e-05 | 0.000874901407169 |

Diferencias presión .0756791278→.0947357040 Pa·s; masa2.06836170034e-9→
2.26468347229e-9kg: ambas aumentan. Revisor recalculó desdehistory, flujos por
stage y cambio final de masa, descartando bugdelagregador. Sensores reales
.099/.1005/.09975m; fallo de masa independiente de posiciónsensor. Magnitud
pequeña no autoriza relajar el criterio. Causa numérica/física no determinada.
No atribuirla a la BC sin evidencia. No repetir bancos ni iniciarP4C.

Timingblowdown: llegada102kPa sensores .099/.297m en .000873870597/.001438368459s;
delta .000564497862s dentro envolvente .000328402386.. .000615957624s.
Velocidades u+a muestreadas340.9325..544.5545m/s; no trayectoria reconstruida ni
validación de amplitud fuerte. Pulso débil100Pa separado para coeficientes.
Longitud/cadena: cambiarheader.2→.3m retrasa onda; controlheader+.1/tail−.1
conserva volumen4.08407045e-4m³ y también retrasa retorno. No es sólo volumen.
RPM2500/3000/3500: misma llegada física.000729366873s, ángulos190.9405031 /
193.1286037 /195.3167043°. No acredita régimenperiódico.

## Casos ejecutados y conservación
19 integraciones nuevas, todas completas;510.907s sumados dentro delsolver,
no tiempo total de orquestación. Máximo271.25s, inferior600s; no timeoutfísico.

| Caso | Tiempo (s) | Residuo global máximo |
|---|---:|---:|
| closed_N100_CFL0.4 | 1.828 | 1.6144e-16 |
| blowdown_N100_CFL0.4 | 17.844 | 1.9855e-15 |
| backflow_N100_CFL0.4 | 5.406 | 6.3219e-16 |
| straight_N100_CFL0.4_RPM3000 | 2.031 | 4.2153e-16 |
| diffuser_N100_CFL0.4_RPM3000 | 2.641 | 4.3901e-16 |
| converger_N100_CFL0.4_RPM3000 | 3.422 | 1.2541e-15 |
| chain_N100_CFL0.4_RPM3000 | 4.000 | 7.3072e-16 |
| long_N100_CFL0.4_RPM3000 | 4.469 | 5.3439e-16 |
| equal_volume_N100_CFL0.4_RPM3000 | 4.281 | 5.6364e-16 |
| chain_N100_CFL0.4_RPM2500 | 3.938 | 7.3072e-16 |
| chain_N100_CFL0.4_RPM3500 | 3.968 | 6.1172e-16 |
| diffuser_N200_CFL0.4_RPM3000 | 13.234 | 2.5985e-16 |
| diffuser_N400_CFL0.4_RPM3000 | 48.531 | 6.0445e-16 |
| diffuser_N100_CFL0.2_RPM3000 | 5.203 | 6.6553e-16 |
| diffuser_N100_CFL0.6_RPM3000 | 1.969 | 3.2333e-16 |
| blowdown_N200_CFL0.4 | 70.360 | 3.3783e-15 |
| blowdown_N400_CFL0.4 | 271.250 | 2.7061e-15 |
| blowdown_N100_CFL0.2 | 34.516 | 3.0037e-15 |
| blowdown_N100_CFL0.6 | 12.016 | 1.5523e-15 |

## Evidencia y revisión
- [x] 88 pruebas PASS,23.571s; incluye5 focales puerto/geometría y83 históricas.
- [x] P2 completo T01–T12/58 finales y FIRST_ORDER/R4 reevaluados offline PASS.
- [x] Siete regresiones históricasP0 offline PASS; sin nuevas campañasP0/P2/P3.
- [x] P3 C00/C00B reevaluados; evidenciaC01–C12 intacta por72SHA256, siete archivosP3 y27P2 congelados.
- [x] Revisión independiente /root/p3_review: P4A PASS, P4B STOP; regresiones confirmadas.
- [x] Autorrevisión de alcance/índice/hashes/documentación separada; no revisión general nueva.
- [x] Gráficas de banco inspeccionadas visualmente; no son capturaWindows ni aceptaciónhumana.

Frontera exterior nonreflectingP2 con estadoexplícito. Revisor documentó salto
potencial100000→98724.6267Pa al cambiarentropía donante en un estado térmico
artificial. No se cambióBC; en campaña no hay evidencia de que ese fenómeno cause
el fallo. Se conserva alcance de truncamiento característico lineal/local, no
radiación de escape real ni anecoico universal.

Dos fallos de infraestructura preservados: primerP4B se rechazó por timeoutdel
comando fuera del rango del esquema, antes de integrar; corregido a3500s totales,
600s porcaso intactos. P4_CLOSE completó88tests yregresiones, pero falló al fusionar
checkIDhistorical duplicado con nombrecomando. Corregido a baseline_command y
validado por IDsdisjuntos/dry-run, sin repetirtests. No afirmar que ese runnativo
pasó: permaneceFAILED_INFRASTRUCTURE. P4A nativoBLOCKED sólo reviewerhook;
P4B nativoSCIENTIFIC_CHANGE_REQUIRED por fallo real. Dictámenes adjuntos separados.

Comandos reales desde raíz, Python .venv: `-m dev_orchestrator.runners.run_phase`
P4A/P4B/P4_CLOSE con `--dependency P2=docs/gasdynamic/p2_accepted_dependency.json`.
No relanzar campañas trasSTOP sin resolver decisióncientífica. Evidencia:
results/p4-exhaust-20260918; gráficas port-blowdown.png/svg y waves-refinement.png/svg.
No publicar, no modificarcredenciales/globales, noarchivarP4. Borradoajeno redme.txt
conservado fuera decommits. OpenSpecautomático sigueomitido.

OpenSpec estricto: cambioP4 y specconsolidadaP3 PASS. AtributosGit locales
preservan bytes de los tres módulosP4 revisados; sin configuración global.
