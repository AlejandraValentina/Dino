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
