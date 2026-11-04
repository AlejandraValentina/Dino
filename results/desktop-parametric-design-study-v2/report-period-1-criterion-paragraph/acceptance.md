# Texto de criterio para curvas de respuesta

La introducción a las curvas de comparación describe el filtro en español: RPM y contexto operativos exactos, periodicidad observada de orden 1 en ambos extremos y métrica definida y finita. No expone `PERIOD_1` como código. Las reglas de elegibilidad y la restricción de no conectar/interpolar/ajustar puntos no cambiaron; el JSON mantiene los estados fuente originales.

## Verificación

- 46 pruebas pasan en `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`.
- Desktop exportó el informe sintético desde la ventana visible; Chrome lo verificó a 1360 × 3000.
- `verify_acceptance.py` verifica criterio visible, valores fuente, estado del runner y hashes.
- No se ejecutó el solver ni se modificó la física.
