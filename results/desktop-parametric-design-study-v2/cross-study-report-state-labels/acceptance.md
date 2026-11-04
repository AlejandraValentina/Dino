# Etiquetas de estado en informes de comparación

## Cambio

Las tablas de exclusión de puntos de respuesta ahora presentan la clasificación y periodicidad con las etiquetas de `state_label` usadas por el resto de Desktop. Así, un extremo no periódico aparece como **Límite de ciclos · no convergida / Ciclos insuficientes**, no como dos enums internos.

Los códigos fuente siguen intactos en el JSON completo adjunto al HTML. El cambio afecta únicamente la presentación; no cambia qué puntos califican para gráficos o contrastes.

## Verificación

- Pruebas de `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`: **46 passed**.
- La prueba exige las etiquetas visibles traducidas, comprueba que el enum concatenado ya no aparece en la tabla y comprueba que `MAX_CYCLES_NONCONVERGED` e `INSUFFICIENT_CYCLES` siguen en el JSON original.
- Desktop nativo exportó el informe sintético desde Resultados/Comparar. Chrome lo mostró a 1360 px; se conserva además la captura de la ventana. SHA-256 y dimensiones están en `acceptance-receipt.json`.

**Origen:** fixture sintético, expresamente identificado en el informe. No hubo ejecución del solver ni campaña científica.

## Pendiente visible

Los códigos de criterio de pareo y algunos nombres de campos operativos continúan apareciendo como identificadores en otras tablas del mismo informe. La tarea READY `DESKTOP-PARAMETRIC-REPORT-PAIRING-CONTEXT-LABELS-V1` los cubre por separado; se preservarán los IDs originales en el JSON.
