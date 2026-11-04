# DINO_PARAMETRIC_CROSS_STUDY_RESPONSE_PLOT_V1 — aceptación

La comparación guardada entre dos y cuatro estudios ahora incluye una gráfica de respuesta para la métrica elegida. La vista sólo acepta puntos que pertenecen a pareos exactos de RPM y contexto, con ambos extremos estrictamente `PERIOD_1` y con el valor de métrica finito y definido. No conecta puntos, interpola, ajusta ni crea diferencias. Los colores identifican estudios en una leyenda integrada a `CurvePlot`.

Los pareos excluidos, estados no periódicos, métricas indefinidas y puntos sin contraparte siguen en la tabla completa. Un aviso informa cuántos pares son graficables y cuántos quedan excluidos. Un resultado vacío conserva la explicación en el gráfico y en la tabla.

## Verificación

- Regresión enfocada: `test_cross_study_response_plot_uses_only_exact_period_one_metric_pairs` y `test_cross_study_comparison_page_keeps_full_identity_and_metric_states`: 2 PASS. Se comprobó selección de potencia/torque, RPM observadas, series no conectadas, exclusión del pareo insuficiente y conservación de filas.
- Regresión integrada final: `tests-final-v2/cross-study-response-plot-final-regressions.summary.json`: 66 passed y 2 fallos en aserciones antiguas ajenas a esta modificación (`test_component_build_uses_backend_derived_port_schedule` aún espera cuatro nombres de pestaña anteriores; `test_main_window_keeps_results_and_single_run_strip_visible` espera dos modos cuando el Desktop actual tiene tres). Ninguno toca el trazador ni el flujo de comparación. Las 58 pruebas de estudio/comparación/reporte pasaron dentro de esa suite. Los ocho tests restantes de Workbench pasaron al excluir esas dos aserciones obsoletas; compilación de los módulos modificados: PASS.
- Ejecución de ventana Qt nativa: `capture_native_fixture.py`; capturas `cross-study-response-plot-native-chart.png` y `cross-study-response-plot-native-table.png`, recibo `native-window-receipt.json`.
- Los datos de la captura son un fixture sintético marcado en pantalla para comprobar la presentación. No se ejecutó el solver y no constituyen evidencia física ni validación predictiva.
- COM/UIA: la evidencia previa en `../cross-study-comparison/acceptance.md` determina que el fallo era el teardown del proveedor COM del harness UIA después del cierre de la ventana; no se reprodujo en la aplicación Qt nativa. Esta tarea no requirió automatización UIA/COM.

## Límites

La gráfica presenta puntos medidos y pareados únicamente. Los resultados transitorios y los puntos sin pareja quedan en la tabla, no se mezclan en una serie de respuesta. La comparación sigue siendo descriptiva y no constituye una afirmación causal ni una predicción validada.
