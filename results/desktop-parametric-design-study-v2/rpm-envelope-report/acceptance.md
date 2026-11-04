# Envolvente geometría × RPM en el informe técnico

Fecha: 2026-11-04. Datos del recorrido gráfico: **SYNTHETIC**; artefactos leídos de la integración sintética existente. No se ejecutó el solver.

## Cambio

- El informe técnico ahora incluye RPM exacta, clasificación, periodicidad, ciclos y valor geométrico en cada fila del estudio, además de ID de corrida, identidad de motor, hashes de resultado/artifact, ruta e identidad/hash del manifiesto de barrido.
- La envolvente identifica `RPM_ENVELOPE_V1`, informa los grids discretos guardados y explicita que el manifiesto no se interpola ni se resume en prestaciones. El estado científico continúa marcado según el manifiesto.
- Para envolventes, el export exige la ruta del manifiesto y verifica que el archivo siga coincidiendo con el objeto abierto. Verifica también el hash de cada `series.json` asociado; un sweep completo sin hash/ruta o con contenido cambiado se rechaza.
- No se editó el solver ni se reejecutaron puntos.

## Verificación

- `tests/test_desktop_technical_report.py -k rpm_envelope`: 3 pruebas focalizadas pasaron; cubren RPM/geometría/estados exactos, hash del sweep y rechazo de manifiesto obsoleto o no enlazado.
- Suite final ampliada: `tests-final/parametric-rpm-report-final.summary.json` (resultado completo allí).
- Recorrido nativo de Desktop: el script `verify_native_rpm_envelope_report.py` abrió en Windows la referencia del proyecto y el manifiesto sintético ya existente, importó sus 4 artifacts existentes y ejecutó el botón de exportación HTML. Recibo: `native-window-receipt.json`. No inició solver/campaña.
- Captura: `native-rpm-envelope-report.png`. El panel muestra los cuatro puntos 2 diseños × 2 RPM, `Límite de ciclos · no convergida` / `Ciclos insuficientes` y métricas en blanco.

## Evidencia y límite científico

- SHA-256 del manifiesto existente: `dee8469aa9ed77e51ff4e52e03311120fc4fecbee62efa7646d724a121579c23`.
- SHA-256 del informe HTML: `c58be643562e82cf0814a458e6589cc3faebbc92f375ba5106ee37c0dcea2d82`.
- SHA-256 de la captura: `8228f180e45bbe556cf523e222fc9115f3b7783e1cb956056236854f1cd4f630`.

Los cuatro puntos del fixture tienen estado `INSUFFICIENT_CYCLES`. Esto demuestra recuperación de procedencia, presentación y exportación; no demuestra una curva de prestaciones, periodicidad validada ni predicción. Se mantienen en vigor los límites científicos y el diagnóstico previo del error COM/UIA de teardown; esta aceptación empleó la ventana Qt nativa.
