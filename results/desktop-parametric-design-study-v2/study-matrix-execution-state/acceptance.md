# Estado persistido en la matriz del estudio individual

## Cambio

La matriz de puntos de un estudio ahora muestra columnas distintas para **Ejecución**, **Clasificación** y **Periodicidad**. Un punto con ejecución `COMPLETE` y clasificación `MAX_CYCLES_NONCONVERGED` aparece como terminado y no convergido, sin que la periodicidad insuficiente oculte ninguna dimensión. Los estados guardados como clasificación también usan las etiquetas españolas comunes. Se conserva la disposición de los datos; no cambian CSV, manifiestos ni solver.

## Verificación

- `python -m pytest tests/test_desktop_design_study.py -q`: **40 passed**; luego, las cuatro regresiones de estado, tabla completa, filtros y CSV se ejecutaron de nuevo: **4 passed** tras añadir cobertura de cancelación y reutilización.
- Las comprobaciones cubren estado `COMPLETE`, cancelación, reutilización histórica verificada, clasificación no convergida y periodicidad en columnas independientes; la exportación CSV sigue conservando precisión y registros originales.
- `capture_synthetic_study_matrix.py` captura la tabla Qt nativa a 1360×340 con dos puntos sintéticos: uno periódico y otro completo pero no convergido. `capture-receipt.json` identifica el origen y los valores mostrados. No se ejecutó ninguna simulación.
