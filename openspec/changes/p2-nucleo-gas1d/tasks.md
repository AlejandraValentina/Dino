## P2
- [x] Leer orden/P1 y registrar aceptación P1 sin modificar contrato ni baseline.
- [x] Implementar núcleo aislado first-order y tests unitarios geométricos/numéricos.
- [x] Implementar referencias independientes, matriz contractual y evidencia P2A.
- [x] Ejecutar P2A mediante orquestador; revisar resultados y defectos concretos.
- [x] Revisión independiente read-only y gate P2A.
- [ ] P2B únicamente después de P2A PASS: MUSCL/minmod y SSP-RK2, repetir matriz.
- [x] Verificar hashes/regresiones P0, OpenSpec, documentar gate y commits.

La eliminación previa de redme.txt es ajena y no se incluye. Sin UI, proyecto JSON,
paquete ni P3. Reparaciones después de primera ejecución: 0/3.
11 unit tests iniciales aprobados; aún no acreditan T01–T12 completos.

## Cierre por STOP científico — 17/09/2026
**SCIENTIFIC_CHANGE_REQUIRED**. P2A no aprobado, P2B no implementado y P3 no
iniciado. Fuente `63e2863921a1d7c2434899247876aa6bb03990fb`, ejecución única
`20260917T164812-P2-07051b7effd6` por dev_orchestrator, con P0/P1 aceptadas.
No se usaron reparaciones: 0/3; la condición científica exige STOP inmediato,
no tres modificaciones arbitrarias para intentar aprobar.

T01 PASS, T02 FAIL, T03 PASS, T04 PASS, T05 FAIL, T06 PASS, T07 PASS.
T08 parcial (solo reposo/área constante N100/N200 cerrados), T09–T12 no ejecutados.
12 subcasos registrados:10PASS/2FAIL. T08 N400 estaba en curso al detener;
no se conserva ni acredita como resultado completo. Solver en subcasos registrados:
96,768s; comando de campaña hasta interrupción:113,766s.

T02 Sod: contacto exacto0,6854905240097903, gradiente máximo contractual Y
ubicado0,6925, error0,00700947599=2,80379dx; límite2dx=0,005. Referencia,
ventana e índice comprobados offline por revisor; sin defecto concreto que
permita corregir este incumplimiento dentro de P1. No se cambiaron método,
N, métrica ni umbral. L1ρ0,00723442/L1p0,00565660/L1u0,00991463; el resto
de gates Sod aprobó. Cambiar el contrato requiere nueva decisión científica.

T03: velocidad340,942089m/s, error relativo2,79958e−5, amplitud0,838695 de
referencia. T04: reflexión+0,842468, pico1,000000L/a. T05: parada a17 pasos,
No consistent open-boundary branch; velocidades de rama a redondeo−2,273737e−13
vs+4,547474e−13. Defecto de robustez pendiente, no imposibilidad física.
T06 E1Y0,058714814 y E1ρ/(2ρ0)0,027241539. Peor ledger registrado
1,74253e−15 frente1e−10. HLLE=0 en subcasos registrados; no atribuir T12 PASS.

Revisión independiente read-only `/root/p2_review`: BLOCKED,
scientific_change_required=true. Hallazgos pendientes además de T05:
contadores HLLC incluyen flujos característicos directos/duplicación de cara
periódica, registros fallback de frontera no guardan ghost real; BC no reflectiva
con base explícita mezcla entropía/composición predeterminadas. No se corrigió
ni implementó más código tras STOP. Las cifras HLLC originales no se certifican.

La campaña hijo fue detenida explícitamente al confirmarse T02. El runner
registró gate técnico FAILED_INFRASTRUCTURE por command_failed:p2a_campaign;
se conserva evidence.json intacto, no se disfraza como corrida completa.
La decisión científica y revisión están en artifacts/p2-scientific-decision.json
junto a evidencia técnica original en `results/p2-gas1d-20260917/`.

11 unit tests PASS en ejecución formal (EOS, HLLC/HLLE, especie, geometría,
fronteras, CFL, equilibrio variable corto, ledger y referencia Sod). No equivalen
a T01–T12 completos. P0: hashes intactos y7regresiones exactas offline PASS;
ninguna nueva integración0D. Contrato P1 congelado intacto. OpenSpec estricto
aprobado; autorrevisión de alcance separada de revisión independiente.
Figuras Sod/pulso SVG y PNG derivadas de arrays conservados; Sod inspeccionada
visualmente. No inspección UI/Windows, paquete ni aceptación de P2 atribuida.
Commit de evidencia registra este cierre. Sin publicar ni archivar; redme.txt ajeno.

## Continuación P1-R2 — 18/09/2026
El observable hidrodinámico T02 aprobó y se adoptó 1D_CONTRACT_V1_R2;
el fallo histórico anterior no se reescribe. Ver tareas de p1-r2-contacto.
Retenidos fixes de contabilidad y estado exterior no reflectivo. T05 no aprueba:
ensayo provisional fallido con excepción retirada de velocidadcero; sus dos
ramas son incompatibles también a70dígitos. SCIENTIFIC_CHANGE_REQUIRED para BC,
sin reanudar T01–T12/P2A ni iniciar P2B/P3. Una ronda de reparación/ensayo de3;
las restantes no autorizan modificar física para superar el gate.

## Continuación P1-R3 — 18/09/2026
R3 aprobado tras revisión conceptual previa; BC pressure-release y T05 PASS.
Campaña final `20260918T110612-P2_R3-9d1c983a7e65`, fuente b353e90:
52/52 casos individuales PASS, T01–T10/T12 PASS, **T11 FAIL**.
Sensibilidad amplitud pulso CFL0,6 frente0,2:0,0833638270618394 >0,08.
**P2A BLOCKED** confirmado por revisión independiente; no bug de medición
identificado. No confundir casos individuales con comparaciones agregadas.
25 unit tests PASS; peor ledger6,53449e-15, HLLC36252480/HLLE6;
baselineP0, P1v1/R2, T02/T06 conservados. Reparaciones acumuladas3/3:
contadores/exterior R2; partición temporal R3; identidad aritmética de masa HLLC.
No clipping, nuevos limiters, cambios de método/ondas, CFL o tolerancias.
Primera campaña R3 preservada:51/52 casos PASS y la misma sensibilidad incumplida.
Tablas, deltas y recibos en `../p1-r3-fronteras/tasks.md` y
`results/p1-r3-fronteras-20260918/`. P2B no iniciado; decisión sobre T11 y
human gate de P2 pendientes. Sin P3, aceptación humana atribuida, archivo o push.
Los registros anteriores conservan su estado histórico.

## Continuación P1-R4 — 18/09/2026
**P2A_PASS_FIRST_ORDER_VERIFIED** bajo1D_CONTRACT_V1_R4, revisado de forma
independiente. El estudio congelado demuestra reducción de sensibilidad en
N400/800/1600 y conserva límites de exactitud T03; se retira explícitamente la
garantía8% aN800. El FAIL históricoR3 no se sobrescribe ni desaparece por cálculo.
Run20260918T115319-P2A_R4_VERIFY-7474ef29fc6d: seis integraciones T11 nuevas,
numéricamente idénticas;46 casos reutilizados por hashes,52 reevaluados.
T01–T12 PASS bajoR4; fuente productiva/solver/P0/contratos anteriores intactos.
Ocho pruebas pertinentes PASS, revisión independiente y OpenSpec estricto.
Ver `../p1-r4-cfl/tasks.md` y `results/p1-r4-cfl-20260918/` para tablas y recibos.
Presupuesto de reparaciones3/3 anterior no reiniciado; R4 fue revisión científica
con implementación congelada. P2B no iniciado, human gate deP2 pendiente;
P2 no se declara completo, no P3/publicación/archivo. redme.txt ajeno preservado.

## P2B — orden actual 18/09/2026
- [x] Registrar P1_R4_HUMAN_ACCEPTED y P2A_HUMAN_ACCEPTED por la usuaria, sin aceptación global P2.
- [x] Congelar baseline first-order y verificar presupuesto de reparaciones por fase.
- [x] Implementar MUSCL/minmod y SSP-RK2 sin alterar primer orden ni física.
- [x] Pruebas de reconstrucción, stages, rechazo completo, BC y contadores.
- [ ] Campaña P2B T01–T12 mediante dev_orchestrator con STOP ante bloqueo científico.
- [x] Comparación P2A/P2B y regresión P0/first-order según alcance ejecutado.
- [x] Revisión independiente, OpenSpec estricto, documentación y commits locales.

Registro inicial: P3 prohibido. Presupuesto P2B0/3 al autorizar; el resultado
inferior registra1/3 usado. No se reinicia el presupuesto anterior deP2A.
Se conserva eliminación ajena redme.txt y toda evidencia previa. Sin push/archivo.

## P2B — resultado 18/09/2026
**FAILED_INFRASTRUCTURE**. No P2B/P2 PASS, no P2_HUMAN_ACCEPTED ni P3.
La implementación está registrada, pero la verificación completa queda pendiente.
La usuaria aceptó específicamente P1-R4 y P2A en la orden a7a088e7; recibos
`docs/gasdynamic/p1_r4_human_acceptance.json` y `p2a_human_acceptance.json`.
No se reescriben estados históricos de las secciones anteriores.

### Arquitectura y alcance del diff
`motorsim/gas1d/methods.py` despacha FIRST_ORDER al solver original sin cambios
y MUSCL_SSPRK2 a `second_order.py`. Reconstruye rho/u/p/Y en centroides reales
con minmod de gradientes izquierdo/derecho; periodicidad con desplazamiento L,
ghosts de BC existentes reflejados geométricamente en extremos. Si una cara es
inadmisible, anula todas las pendientes de esa celda según P1, con contador.
No clipping ni nuevos limiters. Una sola evaluación por cara periódica compartida.
SSP-RK2: C1=Cn+dt L(Cn); C2=C1+dt L(C1); Cnuevo=(Cn+C2)/2.
EOS comprueba C1, C2 y Cnuevo; rechazo completo y dt/2, máximo12 reducciones.
BC/source se evalúan en ambas etapas; ledger usa pesos1/2,1/2; registra por etapa
y paso, contadores de trabajo rechazado incluidos. Modos no expuestos en UI.
No cambios en EOS, HLLC/HLLE, source, malla, BC R3, detector R2, baseline ni JSON.
Adaptador `dev_orchestrator/p2b_campaign.py`, fase P2B y entrada declarativa
permiten presupuesto nuevo3 según política existente, sin cambiar configuración.
El orden prioriza positividad y detiene al primer fallo no resuelto.

### Campaña y reparaciones
Fuentes:012caad aceptación/congelación; cd86d7e implementación;
4620200 reparación1 y conservación de intento1. Sin publicación.
Intento1 `20260918T121546-P2B-012ba5672a64`: falso FAIL del comprobador CFL,
T12_contact completo pero dt/unit redondeó0,4000000000000001.
Reparación1/3: registrar dt y límites originales de cada etapa; comprobar la
misma desigualdad exacta dt<=CFL*unit. Sin epsilon, cambioCFL o nueva aritmética
de integración. Prueba acepta ese redondeo y rechaza nextafter(dt,+infinito).
Revisión independiente aprobó la reparación. Intento1 se conserva intacto.

Intento2 `20260918T121838-P2B-abf510d53a0f`: ocho casos PASS, uno incompleto.
T04 agotó120,062s tras2805 pasos, t=0,002684548582421251s frente
objetivo0,00337310127194846s. No se certifica coeficiente de reflexión parcial.
Campaña383,625s (incluye medición/escritura), detenida antes del resto.
El runner nativo registra BLOCKED por P2B=false y hook de revisión no conectado;
el resumen numérico registra FAILED_INFRASTRUCTURE por wall_timeout. Se conservan
ambos; el reviewer real está documentado aparte, nunca sustituido por el stub.
No se amplió120s/subcaso ni se repitió tras el timeout. T10_800 conserva únicamente
la excepción240s ya documentada, pero no llegó a ejecutarse. Presupuesto P2B1/3.

### Matriz contractual
| Gate | MUSCL_SSPRK2 actual | FIRST_ORDER control R4 |
| --- | --- | --- |
| T01 uniforme | PASS (reposo y movimiento) | PASS |
| T02 Sod | PASS | PASS |
| T03 acústica | PASS | PASS |
| T04 reflexión cerrada | Incompleto: timeout, no resultado final | PASS |
| T05 reflexión abierta R3 | No ejecutado; ideal_open_pressure_release previsto | PASS |
| T06 especie/contacto | No ejecutado como gate T06 | PASS |
| T07 conservación | No ejecutado como suite T07 | PASS |
| T08 área variable/tobera | No ejecutado | PASS |
| T09 backflow | No ejecutado | PASS |
| T10 refinamiento | No ejecutado; orden>=1,5 NO acreditado | PASS |
| T11 CFL R4 | No ejecutado en P2B | PASS |
| T12 positividad | Parcial4/10: expansión, contacto, Y=0, Y=1 PASS | PASS |

FIRST_ORDER: reevaluación agregada offline de52 registros congelados y estudioR4
preexistente, con inventarios/hash verificados. No52 integraciones nuevas ni nueva
campaña0D. La prueba de despacho demuestra identidad de resultado FO salvo tiempo.
T12_contact no se presenta como ejecución formal T06; faltan seis frustums T12.

### Casos ejecutados: conservación y coste
| Caso | Pasos | Tiempo s | HLLC | HLLE | Peor ledger de paso | Peor ledger de etapa |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| T01_rest | 251 | 1.063 | 50200 | 0 | 0 | 0 |
| T01_moving | 301 | 1.297 | 60200 | 0 | 0 | 0 |
| T12_expansion | 283 | 4.796 | 232971 | 10 | 1.77636e-15 | 1.16805e-16 |
| T12_contact | 3125 | 66.578 | 2600000 | 0 | 8.71265e-15 | 1.57377e-16 |
| T12_pure0 | 3308 | 69.219 | 2892800 | 0 | 8.83712e-15 | 1.57377e-16 |
| T12_pure1 | 3308 | 69.172 | 2892800 | 0 | 8.83712e-15 | 1.57377e-16 |
| T02_sod | 547 | 11.141 | 526914 | 0 | 2.50216e-16 | 9.88014e-17 |
| T03 | 901 | 37.063 | 1439798 | 0 | 2.39194e-16 | 1.55744e-16 |
| T04 | 2805 | 120.062 | 4648800 | 0 | 2.36012e-16 | 1.5919e-16 |

T04 es parcial; su tiempo no compara soluciones al mismo instante.
Todos los estados aceptados/etapas registrados cumplen rho,p,T>0 y0<=Y<=1.
Cero downgrades observados; los10HLLE son de expansión, motivo inadmissible_star
(vs6 en FO). Rechazos contabilizados exclusivamente por CFL de etapa (1918). En los nueve
registros, incluidoT04parcial:15344483HLLC y10HLLE; no comparar este total parcial
con el total de52casosFO como si fueran campañas equivalentes.
No se midió memoria pico; no se afirma memoria/coste completo de P2B.

### Sod y acústica: comparación al mismo tiempo final
| Métrica | FIRST_ORDER | MUSCL_SSPRK2 |
| --- | ---: | ---: |
| Sod rho_L1 | 0.00723442066 | 0.00224489335 |
| Sod u_L1 | 0.00991462899 | 0.00329297951 |
| Sod p_L1 | 0.00565659557 | 0.00149620259 |
| Sod shock_position_error | 0.00206885359 | 0.00206885359 |
| Sod contact_position_error | 0.00299052401 | 0.00200947599 |
| T03 speed | 340.942089 | 340.945549 |
| T03 speed_relative_error | 2.7995799e-05 | 3.81443152e-05 |
| T03 amplitude | 8.38422039 | 9.63078348 |
| T03 pressure_L1 | 0.0120447663 | 0.00121933551 |
| T03 pressure_L2 | 0.0325611719 | 0.00464874455 |
| T03 disipación 1−A/Aexacta | 0.161305028 | 0.0366081392 |
| T03 error de desplazamiento de centroide, m | 1.25981096e-05 | 1.71649419e-05 |
| T03 tiempo s | 12.032 | 37.063 |

La fase se representa por desplazamiento de centroide al tiempo final, no ángulo
de un armónico. MUSCL reduce difusión pero no mejora universalmente velocidad/fase;
ambas velocidades cumplen1%. R2 localiza el contacto Sod sin usarY ni exacta;
error0,803790396Δx, shock0,827541438Δx, ambos<=2Δx. DiagnósticosY:
Agradiente0,690; Bcruce0,688744681463; Ccentroide0,687914924708;
Dhidrodinámico0,6875, exacto0,685490524010. Son diagnósticos, no cambio de gate.

### Refinamiento disponible
Solo control histórico FO. MUSCL no tiene una serie T10 ejecutada y no se infiere
orden desde Sod/contactos. Se conservan pares contractuales200/400 y400/800>=1,5.
| N | dx | FO rho L1 | FO rho L2 | FO rhoY L1 | FO rhoY L2 | Orden rho L1 desde N anterior | MUSCL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 100 | 0.01 | 0.0107372934 | 0.0119258212 | 0.027045011 | 0.0300422554 | — | No ejecutado |
| 200 | 0.005 | 0.00561778718 | 0.00623977322 | 0.0141788741 | 0.0157516124 | 0.934556 | No ejecutado |
| 400 | 0.0025 | 0.00287404547 | 0.00319226086 | 0.00726325816 | 0.00806932308 | 0.966919 | No ejecutado |
| 800 | 0.00125 | 0.00145368239 | 0.00161463514 | 0.00367642097 | 0.00408454332 | 0.983371 | No ejecutado |

No nuevas conclusiones sobre T05, tobera, backflow o sensibilidadCFL en P2B.
El refinamiento R4 de MUSCL sigue pendiente; el8% histórico no se restaura.

### Regresión, revisión y comandos
49 pruebas pertinentes PASS (nueve P2B más FO, fixes, R2/R3/R4), log conservado.
Siete regresiones históricasP0 exactas offline PASS; hashes de producción,
baseline0D y31 archivos congelados coinciden. UI/JSON y solverFO sin cambios.
Revisión independiente real por `/root/p2b_review`: implementación/fix aprobados
en alcance revisado; cierre bloqueado correcto, no aprobación global P2B.
Autorrevisión: alcance Git, hash/inventarios, documentación y pendientes; distinta
de la revisión independiente. OpenSpec estricto PASS.

Ejecución formal desde raíz (no repetir sin resolver el bloqueo):
```powershell
.\.venv\Scripts\python.exe -m dev_orchestrator.runners.run_phase P2B --dependency P0=docs/gasdynamic/p0_accepted_dependency.json --dependency P1_R4_CFL_REVIEW=docs/gasdynamic/p1_r4_accepted_dependency.json --dependency P2A_R4_VERIFY=docs/gasdynamic/p2a_accepted_dependency.json
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_p2b.py -v
openspec validate p2-nucleo-gas1d --strict --no-interactive
```
Suite49: patrones test_p2b.py, test_gas1d.py, test_p2_fixes.py,
test_p1_r2.py, test_p1_r3.py, test_p1_r4.py y test_p1_r4_gate.py mediante unittest.
Evidencia en `results/p2b-gas1d-20260918/`: intentos originales, decision.json,
independent-review.json, regression.json y verification-tests.log.
Pendiente: resolver límite operativo sin cambiar ciencia; terminar T04–T11 y
frustumsT12; acreditar orden, CFLR4 y gate integral; después aceptación humanaP2.
No P3, empaquetado, publicación ni archivo. Eliminación ajena redme.txt preservada.
