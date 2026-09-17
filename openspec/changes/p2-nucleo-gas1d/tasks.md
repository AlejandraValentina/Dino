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
