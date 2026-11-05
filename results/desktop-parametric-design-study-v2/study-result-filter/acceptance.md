# Filtros de vista para matrices de estudios paramétricos

Estado: implementados y verificados con fixture sintético; sin ejecución de solver.

## Capacidad

La matriz de Resultados ofrece filtros opcionales por diseño, RPM exacta, estado registrado de ejecución y periodicidad. Al abrir el estudio, todos sus puntos están visibles. El contador muestra `visibles / total` y declara que la exportación completa incluye todas las filas. **Limpiar filtros** restaura la vista inicial.

Los filtros sólo usan `setRowHidden` en la tabla de presentación. No modifican el manifiesto, estados, valores, snapshots ni resultados. La exportación completa sigue recorriendo todos los puntos del manifiesto aunque la vista esté filtrada; la exportación de filas seleccionadas conserva su comportamiento. Los estados conocidos se traducen en la interfaz; los valores desconocidos permanecen en los datos y se presentan mediante la etiqueta neutral existente.

## Pruebas

- `python -m pytest tests/test_desktop_design_study.py -q -k 'parametric_study_filters_are_view_only_default_all_and_full_export_ignores_them'` — 1 passed.
- `python -m pytest tests/test_desktop_design_study.py -q` — 39 passed.
- `git diff --check` — limpio.
- `filter-widget-synthetic.png` es una captura del widget PySide6 sobre la plataforma Windows (1440×900). Los filtros seleccionan un diseño, 4000 RPM, Cancelado y No evaluada; el contador muestra 1 de 4. El fixture sólo verifica presentación y filtros.

## Límites

Las opciones provienen únicamente de valores presentes en el manifiesto y resultados importados. Los filtros no predicen, completan ni reinterpretan métricas. El estudio original y su exportación permanecen completos.
