# Fuente rc11 — controles previos al candidato único

2026-11-03. Alcance: hipótesis de revisión rc10, correcciones confirmadas de Desktop y protección de precisión. Solver, contratos persistentes y modelos físicos sin cambios.

- Prueba integrada final: **73 PASS, 1 SKIP**, 313,21 s (`source-tests/rc11-final-source.summary.json`). La omisión corresponde a la raíz histórica externa; se cubre importación real en EXE.
- Delta final de precisión/editor: **16 PASS**, 76,13 s (`source-tests/rc11-precision-regression.summary.json`). Incluye longitud sintética de precisión arbitraria, identidad exacta al guardar sin editar y reapertura.
- Presentación/curvas: **15 PASS** (`final-presentation-tests.txt`); distribución/versión: **6 PASS** (`version-check.txt`). Conjuntos superpuestos; no se suman como pruebas diferentes.
- Primera regresión integrada: 3 fallos, 69 PASS, 1 SKIP. Se corrigió ausencia de provenance opcional, se conservó el rol interno con delegado visual y se actualizó la prueba estructural al eliminar el scroll exterior. Evidencia original conservada.
- Un intento de prueba de precisión se interrumpió porque el fixture no seleccionaba la variante y abría el mensaje modal de motor base. Se corrigió el fixture; no fue una divergencia del solver ni una corrida científica.
- EXE rc10: tabla desaparece al comprimir el editor con historial, sin pérdida del proyecto. CSV+JSON abre 30 puntos. Copia sintética adicional confirma el redondeo al guardar, con entrada 83.123456789 y salida 83.1 en `rc10-precision-after.dino2t.json`; se preserva la copia, sin editar el caso histórico original.
- GUI de fuente compacta comprobada; las capturas finales de aceptación se producirán sobre el único ejecutable nuevo.
- Dependencias fijadas: **17 PASS**. Almacenamiento: **PASS**, 1,5 GiB distribución + 1,2 GiB trabajo/copia y reserva de 2 GiB. No se limpiaron históricos.

rc11 se construye desde un worktree limpio del commit de corrección; no incorpora los cambios locales ajenos del runner científico. Se conserva rc7, rc9 y rc10. Sin push ni publicación. La decisión de aceptación del EXE sigue pendiente hasta completar sus pruebas.
