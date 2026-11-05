# Filtros para comparación entre estudios

Estado: implementación y verificación focalizadas completas. No se ejecutó el solver.

## Cambio

La tabla **Comparar estudios guardados** permite filtrar por RPM exacta y por
pares exactos o puntos sin pareja. Todas las filas quedan visibles por defecto;
el contador indica cuántas filas de la comparación están a la vista y **Limpiar
filtros** restablece ambos selectores. El selector conserva el valor flotante
exacto como dato y ofrece su representación almacenada en el tooltip.

Los filtros sólo ocultan filas con `setRowHidden`. No modifican pares, estados,
el gráfico, manifiestos ni valores. La generación de CSV continúa usando el
objeto verificado completo: una prueba deja la vista filtrada al punto sin
pareja y comprueba que el constructor de exportación conserva los dos pares y
el punto sin pareja, con sus tres RPM. El orden de la tabla puede cambiar por
su ordenamiento habilitado; las pruebas identifican las filas por RPM y sus
metadatos, no por posición.

## Verificación

- `python -m pytest tests/test_desktop_design_study.py -q` — **40 passed**.
- `git diff --check` — limpio.
- `python results/desktop-parametric-design-study-v2/cross-study-result-filter/capture_synthetic_cross_study_filter.py` — abrió la página real de Resultados en Qt/Windows y produjo la captura a 1600×1020. La evidencia muestra dos filas: un par exacto y un punto con ciclos insuficientes sin pareja; contador `2 de 2 filas visibles`.
- Captura: `cross-study-filter-synthetic.png`. Generador reproducible: `capture_synthetic_cross_study_filter.py`.

Los manifiestos, nombres y puntos de la captura son **sintéticos para presentación**;
no constituyen datos experimentales, una corrida del solver ni validación física.

## Alcance pendiente

No se reabrió el diagnóstico UIA/COM: la evidencia vigente clasifica el error
anterior como consulta de un proveedor UIA COM retenido por el harness después
de destruir la ventana nativa, no como una operación COM de Dino. Esta entrega
no cambia ni depende de automatización UIA.
