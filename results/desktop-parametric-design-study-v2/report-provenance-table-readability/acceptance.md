# Legibilidad de procedencia en informe de comparación

**Origen de datos:** fixture sintético de presentación. No se ejecutó el solver ni se generaron predicciones.

## Resultado

La tabla de puntos del informe HTML pasó de 17 columnas a un resumen de 9 columnas. Cada fila conserva un control expandible **Ver fuente y hashes** con los identificadores, hashes y ruta exacta, además de la bandera de verificación. La procedencia desplegada se muestra como panel superpuesto y no ensancha la tabla. El apéndice JSON sigue conteniendo intacto el objeto completo de comparación. Los estados del resumen se presentan con etiquetas españolas.

La interacción verificada fue la acción nativa `Resultados > Comparar > Exportar informe técnico HTML`. La ventana real de Desktop y el resultado HTML se capturaron; Chrome se abrió a 1360 × 2000 px para revisar legibilidad. Una vista auxiliar abre el primer panel de procedencia para comprobar su tamaño y posición sin modificar el HTML exportado. Capturas y hashes están en `acceptance-receipt.json`.

## Pruebas

- `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`: **46 passed**.
- La regresión exige nueve encabezados en el resumen, cinco filas expandibles para los cinco puntos sintéticos, métricas y todos los campos de procedencia.
- La vista auxiliar a 1360 × 1100 px verifica visualmente hashes, rutas y verificación dentro del panel desplegado, sin ensanchar la tabla.
- El receipt comprueba hashes de las dos capturas y del HTML, dimensiones, preservación del apéndice y aviso de que la validación no está reclamada.

## Incidente del wrapper gráfico

La primera ejecución produjo el HTML y ambas capturas, pero `TemporaryDirectory` lanzó `WinError 145` al borrar `DawnWebGPUCache`, después de que Chrome hubiera guardado la imagen. El runner se ajustó a `ignore_cleanup_errors=True`; no hay cambios de producto asociados a ese error. La verificación del receipt se completó usando los artefactos ya generados, sin repetir el recorrido Desktop.

## COM/UIA

La evidencia aceptada de la tarea anterior localiza el incidente en el teardown de `pywinauto`/UIA: el harness reutilizaba un proveedor COM después de destruir la ventana nativa. No es una operación COM de Dino. El Python activo no tiene `pywinauto`, por lo que no se repitió ese camino. En esta ejecución sí se abrió Desktop en la sesión gráfica y se exportó el informe desde su acción nativa.

## Limitación restante

Los estados en la tabla de exclusiones de los gráficos y en puntos sin contraparte todavía exponen códigos internos; el resumen principal ya está traducido. La tarea READY `DESKTOP-PARAMETRIC-CROSS-STUDY-REPORT-STATE-LABELS-V1` cubre esas secciones.
