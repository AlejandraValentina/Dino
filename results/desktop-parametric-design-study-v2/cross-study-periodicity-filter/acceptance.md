# Filtros de periodicidad por extremo en Comparar

Estado: implementados y verificados. Sin ejecución del solver.

## Capacidad

La comparación entre estudios agrega selectores independientes de periodicidad
para los extremos A y B. Las opciones proceden de los valores presentes en los
puntos cargados y usan las etiquetas de estado existentes. Un extremo sin punto
se representa como **Sin punto**; los puntos cuyo estado no fue evaluado
conservan la etiqueta existente **No evaluada**.

Los filtros se aplican sólo a las filas mostradas. Todas aparecen al cargar la
comparación; **Limpiar filtros** restaura todas las opciones y cambiar el
proyecto descarta opciones de la comparación anterior. Manifiestos, puntos,
clasificaciones, valores, gráfica y exportación permanecen sin alterar. El CSV
completo conserva pares y puntos sin contraparte aunque se filtre la tabla.

## Pruebas

- `python -m pytest tests/test_desktop_technical_report.py tests/test_desktop_design_study.py -q` — **56 passed**.
- La regresión usa un fixture sintético con un par `PERIOD_1`/`INSUFFICIENT_CYCLES` y un punto no evaluado sin contraparte. Comprueba filtros independientes A/B, estado traducido, opción **Sin punto**, contador, limpieza, reinicio al cambiar el proyecto y que el CSV completo aún incluye las tres RPM y sus tipos de pareamiento.
- `capture_synthetic_periodicity_filter.py` renderizó la sección Comparar real de PySide6/Windows con un fixture sintético. La captura muestra los filtros A/B, un extremo periódico, otro con ciclos insuficientes y `1 de 2 filas visibles`.
- Captura: `cross-study-periodicity-synthetic.png`.
- `git diff --check` — limpio.

La captura y los fixtures son **sintéticos y sólo verifican presentación/flujo**;
no constituyen datos experimentales, una predicción ni evidencia de desempeño.
