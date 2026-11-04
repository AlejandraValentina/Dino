# CSV de comparaciones entre estudios paramétricos

Fecha: 2026-11-04. Evidencia de interfaz: **SYNTHETIC**; no se ejecutó el solver.

## Implementación

- Agrega `Exportar comparación CSV…` para la comparación cargada actualmente.
- Exporta una fila por pareja exacta y por punto sin pareja, con RPM, diseño/factores exactos, estados, motivo de no pareo, fuente/run IDs, hashes de ambos manifiestos, identidades/hash del resultado, ruta del artifact y calificación científica.
- Potencia, torque, BMEP y deltas quedan vacíos si los puntos no son periódicos o la métrica no está definida. No hay interpolación ni recálculo.
- Antes de exportar vuelve a verificar el hash e identidad del manifiesto y, para cada fuente marcada verificada, el hash de `result.json`, `run.json`, `run_id` e identidad. Cambios posteriores a la comparación impiden la exportación.
- El control permanece deshabilitado hasta cargar una comparación; se deshabilita al invalidar/cambiar las referencias del proyecto o si falla la verificación. El CSV se crea en modo exclusivo y no reemplaza archivos.

## Pruebas

- `python -m pytest -q tests/test_design_study.py tests/test_desktop_design_study.py tests/test_desktop_technical_report.py` — **47 passed** en 203.34 s. Summary: `tests-verified/parametric-cross-study-csv-final.summary.json`.
- La regresión nueva confirma precisión completa, filas `EXACT_PAIR` y `UNPAIRED`, estados no convergidos, métricas ausentes, IDs/hashes, validación positiva de fuente, rechazo de artifact/manifiesto alterados, rechazo de sobreescritura e invalidación del control.
- Aplicación Desktop fuente abierta en una ventana Qt nativa de 1440×837. Se ejecutó la acción CSV sobre dos estudios/manifiestos sintéticos registrados en un proyecto; la captura muestra la tabla y el mensaje del archivo generado. Script repetible: `verify_native_cross_study_csv.py`.

## Evidencia

- CSV sintético: `synthetic-comparison.csv`; SHA-256 `819af0ddfaf839cb221e790526f9b6be9282bca50fa31e539a3b14f13028905a`.
- Captura: `native-cross-study-csv.png`; SHA-256 `688c91f5b9065ea268ced07af7d1c2f99426ac7f8fb434511db9bfc6c7bdbcfc`.
- Recibo estructurado: `native-window-receipt.json`.

El CSV sintético ilustra una fila no convergida pareada por condiciones exactas y un punto sin pareja por RPM, ambos sin métricas. La comparación visual no es evidencia de una ejecución física, periodicidad experimental ni predicción validada.
