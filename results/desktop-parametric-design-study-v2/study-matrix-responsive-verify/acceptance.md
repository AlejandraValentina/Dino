# Matriz paramétrica: verificación de anchuras

## Defecto y corrección

La última columna de la tabla estiraba hasta absorber el espacio sobrante, dejando demasiado poco ancho para ejecución y periodicidad. La matriz ahora preserva anchos legibles para **Ejecución**, **Clasificación** y **Periodicidad**, y asigna el espacio sobrante a **Valor**. Los diez campos conservan su orden y sus datos.

## Verificación

- El harness muestra la tabla Qt nativa a 980×680 y 1360 px de ancho; en la sesión Windows actual, el área visible limita la altura solicitada de 900 a 881 px. Todos los textos de los tres estados se verifican contra el ancho de celda y las imágenes muestran todas las columnas sin truncamiento.
- Capturas y SHA-256: `study-matrix-980x680-left.png`, `study-matrix-1360x881-left.png`, `capture-receipt.json`.
- Suite completa `python -m pytest tests/test_desktop_design_study.py -q`, ya con el ajuste de anchos: **40 passed**. La comprobación focalizada de configuración/layout también pasó: **2 passed**.
- No se usó el solver. La tabla contiene sólo datos sintéticos de presentación.
