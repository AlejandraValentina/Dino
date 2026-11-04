DINO_PARAMETRIC_CROSS_STUDY_COMPARISON_V1 — aceptación

Desktop permite elegir entre dos y cuatro estudios paramétricos ligados al proyecto. Antes de comparar, verifica el SHA-256, schema e identidad de cada referencia, la baseline común, y los hashes/resultados de cada punto terminal; después reutiliza el importador existente para verificar los artifacts. Se rechazan baselines distintos, fuentes cambiadas y matrices mayores de 30 puntos por estudio. No hay cálculos del solver.

La tabla conserva cada punto, incluidos los no pareados. Un par directo requiere RPM exacta y coincidencia de combustible, AFR, número total de celdas, horizonte de ciclos, identidad del solver e identidad de implementación. Las geometrías/identidades de motor se exponen por prefijo visible y SHA completo en tooltip. Los puntos sin par explican si faltó una RPM exacta, su artifact terminal o si difirieron campos operativos.

Las métricas y diferencias sólo se muestran si ambos resultados son PERIOD_1 y la magnitud está definida. No se interpolan curvas, no se promedian pares ni se infieren efectos agregados. La exportación HTML contiene los manifiestos fuente, rutas y hashes, configuración/identidad por punto, estados, pareos y filas sin contraparte.

Verificación:
- `python -m compileall -q motorsim/desktop/results_page.py motorsim/desktop/technical_report.py tests/test_desktop_design_study.py tests/test_desktop_technical_report.py results/desktop-parametric-design-study-v2/cross-study-comparison/verify_cross_study_desktop.py`: PASS.
- Suite completa relevante: `tests/test_design_study.py tests/test_desktop_design_study.py tests/test_desktop_technical_report.py`: 44 passed in 198.53 s; ejecución final registrada en `tests-final/desktop-parametric-cross-study-final-regressions.summary.json`.
- Ventana nativa Windows: abrió dos estudios sintéticos previos, volvió a importar 8 puntos, generó 8 pareos a 3000 RPM y mantuvo 2 puntos a 4000 RPM sin contraparte. Los 8 son `INSUFFICIENT_CYCLES`; cero métricas o diferencias definidas. Evidencia reproducible: `native-window-receipt.json` y `cross-study-comparison-desktop-real-window.png`.
- La acción real de exportación Desktop produjo HTML y SHA-256 `12d12e45352281198b88e518df8a301d1969c6c56f6c88241f99c5a2edb2cce3`; el archivo de prueba se generó en una carpeta temporal y no se incluyó en el repositorio.
- Pruebas adversariales rechazan hash de fuente alterado, baseline distinta y matrices sobredimensionadas antes de importar artifacts.

Límite científico: ambos estudios reales usados para integración son sintéticos y no convergidos; esta comparación valida el flujo del producto, no la física predictiva.

COM/UIA anterior: la evidencia V1 identifica el fallo como teardown del harness UIA que conservó un proveedor COM después de destruir la ventana nativa. No fue un fallo del solver ni de la exportación Dino. La repetición de pywinauto sigue pendiente porque no está instalado en Python activo; la interfaz fuente se verificó con ventana nativa Qt y cierre normal.
