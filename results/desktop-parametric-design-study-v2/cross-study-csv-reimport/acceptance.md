# Reimportación de CSV de comparación entre estudios

Fecha: 2026-11-04. La fuente de demostración y la interacción gráfica son **SYNTHETIC**; esta verificación no ejecuta el solver ni constituye evidencia física.

## Entrega

- El formato exportado `DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1` se reconoce antes del importador CSV genérico y se valida con encabezados y orden exactos.
- La vista de solo lectura conserva texto, precisión decimal y decisiones del CSV. Muestra parejas exactas y puntos sin pareja, con estado de convergencia visible. No agrega curvas ni interpreta un punto transitorio como prestación.
- Manifiestos repetidos deben conservar una misma ruta/hash y toda fila debe conservar el baseline y el estado científico coherentes. Un artifact marcado como verificado se revalida por hash e identidad; cambios demostrables se rechazan. Fuentes no verificadas o no disponibles siguen identificadas sin promover su estado.
- El resumen tabular usa columnas compactas sin scroll horizontal en la ventana verificada. Al seleccionar una fila, el panel de detalle conserva el registro CSV íntegro, incluidos IDs, hashes y rutas.
- Los controles de análisis normal, curvas y exportación se retiran para este tipo de snapshot. Los valores vacíos siguen vacíos y la clasificación científica `NOT_CLAIMED` se presenta como no declarada.

## Verificación

- `python -m pytest -q tests/test_desktop_comparison_snapshot.py tests/test_parametric_study_snapshot.py tests/test_parametric_factorial_snapshot.py tests/test_desktop_design_study.py` — **45 passed, 0 failed**; summary reproducible en `tests-final/parametric-cross-study-csv-reimport-final.summary.json`.
- `python results/desktop-parametric-design-study-v2/cross-study-csv-reimport/verify_native_cross_study_reimport.py` — aplicación Desktop PySide6 nativa visible a 1440×837, importando el CSV sintético existente por el flujo normal de carga. Confirma 2 filas, clasificación no convergida, motivo de no pareo, ausencia de curvas, solo lectura, `NOT_CLAIMED` y ausencia de scroll horizontal.
- No se usó UI Automation COM: la apertura, selección, renderizado y captura ocurrieron en la ventana Qt nativa. La causa histórica de COM —teardown de un provider UIA obsoleto en el harness tras destruir la ventana Qt nativa— está descrita en `results/desktop-parametric-design-study-v2/cross-study-comparison/acceptance.md`; no se observó como defecto de producto.

## Evidencia

- Fuente sintética ya aceptada: `../cross-study-csv-export/synthetic-comparison.csv`; SHA-256 `819af0ddfaf839cb221e790526f9b6be9282bca50fa31e539a3b14f13028905a`.
- Captura de la ventana nativa: `native-cross-study-csv-snapshot.png`; SHA-256 `3f9e0da02ee6c5e9bb3614aac2f45706015482863cd7ae2d675baf4baa6fa41c`.
- Recibo: `native-window-receipt.json`.

Limitación: el snapshot refleja las decisiones y la calificación guardadas al exportar. Una importación no vuelve a ejecutar la comparación ni modifica sus archivos originales.
