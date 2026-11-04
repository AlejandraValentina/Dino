# Inspección de puntos en comparación entre estudios

Fecha: 2026-11-04. Las capturas y los manifiestos de la prueba gráfica son **SYNTHETIC**. No se ejecutó el solver y no constituyen validación experimental ni predicción validada.

## Entrega

- Los puntos del gráfico exacto PERIODO 1 conservan la identidad del punto y las filas de comparación que los generaron.
- Un clic sobre el marcador selecciona su fila pareada y muestra los datos del diseño, RPM, clasificación, periodicidad, ciclos, métrica seleccionada, IDs de corrida, ruta y hashes de manifiesto, motor, corrida y artifacts.
- Si el mismo punto aparece en más de un par entre estudios, el panel enumera todas las filas y los endpoints correspondientes sin duplicar el marcador.
- Se indica si la fuente fue verificada durante la carga de la comparación. El fixture visual se identifica como no verificado; sus hashes de presentación no se promueven a evidencia.
- Puntos no periódicos, métricas indefinidas y filas sin pareja mantienen las exclusiones y el contenido de tabla existentes. No se interpolan ni recalculan valores.

## Verificación

- El test de interacción emite la señal del punto gráfico y confirma selección de fila, asociación a dos pares, identidad de fuente y hashes.
- `python -m pytest -q tests/test_desktop_design_study.py tests/test_desktop_comparison_snapshot.py tests/test_parametric_study_snapshot.py tests/test_parametric_factorial_snapshot.py` — **46 passed, 0 failed**; summary en `tests-final/point-inspection-final.summary.json`.
- `verify_native_point_selection.py` abre Dino Desktop en ventana Qt nativa a 1440×837 y usa un clic `QTest` sobre un marcador visible. El recibo confirma que la fila exacta se seleccionó, sus hashes/IDs se mostraron, la fuente sintética permaneció no verificada y el punto sin pareja siguió en la tabla.
- Capturas separadas documentan el gráfico antes del clic y el panel de procedencia después del clic.
- No se utilizó la automatización COM/UIA para esta prueba; la entrada y la presentación fueron comprobadas directamente en Qt. El error histórico de COM sigue atribuido al teardown de un provider UIA obsoleto del harness después de destruir la ventana Qt nativa; no se reproduce en la ruta de producto.

## Evidencia

- Gráfico y filas: `native-response-plot-synthetic.png`.
- Selección y detalle: `native-marker-selection-synthetic.png`.
- Recibo: `native-marker-selection-receipt.json`.
- Los manifiestos sintéticos usados para habilitar la sección dentro del proyecto se generan al ejecutar el script; contienen sólo IDs, schema y clasificación sintética.

La selección expone datos del snapshot de comparación ya verificado; no revalida ni cambia sus artifacts y no altera la calificación científica guardada.
