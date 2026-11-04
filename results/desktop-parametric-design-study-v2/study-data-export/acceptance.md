# Exportación de puntos de estudios paramétricos desde Desktop

Fecha: 2026-11-04. Tipo de fixture de interfaz: **SYNTHETIC**. No se ejecutó el solver.

## Entrega

- Agrega exportación CSV de los puntos seleccionados en la matriz de un estudio abierto desde el proyecto.
- Conserva números sin redondeo, valores de factores JSON, estados, IDs de corrida, identidades, hashes y ruta del manifiesto.
- Antes de escribir vuelve a leer y verificar el SHA-256 del manifiesto contra la referencia guardada en el proyecto. Crea el CSV en modo exclusivo para no sobrescribir archivos.
- Los valores de potencia, torque y BMEP sólo se exportan si la corrida importada corresponde exactamente a la fuente del manifiesto, su `result.json` concuerda con los hashes de `run.json`/manifiesto y la métrica está definida para un punto `PERIOD_1`. En las demás filas quedan vacíos.
- Corregida la presentación de estados: la tabla usa la clasificación/periodicidad ya guardada en el manifiesto mientras el artifact no esté cargado. Las métricas continúan vacías hasta su importación verificada.

## Verificación

- `python -m pytest -q tests/test_design_study.py tests/test_desktop_design_study.py tests/test_desktop_technical_report.py` — **46 passed** (`tests-final/parametric-study-csv-final.summary.json`). Incluye comprobación de valores de precisión completa, factores, estados convergidos/no convergidos, validación de fuente, rechazo de manifiesto alterado y rechazo de sobrescritura.
- Aplicación Desktop fuente abierta como ventana Qt nativa en Windows; estudio reabierto desde referencia del proyecto; dos filas seleccionadas y exportadas por la acción real de interfaz. La captura `native-window-study-csv-export.png` muestra la matriz, estados y control de exportación.
- Recorrido gráfico: `verify_native_desktop_csv.py`. CSV emitido: `synthetic-native-selected.csv`.

## Artefactos

- SHA-256 manifiesto sintético: `aeeed060e7786e7eec5aa41439a99164583a05ecccf77e6705e65d280082cb79`.
- SHA-256 CSV exportado: `3a2e71ee547e31b94257afbb1a6d98e5aef1b49dab193836b9d03ef766834f67`.
- SHA-256 captura: `b7f5709b7af3f1d2d40450599b66546c46e5ac0eeb0a7347ed518bde385efdea`.

El fixture contiene una fila `PERIOD_1` sintética y otra `INSUFFICIENT_CYCLES`. La aplicación conserva ambas etiquetas; la fila no convergida exporta las métricas vacías. **Esto verifica integración y formato, no desempeño físico, periodicidad validada ni predicción del motor.**
