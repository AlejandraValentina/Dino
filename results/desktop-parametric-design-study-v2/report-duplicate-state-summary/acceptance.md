# Resumen sin estados duplicados

La columna de clasificación/periodicidad muestra una sola etiqueta cuando ambos campos originales contienen el mismo estado. Si difieren, conserva las dos etiquetas; el punto sintético no convergido sigue mostrando por separado **Límite de ciclos · no convergida** y **Ciclos insuficientes**. El JSON conserva ambos campos originales exactamente.

## Pruebas y evidencia

- 46 pruebas pasan en `tests/test_desktop_technical_report.py` y `tests/test_desktop_design_study.py`.
- Desktop exportó el informe comparativo sintético desde la ventana real y Chrome renderizó el HTML a 1360 × 3000.
- Las capturas antes/después usan el mismo fixture. La evidencia de antes muestra ocho etiquetas periódicas repetidas en cuatro puntos; después quedan cuatro etiquetas, sin perder la condición no convergida.
- No se ejecutó el solver. El informe mantiene el aviso de fixture sintético y `NOT_CLAIMED`.
- `verify_acceptance_receipt.py` comprueba texto, JSON, dimensiones y hashes.

Los hashes están en `acceptance-receipt.json`.
