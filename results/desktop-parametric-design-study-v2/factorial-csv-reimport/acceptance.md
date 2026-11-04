# Reimportación del CSV factorial — aceptación

Desktop reabre el CSV V1 exportado anteriormente como snapshot de solo lectura, separado de las curvas normales y de las corridas ejecutables. Se valida el encabezado exacto, 13 filas (4 `POINT` y 9 `CONTRAST`), IDs, niveles factoriales, RPM, clasificaciones, calificaciones, fórmulas, metadatos y hashes. Los números se mantienen como texto para conservar su representación decimal original.

Cuando los archivos siguen disponibles, se recalculan los SHA-256 del manifiesto, `result.json` y `run.json`, y se cotejan los bindings de corrida e identidad. La vista distingue esta comprobación actual de la comprobación registrada al exportar. Si un archivo falta o cambió, el snapshot conserva sus datos y muestra el estado correspondiente sin presentarlo como verificado actualmente.

## Verificación

- `tests/test_parametric_factorial_snapshot.py`: cubre el export existente, schema exacto, rechazo de columnas/filas/hashes inválidos, cambios de manifiesto/artifact, duplicados, fórmulas faltantes y calificaciones no periódicas. También comprueba que la definición de campos permanece sincronizada con el exportador.
- Prueba de vista Desktop: 1 PASS; 4 diseños y 9 contrastes visibles, sólo lectura, `NOT_CLAIMED`, las curvas normales vacías, valores exactos y origen de contraste omitido identificado.
- Regresión integrada final: `tests-final-v3/factorial-csv-reimport-final-regressions-v3.summary.json`: **71 passed**, sin fallos. Incluye los 5 módulos de estudios, Desktop, informes y snapshots. Suite focalizada final: 7 PASS. Módulos modificados compilados.
- Ventana Qt nativa Windows: `capture_native_factorial.py` abrió el CSV histórico aceptado mediante el flujo normal de importación. Receipt: `native-window-receipt.json`; capturas: `factorial-csv-snapshot-native-points.png` y `factorial-csv-snapshot-native-contrasts.png`.
- CSV fuente SHA-256 `753e67bf1aaef28effdada5cf455c744310161300ae0c9ddf67821e9a356b834`; manifiesto actual coincide (`79eb2cff8b3253842e84d7e891a1f5f5de0687cfafad45ac7d411db311cd49cd`); los cuatro artifacts actuales coinciden por hash e identidad. No se ejecutó el solver.

## Limitación preservada

Las filas `CONTRAST` de este export V1 contienen `[null,null,null,null]` en sus columnas de IDs y hashes fuente, aunque las cuatro filas `POINT` sí incluyen sus identidades y hashes completos. El snapshot no rellena esos campos: los identifica como ausentes y conserva las fuentes por punto. Los contrastes disponibles siguen etiquetados como descriptivos, no validados; los resultados de la fixture son sintéticos y `NOT_CLAIMED`.
