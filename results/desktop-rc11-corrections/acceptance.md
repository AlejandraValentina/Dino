# Dino Desktop rc11 — BLOCKED para aceptación Windows integrada

2026-11-03. Se construyó **un único** candidato desde `bb6903cd3acf1067c83ca6dd1d692c9a4db6af05`, en worktree limpio. Build PASS en 62,391 s; ZIP íntegro, sin reconstrucción. La clasificación BLOCKED corresponde a dos defectos P1 de presentación encontrados durante su aceptación, no a un fallo del build, del solver ni de integridad de proyectos.

Versión: **0.1.0-rc11 TRIAL**, Windows x64.

ZIP local: `C:\Users\ageribon.MIDES\Dino-artifacts\Windows\MotorSim-0.1.0-rc11-windows-x64-bb6903cd-trial-20261103T142323Z.zip`

SHA-256: `b021625b30afcd031b8464570aefb4d5bc189eb8167c7f45e1a787aff9e8270c`.

ZIP: 46.921.619 bytes; distribución: 113.752.655 bytes. Receta, identidad y dependencias en `package.json`. rc7, rc9 y rc10 no se modificaron ni reemplazaron; sin push o publicación.

## Decisión y límites

**No se concede READY_TRIAL.** El paquete conserva dos pendientes de la revisión:

1. **H1 / RC11-P1-01:** Comparar todavía presenta el motivo `NO_PERIODICITY_TRANSIENT_ONLY`; el resumen ancho de checkpoint expone `EXPLORATORY_CURVE_PARTIAL`. Capturas `exe-19`, `exe-21` y `exe-24`.
2. **H10 / RC11-P1-02:** el historial acoplado en 1360×900 queda reducido a una fila por la altura mínima del formulario central. Capturas `exe-16` y `exe-16b`. El explorador flotante compacto ya funciona; el defecto persiste al acoplarlo en la ventana mediana.

**Ambos están corregidos en fuente después del build**, con regresión y GUI real: traducción también de motivos/resumen, preservando códigos originales; explorador flotante temporal de 420 px a todas las resoluciones, tabla mínima de 180 px. `source-post-history-980.png`, `source-post-history-1360.png` y `source-post-reason-1360.png` demuestran la corrección en fuente. **Esos cambios no están dentro del ZIP identificado arriba.**

No se repite el build porque el encargo autoriza un único candidato. El paso siguiente concreto es autorizar otro candidato desde la fuente corregida y repetir sólo las comprobaciones afectadas de estados, historial y navegación. No se necesita una nueva investigación ni un cambio de física.

## Prioridad de integridad: resultado

- El supuesto P0 de tabla vacía al reabrir fue **NO REPRODUCIDO como pérdida de datos**. rc10 conservó el archivo exacto; el historial comprimía visualmente la tabla. Evidencia rc10 y hash en `rc10-project-integrity.json`.
- Durante esa comprobación se confirmó un defecto distinto de integridad: rc10 podía guardar `83.123456789` mm como `83.1` al releer campos formateados. Se trató como corrección prioritaria: EditRole conserva precisión completa, el delegado sólo redondea al pintar y guardar sin editar evita reconstruir la geometría.
- **rc11 empaquetado supera la regresión de precisión**: variante `precision-ab` con `103.123456789` mm, segundo guardado sin editar idéntico byte a byte, cierre del proceso, reapertura y edición con todos los decimales visibles. Capturas `exe-07`/`exe-08`, `precision-byte-receipt.json` y snapshot `precision-first-save.json`.

## Pruebas sobre el ejecutable real

Todas las acciones del recorrido se realizaron con teclado/ratón en `Dino2T.exe`; las verificaciones posteriores sólo leen/copian artefactos y no ejecutan el solver.

| Recorrido | Resultado | Evidencia |
|---|---|---|
| Crear, editar y guardar motor | PASS: `rc11-synthetic-corrections`, diámetro 57 mm, cárter 365 cm³, apertura primaria 105°; orígenes sintéticos explícitos | Capturas 01–04; proyecto guardado |
| Escape y variante A/B | PASS: base 83 mm, variante 103.123456789 mm, perfil/tabla/deltas y precisión conservados | Capturas 04–08; snapshot/hash de guardado |
| Cerrar y reabrir | PASS: parámetros y variante presentes; tabla visible al reabrir | Capturas 05–08 |
| Serial acotado | PASS: 3000 RPM, horizonte de 3 ciclos, 60 s, 1024 MiB, máximo 512 MiB de artefactos | Capturas 09–10; manifiestos seriales |
| Cancelar y reanudar desde menú compacto | PASS: `CANCELLED_CHECKPOINTED`; dos ciclos completos restaurados exactamente, 0 pasos físicos durante restore; termina a 3 ciclos, no convergido | Capturas 11–13; `packaged-verification.json` |
| A/B paralelo | PASS: 3000/3500 RPM × dos variantes, 1 ciclo/punto, tres workers, cuatro puntos COMPLETE, 20,344 s, límite agregado 120 s | Capturas 14–19; dispatch, procesos y ventanas |
| Interpretación de no convergidos | PASS parcial de presentación: transitorios desmarcados inicialmente; gráfico vacío por defecto; opt-in punteado; sin máximos de prestaciones calculados con transitorios. Persisten códigos en los dos lugares H1 | Capturas 18, 19, 22 |
| Condiciones A/B por RPM | PASS: compara pares exactos; diferencia de geometría explicada sin advertencia falsa entre RPM diferentes | Captura 19; tests de condiciones |
| Métricas principales | PASS: potencia/torque/BMEP visibles, transitorios e indefinidos etiquetados | Capturas 18–24 |
| Presión y ondas disponibles | PASS: unidades originales, ticks angulares y marcadores sin eliminar muestras del trazado/selección/exportación | Capturas 20–21 |
| Histórico sintético 30 puntos | PASS: importación del CSV+JSON existente, curvas, exportación de tabla, reapertura desde Desktop; puntos y unidades idénticos | Capturas 23–24; `packaged-historical.csv` + JSON |
| CSV sin JSON compañero | PASS: rechazo controlado con instrucciones; selección anterior conservada | Capturas 25–27; fixture negativo copiado, sin inventar resultados |
| 980×680 / 1360×900 / 1920×1080 | Realizadas: editor, resultados, menús, historial y presión. H10 falla al acoplar historial en la ventana mediana | Capturas con tamaños indicados |
| Procesos | PASS: workers del mismo EXE con `--multiprocessing-fork`, una ventana principal, ningún proceso del EXE tras cierre | `worker-processes.json`, `worker-windows.json`, `processes-terminal.json`, `processes-after-close.json` |
| Datos entregados al solver | PASS: comparación exacta del documento nativo completo, identidades vinculadas al manifiesto congelado, checkpoints por hash | `verify_packaged_evidence.py`, `packaged-verification.json` |

Los tamaños exactos se comprobaron con escala Qt efectiva de 100% sobre Windows al 125%. La barra de tareas se ocultó sólo para la captura 1920×1080 y se restauró. No se afirma cobertura de todos los monitores/DPI.

## Pruebas automatizadas y revisión

- Fuente integrada previa al candidato: **73 PASS, 1 SKIP**, 313,21 s.
- Delta de precisión/editor previo al candidato: **16 PASS**, 76,13 s.
- Fuente posterior a detectar los dos pendientes: **18 PASS**, 63,17 s, más comprobación focal final de los estados y el viewport real.
- Comprobación de artefactos producidos por el EXE: **PASS**, cinco corridas y roundtrip exacto de 30 puntos.
- El skip exige raíz histórica externa; el recorrido real de ese histórico se probó en el EXE.
- Las primeras regresiones fallidas y su corrección se conservan; no se reescribieron resultados. Los conjuntos se superponen y no se suman como tests distintos.

Revisión propia: `SELF_REVIEW`. La matriz [findings.md](findings.md) distingue CONFIRMADO, NO REPRODUCIDO y LIMITACIÓN DE DISEÑO, con pruebas y riesgos por hallazgo. No se representa esta entrega como una revisión independiente.

## Recursos, límites científicos y trabajo fuera de alcance

Preflight de almacenamiento PASS con 1,5 GiB + 1,2 GiB estimados y reserva de 2 GiB; 17 dependencias fijadas verificadas. Artefactos nuevos de ejecución: unos 9,73 MB; pico observado 330,20 MiB, por debajo de 1024 MiB. Todas las ejecuciones acotadas quedaron dentro de sus límites. No hubo campañas de convergencia, periodicidad o GCI.

Las configuraciones no activan reconstrucción espacial V2/MUSCL; Brent sigue desactivado por defecto. No se modificó solver físico, modelos, tolerancias, CFL, topología ni contratos persistentes. El motor y el histórico son sintéticos; validación experimental NOT_PERFORMED y predictividad NOT_CLAIMED. Undo/redo global y adición/eliminación de componentes se clasifican como capacidad mayor fuera de este parche.
