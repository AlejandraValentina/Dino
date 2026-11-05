# Procedencia: ejecución, clasificación y periodicidad

## Cambio

La ficha de trazabilidad del punto seleccionado distingue ahora el estado de ejecución persistido en el manifiesto, la clasificación del solver y la periodicidad observada. Los tres valores permanecen separados y se presentan con las etiquetas traducidas existentes. Los datos originales y el manifiesto no se reescriben.

## Evidencia

- Regresión `test_parametric_point_details_bind_manifest_nested_sweep_and_source_status`: un punto sintético con `status=COMPLETE`, `classification=MAX_CYCLES_NONCONVERGED` y `periodicity=INSUFFICIENT_CYCLES` comprueba los tres textos independientes además de las verificaciones previas de hashes, manifiesto anidado, fuente y validación no reclamada.
- Suite `python -m pytest tests/test_desktop_design_study.py -q`: **40 passed**.
- Captura de la aplicación Dino Desktop en ventana Qt nativa de Windows, con un manifiesto **sintético de presentación** y sin ejecutar el solver. La captura muestra los tres campos en la ficha del punto. `capture-receipt.json` incluye hash del manifiesto y de la imagen.
- No se modificaron el solver, los estados científicos, la persistencia ni la exportación.
