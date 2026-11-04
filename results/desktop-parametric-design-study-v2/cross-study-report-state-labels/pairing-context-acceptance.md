# Etiquetas legibles de pareo y contexto operativo

Los informes comparativos muestran ahora:

- `EXACT_RPM_AND_OPERATING_CONTEXT` como **RPM exacta y contexto operativo coincidente**.
- `total_finite_volume_cells` como **cantidad de celdas de volumen finito** en una explicación de incompatibilidad.

Son cambios de presentación solamente. La comparación continúa exigiendo los mismos campos y coincidencia exacta; el JSON original del informe conserva tanto `pairing` como el texto y los IDs crudos de la razón.

## Validación

- `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`: **46 passed**.
- Desktop nativo abrió el informe comparativo y lo exportó desde su control normal. Chrome renderizó el HTML a **1360 × 3000** para incluir las tablas de contrastes y puntos sin contraparte.
- El caso contextual adicional se marcó como fixture sintético; no se ejecutó el solver. No se interpolaron datos ni se modificó el emparejamiento.
- `verify_pairing_context_receipt.py` comprueba textos visibles, conservación de códigos JSON, salidas de pruebas y hashes de informe/capturas.

Los detalles de origen están en `pairing-context-acceptance-receipt.json`.
