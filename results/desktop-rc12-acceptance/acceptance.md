# Aceptación focal rc12 TRIAL

Fecha: 2026-11-03. Alcance: empaquetar las dos correcciones de presentación
pendientes de rc11 y comprobarlas en `Dino2T.exe`. No se cambiaron física,
solver, modelos, tolerancias, proyectos históricos ni contratos.

## Identidad del paquete

- Versión: `0.1.0-rc12 TRIAL`.
- Commit fuente limpio: `02f3ce8677cda592521fd554104a9ee9e04d4c10`.
- `build.json`: `source_dirty=false`, Windows x64, Python 3.11.0.
- ZIP: `C:\Users\ageribon.MIDES\Dino-artifacts\Windows\MotorSim-0.1.0-rc12-windows-x64-02f3ce86-trial-20261103T151816Z.zip`.
- SHA-256: `17c0ef36647ba91fc1a6c37b8719f792ef7ceac618d748ad632e2c2cdb498469`.
- Integridad ZIP: `testzip=None`, 327 entradas. El manifiesto interno identifica la misma versión y commit.
- Un único build; duración 63,219 s; PyInstaller terminó con código 0. rc7, rc9, rc10 y rc11 no se alteraron.

## Verificaciones en el ejecutable empaquetado

1. Arranque de `Dino2T.exe`: una ventana principal, responde y muestra `0.1.0-rc12` en el pie.
2. Apertura por la interfaz del proyecto sintético existente `rc11-synthetic-corrections`; cilindro, distribución y cuatro filas de lumbreras cargan. Se mantuvo intacto el proyecto de referencia.
3. MODELO → Escape abre el perfil y las cotas guardadas. La variante y comparación A/B existentes continúan disponibles; no se escribió ni cambió el proyecto durante esta comprobación.
4. El explorador de historial flotante a 1360×900 permite mostrar cinco registros simultáneamente. Estados legibles como “Límite de ciclos · no…” y “No convergida”; no hay códigos de clasificación en las celdas.
5. RESULTADOS → Comparar muestra la explicación “Configuraciones distintas…” y el estado “TRANSITORIO, NO CONVERGIDO”, sin el identificador interno en el resumen visible. Las curvas dejan los puntos fallidos/no periódicos como huecos y las tarjetas señalan su condición.
6. El detalle científico y de procedencia sigue disponible al inspeccionar la corrida: identidad, configuración, SHA-256 de resultado/checkpoint, clasificación y periodicidad. El código original permanece en el tooltip técnico y los artefactos; las etiquetas visibles dan su significado en lenguaje normal.
7. No se inició una corrida ni campaña nueva. La prueba rc11 ya aceptada contiene la recuperación real desde checkpoint válido, cancelación, continuidad de ciclos, edición/guardado/reapertura exactos del escape, comparación A/B, y ronda CSV de 30 puntos. Se reutiliza esa evidencia porque los cambios rc12 son presentación de estados y espacio del historial; no alteran los contratos ni el flujo de cálculo. La evidencia está en `results/desktop-rc11-corrections/acceptance.md` y `packaged-verification.json`.

Capturas del EXE rc12: `captures/01-startup.png`, `captures/08-history-all-1360.png`,
`captures/11-comparison-tab.png`, `captures/13-history-tooltip.png` y
`captures/14-exhaust-editor.png`. Antes/después de la corrección de historial
también queda en `../desktop-rc11-corrections/captures/exe-16b-history-settled.png`
y esta captura rc12 `captures/08-history-all-1360.png`.

## Pruebas de fuente y recursos

- Antes del empaquetado: `python -m pytest -q tests/test_desktop_rc11_corrections.py tests/test_desktop_rpm_curves.py` → **18 PASS**, 62,60 s.
- Preflight de salida y temporales: **PASS**, estimación 2,5 GiB y reserva 2 GiB; espacio libre observado 27,1 GB.
- Las 17 dependencias de `packaging/requirements-build.txt` coinciden con `.venv-build`.
- No se ejecutaron pruebas de solver ni campañas científicas durante rc12.

## Decisión

**READY_TRIAL.** Las dos correcciones se comprobaron visualmente en el binario
correcto de dos tiempos y no se observó un defecto P0/P1 nuevo. Esto acepta la
integración funcional TRIAL, no autoriza su publicación ni implica validación
experimental o predictiva. Las capturas incluyen una inspección de tooltip para
confirmar que el dato técnico original sigue accesible; la clasificación visible
en la tabla permanece traducida.

## Cierre del dueño

El dueño aceptó rc12 como **READY_TRIAL para pruebas internas** el 2026-11-03.
La etapa Desktop queda cerrada. El ZIP, hash, capturas, pruebas y metadatos de
construcción quedan preservados; no se generará rc13 ni se iniciará otro
rediseño sin un defecto concreto que lo justifique.
