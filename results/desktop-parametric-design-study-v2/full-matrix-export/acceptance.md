# Exportación de la matriz paramétrica completa

Estado: implementada y verificada con fixture sintético. No se ejecutó solver ni se modificó evidencia científica.

## Cambio

- Resultados agrega **Exportar matriz completa CSV…** para estudios geométricos y por RPM. Exporta todos los puntos del manifiesto aunque no estén seleccionados, conservando aparte la acción existente de exportar sólo filas seleccionadas.
- La matriz completa reutiliza el mismo constructor CSV y las verificaciones proyecto/manifiesto/SHA. Mantiene valores en precisión original, clasificación, periodicidad, ciclos, identities y hashes registrados.
- Los puntos no iniciados, cancelados o no convergidos permanecen como filas; las métricas no definidas quedan vacías y no se presentan como cero.
- Los estudios factoriales conservan el exportador factorial dedicado, por lo que no aparece un control genérico duplicado.

## Pruebas

- `python -m pytest tests/test_desktop_design_study.py -q -k 'full_parametric_matrix_export_includes_all_states_and_exact_precision or parametric_study_csv_export_preserves_precision_states_and_verified_sources'` — 2 passed.
- `python -m pytest tests/test_desktop_design_study.py -q` — 38 passed.
- `git diff --check` — limpio.
- El fixture incluye valores decimales largos y estados `MAX_CYCLES_NONCONVERGED`, `PREPARED/NOT_STARTED` y `CANCELLED`. La prueba confirma que la exportación completa incluye todos los puntos aun con una sola fila seleccionada, mientras el exportador de filas seleccionadas mantiene su requisito.

## Límites

Se conserva el límite de 30 puntos y el contrato CSV existentes. La matriz no agrega ni recalcula resultados físicos; exporta exclusivamente los campos registrados y verificados.
