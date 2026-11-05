# Legibilidad de procedencia de manifiestos en informes HTML

Estado: implementación verificada en el renderer de informes. Sin cambios de
solver ni ejecuciones físicas.

## Cambio

La tabla de manifiestos seleccionados pasó de mostrar ruta y SHA-256 completos
en dos columnas simultáneas a una tabla compacta de tres columnas. Cada fila
identifica el manifiesto por nombre, presenta un prefijo SHA-256 y ofrece
**Ruta y hash completos** para abrir los valores exactos envueltos dentro de la
misma celda. El layout fijo limita el ancho de la tabla; la ruta y hash
completos se conservan también en el objeto reproducible JSON del informe.

No se recalculan, modifican ni eliminan procedencia o datos fuente.

## Verificación

- `python -m pytest tests/test_desktop_technical_report.py -q` — **16 passed**.
- `python -m pytest tests/test_desktop_technical_report.py tests/test_desktop_design_study.py -q` — **56 passed**.
- `git diff --check` — limpio.
- `capture_manifest_report.py` generó y abrió con Chrome headless un informe HTML del renderer real, con rutas sintéticas largas, a 1360×1100. Se revisaron los estados compacto y expandido.
- Capturas: `manifest-provenance-compact.png` y `manifest-provenance-expanded.png`; sus SHA-256 y los del HTML constan en `capture-receipt.json`.
- `test_cross_study_manifest_provenance_is_compact_but_exactly_accessible` comprueba tres encabezados, identificación abreviada, expansión, recuperación exacta de ruta/hash y conservación en JSON.

Toda la procedencia de las capturas es **sintética para presentación**. No
representa una medición, resultado físico ni validación predictiva.

## Límites científicos y de automatización

La exportación sigue identificando los contrastes como descriptivos y declara
que la validación no está reclamada. Se conserva la clasificación histórica
del incidente UIA/COM en
`results/desktop-ui-automation-com-repro/acceptance.md`: el fallo posterior al
cierre se atribuyó a que el harness consultaba un proveedor UIA retenido tras
destruir la ventana nativa; no fue una operación COM de Dino. La automatización
remota continúa desconectada y esta modificación no añade dependencia de UIA.
