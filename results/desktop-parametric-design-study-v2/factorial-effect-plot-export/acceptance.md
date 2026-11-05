# Exportación reproducible de la figura factorial

Estado: implementada y verificada con fixtures sintéticos; no ejecutó ni recalculó ningún solver.

## Recorrido de exportación

Desde el estudio factorial abierto, **Exportar gráfico factorial PNG + fuentes…** produce tres archivos nuevos sin sobrescribir los existentes:

1. PNG de la figura que se muestra en Resultados. Incluye metadatos con `study_id`, SHA-256 del manifiesto, SHA-256 del CSV compañero y la calificación `NOT_CLAIMED`.
2. CSV de cuatro puntos y nueve contrastes producido por el exportador verificado existente, conservando fórmulas, estados, IDs y hashes de las cuatro fuentes. Los contrastes no disponibles permanecen sin valor.
3. JSON con paths y hashes del manifiesto, PNG y CSV, el estado de disponibilidad de efectos y la calificación científica.

Antes de exportar se vuelve a verificar que el manifiesto abierto coincida con el archivo y con su referencia SHA registrada en el proyecto. Si el manifiesto cambió, no se crean archivos. Si alguno de los destinos ya existe, se rechaza el conjunto sin reemplazarlo.

## Pruebas

- `python -m pytest tests/test_desktop_design_study.py -q -k 'factorial_effect_plot_export_binds_png_csv_and_manifest_hash or factorial_effect_plot_uses_verified_signed_values_and_renders'` — 2 passed.
- `python -m pytest tests/test_desktop_design_study.py -q` — 37 passed.
- `git diff --check` — limpio.
- El test abre el PNG generado con Qt, verifica metadatos embebidos, hashes cruzados, 13 filas CSV y bloqueo ante colisión de destinos, cambios del manifiesto o cambios de la tabla que dejarían obsoleta la figura. Datos de prueba sintéticos y procedencia identificada.

## Límites

La exportación es un paquete de documentación de contrastes observados, no una predicción ni una validación experimental. No agrega incertidumbre ni atribución causal. Los paths conservan la procedencia exacta y pueden ser locales a la máquina que genere el archivo.
