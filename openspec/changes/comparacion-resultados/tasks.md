# Tareas de comparacion-resultados

- [x] 1. Comprobar Git, leer contratos y registrar alcance autorizado preservando entrega 5.
- [x] 2. Implementar selección/compatibilidad y diferencias geométricas/descriptivas con lector existente.
- [x] 3. Integrar tabla y superposición A/B por fase con ejes comunes, sin cálculos nuevos.
- [x] 4. Implementar CSV fiel/exclusivo y tratamiento de errores.
- [x] 5. Probar identidades/inversión/porcentajes, entradas, fase/P-V, incompatibilidad, errores y ausencia de cálculos.
- [x] 6. Comprobar Windows/150 % con resultados existentes y capturas/CSV; revisión puntual y OpenSpec.
- [x] 7. Registrar evidencia/pendientes en README/hoja y commit propio sin publicar ni archivar.

Entrega 6 En curso. Barridos e importación de mediciones pendientes, fuera de este
tramo; no se especifican ni implementan. Entrega 5 y aceptación manual pendiente
conservadas. No se repiten simulaciones ni verificaciones históricas.

## Evidencia — 15/09/2026

Inicio main limpio en 5dda9860d4dcb322c839c8cc1ae5f617f6a21387, alineado con referencia
origin/main disponible. Se conserva ese commit, la entrega 5 y todos sus resultados.
Sin fetch/push, credenciales, globales, nuevas dependencias, núcleo ni JSON v5.
Único cambio nuevo: comparacion-resultados. Barridos/importación no especificados.

Implementación: comparison.py interpreta entradas mediante validated_model y
compara campos explícitos, sin igualdad literal de archivos. La vista usa solo
load_result para seleccionar A/B. Nombres, rutas, origen y dirty no se tratan como
condiciones; m/U/F derivados pueden variar. Se canonizan funciones/filas de
lumbreras y se separan descripciones. Tabla desde resumen; curvas desde muestras
del último ciclo, fase documentada y P-V temporal. No se usa el proyecto activo.
Exportación con csv.writer a carpeta exclusiva, valores sin redondear y limpieza
de archivos propios ante error; no declara éxito parcial ni sobrescribe destinos.

### Pruebas automatizadas del tramo

`.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_comparison.py -q`:
**10/10 aprobadas en 2,066 s**, estado final. Fixtures declarados para aritmética/Qt,
no evidencia física; resultados reales existentes para lector y compatibilidad.
Esperados definidos independientemente de compare_results. Comprueban A/A=0,
inversión absoluta y porcentaje respecto a nueva base, A=0 sin denominador artificial,
Y absoluto, resumen distinto de máximos dibujados, compresión, nombres/números
equivalentes/reordenamiento por función, múltiples cambios de ficha/cárter/falda/
lumbrera/tramo, cada condición/metadato ausente, estados no convergidos/balances,
fase por ciclos distintos/P-V temporal, CSV/unidades/identidades/escape, rechazo
de destino existente/fallo de segunda escritura y conservación de datos/fuentes.
Qt comprueba selección ilegible sin reemplazo, incompatibilidad que retira datos
cuantitativos y exportación sin iniciar QProcess ni cambiar proyecto/dirty.
No se ejecutó la suite histórica que inicia ensayos; no hubo simulaciones nuevas.

Una revisión independiente puntual de solo lectura no encontró defectos
reproducibles; ejecutó solo estos 10 tests (1,443 s). Autorrevisión del principal
de diff, exportaciones y capturas. OpenSpec estricto aprobado, sin init/update
ni integración automática. No otra revisión general.

### Resultados existentes utilizados, no ejecuciones nuevas

A/base: `results/simulacion-2t/editor-20260915/A/manifest.json`, compresión 8:1,
run_id `a7f98f7af82d471ebffe53066c24dae8`, último ciclo 10.
B/modificada: `results/simulacion-2t/editor-20260915/B/manifest.json`, compresión 8,2:1,
run_id `85ff236a668f4fd39dcc8c56944641d1`, último ciclo 9.
Ambos perfil **B**, banda 100 Pa y 3000 rpm; convergidos/balances validados.
Única diferencia geométrica detectada: compresión. Sin diferencias descriptivas.
La ejecución histórica C (perfil C) se leyó únicamente para probar incompatibilidad
de perfil, no se usó como geometría B ni se volvió a calcular.

| Magnitud | A | B | B−A | Relativa % |
| --- | ---: | ---: | ---: | ---: |
| W_C J/ciclo | 16,49050751206088 | 16,63155294204956 | 0,14104542998867942 | 0,8553128512601639 |
| W_K J/ciclo | -3,3651306484080394 | -3,3652474266840153 | -0,00011677827597589285 | -0,0034702449377749358 |
| pmax Pa abs. | 1331530,846070603 | 1366927,2751548453 | 35396,42908424232 | 2,6583258802226397 |
| Y_I | 0,9855942761818735 | 0,9858254226456079 | 0,00023114646373445513 | No aplicable |
| Y_K | 0,9771350157648919 | 0,9775046102019959 | 0,00036959443710393725 | No aplicable |
| Y_C | 0,5621858698264297 | 0,5627356966320124 | 0,0005498268055826872 | No aplicable |
| Y_E | 0,38108950299160227 | 0,3819618593595342 | 0,0008723563679319257 | No aplicable |

A comienza su última vuelta en 3420°, B en 3060°: se restan 3240°/2880°
respectivamente, ambos 180–540°, sin mover picos. 721 muestras originales por
ejecución, con volumen temporal sin ordenar. Valores no interpretados como
mejora de motor ni potencia al eje; limitación 0D/energía prescrita conservada.

### Windows visible, captura y exportación

```powershell
.\.venv\Scripts\python.exe tests/verify_comparison_windows.py --output results/simulacion-2t/comparacion-20260915
.\.venv\Scripts\python.exe tests/verify_comparison_windows.py --output results/simulacion-2t/comparacion-20260915 --no-export --suffix=-final
```

Escritorio Default accesible. Automatización de ventanas reales al 150 % efectivo
(DPR 1,5, base 125 % y factor Qt 1,2 solo del proceso), sin aceptación manual.
Botón desde Simulación 2T, selección de A/B vía diálogo, compatibilidad, CSV,
navegación de pestañas, foco Tab y ancho compacto comprobados. Guardas sobre
QProcess.start confirmaron cero procesos de cálculo. Hashes de JSON fuente A/B/C
iguales antes/después, proyecto abierto y dirty conservados.

CSV verificados en `results/simulacion-2t/comparacion-20260915/resumen.csv`
(7 filas de magnitudes) y `curvas.csv` (1442 muestras). Se recuperaron con
csv.DictReader para comprobar valores numéricos completos, unidades, run_id,
fase y orden del volumen contra los resultados guardados. Solo archivos locales
de evidencia, ignorados por Git; no datos personales ni sobrescrituras.

Inspección visual: se corrigió la necesidad de desplazar internamente la tabla
para leer Y_E; resumen/entradas separados en pestañas y tabla ajustada a sus siete
filas. En compacto se alineó arriba para evitar un hueco causado por la altura
de gráficos apilados. Nuevas capturas reabriendo resultados, sin exportar de nuevo
ni calcular. Pruebas afectadas repetidas tras esos ajustes; no campañas físicas.
Capturas preliminares conservadas en `results/simulacion-2t/capturas-comparacion-previas/`.

Capturas reales finales en `docs/images/`, inspeccionadas:
- `motorsim-comparacion-resumen-150-final.png`: A/B, procedencia, condiciones y siete magnitudes.
- `motorsim-comparacion-entradas-150-final.png`: única diferencia de compresión y separación descriptiva.
- `motorsim-comparacion-curvas-150-final.png` y `motorsim-comparacion-curvas-inferior-150-final.png`: superposición, ejes comunes, leyendas, unidades y aviso.
- `motorsim-comparacion-compacta-150-final.png`: disposición vertical y foco visible.

Entrega 6 **En curso: comparación y CSV implementados**. Barridos e importación
de mediciones pendientes y no autorizados en este tramo. No quedan comprobaciones
técnicas pendientes del tramo; aceptación manual no atribuida. Entrega 5 intacta.
Commit propio y publicación a cargo de la usuaria; sin archivar ni iniciar entrega 7.
