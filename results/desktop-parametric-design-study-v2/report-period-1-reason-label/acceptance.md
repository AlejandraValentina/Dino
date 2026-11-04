# Redacción del criterio de periodicidad en exclusiones de gráficos

Las explicaciones del gráfico comparativo ya no exponen `PERIOD_1`; indican **periodicidad observada de orden 1**. La explicación de métrica ausente usa la misma terminología. El filtro sigue exigiendo los mismos extremos PERIOD_1, condiciones exactas y métrica finita. Los estados fuente siguen intactos en el JSON.

## Comprobación

- `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`: **46 passed**.
- Desktop exportó el informe sintético desde la aplicación real; Chrome lo renderizó a 1360 × 3000.
- `verify_acceptance.py` verifica que el texto visible esté traducido y que los códigos de periodicidad sigan en el JSON adjunto.
- No se ejecutó el solver ni se modificó la clasificación científica.

Hashes y dimensiones: `acceptance-receipt.json`.
