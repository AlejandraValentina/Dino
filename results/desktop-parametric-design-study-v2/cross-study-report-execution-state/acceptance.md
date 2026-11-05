# Estados de ejecución en el informe de comparación de estudios

## Cambio

Las tablas HTML de **pares excluidos de las gráficas** y **puntos sin contraparte** exponen el estado guardado de ejecución de cada punto, separado de la clasificación del solver y la periodicidad observada. El estado ausente se representa como “No informada”; no se infiere de las otras columnas. La tabla general de puntos y el objeto JSON reproducible del informe se mantienen completos.

## Verificación

- `python -m pytest tests/test_desktop_technical_report.py -q`: **16 passed**.
- La regresión cubre una ejecución `COMPLETE` no convergida, un punto cancelado con checkpoint sin pareja y un registro histórico que no informa `status`. Comprueba que las tres dimensiones se distinguen y que los códigos/objetos originales siguen en el JSON fuente.
- El harness llama la acción real de exportación HTML de Desktop con un fixture exclusivamente sintético y luego renderiza ese HTML con Chrome. La captura `html-report-state-view-1360x2400.png` y `capture-receipt.json` registran el origen y los hashes.
- No se ejecutó el solver ni se alteraron cálculos, artefactos científicos o contratos.
