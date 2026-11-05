# Estado de ejecución en comparaciones entre estudios

## Cambio

La tabla ahora presenta por separado el estado de ejecución persistido en cada punto, su clasificación y la periodicidad observada. El filtro A y el filtro B de ejecución usan únicamente el campo `status`; la clasificación y periodicidad conservan filtros independientes. Los estados no informados se muestran como tales y la ausencia de un punto de comparación se representa como **Sin punto**.

Los filtros sólo afectan a la vista. La comparación verificada y su exportación CSV conservan todas las filas originales. No se modificaron el solver, la clasificación científica ni los contratos de resultados.

## Verificación

- `python -m pytest tests/test_desktop_technical_report.py tests/test_desktop_design_study.py -q`: **56 passed**.
- La regresión cubre punto terminado periódico, ejecución terminada no convergida (clasificación `MAX_CYCLES_NONCONVERGED` y periodicidad `INSUFFICIENT_CYCLES`), cancelación con checkpoint, punto sin contraparte, filtros combinados, reinicio al cambiar de proyecto y exportación CSV sin filtrado destructivo.
- Capturas nativas de PySide6 con datos de presentación **sintéticos**, no resultados del solver ni validación física: 980×680, 1360×900 y 1600×1020. Los hashes y dimensiones están en `capture-receipt.json`.
- `git diff --check`: sin errores.

## Limitación

La clasificación o periodicidad ausente en un artefacto histórico se identifica como no informada/no evaluada; la interfaz no reconstruye ni infiere esos datos.
