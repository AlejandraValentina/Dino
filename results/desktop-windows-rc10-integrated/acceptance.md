# Dino Desktop 0.1.0-rc10 — READY_TRIAL

Aceptación funcional Windows integrada, 2026-11-03. Un único candidato construido desde `3ad53eefbfe879322e2a9c3eefddf65e01b9a7bb`, worktree limpio, Python 3.11.0, Windows 10 x64. No hubo reconstrucción ni promoción estable. rc7 y rc9 permanecen intactas.

Paquete: [ZIP Windows TRIAL](<C:/Users/ageribon.MIDES/Dino-artifacts/Windows/MotorSim-0.1.0-rc10-windows-x64-3ad53eef-trial-20261103T123310Z.zip>).

SHA-256: `7f7466d63b754b24328eee6016bdbbcf04ef8b59e1e6808234f0f9fc1d0ecf3c`. Tamaño ZIP: 46.920.989 bytes; distribución: 113.743.944 bytes. Identificación completa en `package.json`; build único de 73,203 s en `build/rc10-windows-candidate.summary.json`.

## Cambios y defectos corregidos

- Admisión y conductos de transferencia tienen entradas separadas en MODELO. Comparten la tabla existente, con filtrado por rol y conservación del borrador al cambiar de componente. No hay dos controles para el mismo dato ni cambio de contrato.
- Escape usa perfil/cotas A/B, tabla de tramos y avanzado en pestañas. Los botones de guardado permanecen accesibles fuera del contenido desplazable; se elimina el scroll exterior redundante a 980×680.
- Se corrigió la tabla de estaciones avanzadas que permanecía oculta al abrir su grupo.
- Se integran las evoluciones de navegación, resultados, CSV y MODELO ya aceptadas desde rc9. Solver, tolerancias y modelos experimentales no se modificaron.

## Evidencia ejecutada

Las acciones funcionales se hicieron con teclado y ratón sobre **Dino2T.exe empaquetado**, no invocando widgets o el solver desde Python. `verify_packaged_evidence.py` sólo lee y copia los artefactos resultantes para comprobar contratos, hashes y parámetros. La revisión es `SELF_REVIEW`; esta aceptación no constituye un gate científico ni revisión independiente de validez predictiva.

| Recorrido | Resultado y evidencia |
|---|---|
| Inicio Windows | Una ventana principal; arranque al escalado Windows habitual en `captures/exe-01-default-scale-start.png`. |
| Crear motor sintético y editar | `SYNTHETIC_RC10`: diámetro 57 mm, cárter 365 cm³, admisión 85 mm, transferencia primaria 52 mm; capturas 02, 14 y 15. |
| Lumbreras y distribución | Apertura primaria 105°, cierre 255°, duración 150°, cota 34,597071032 mm. Tabla y distribución sincronizadas: capturas 03, 04 y 16. |
| Duplicar y modificar escape | Variante `escape-plus20`, primer tramo 83→103 mm. Perfil/cota/delta sincronizados; selección del segundo tramo en perfil reflejada en tabla: capturas 05, 17 y 18. |
| Persistencia y compatibilidad | Guardado, cierre completo del proceso, nueva apertura y restauración de parámetros/variante/recetas. Proyecto anterior `synthetic-editor-v2` abierto sin modificarlo: capturas 13 y 20. Historial durable vuelve a abrir: captura 21. |
| Serial y cancelación | 3000 RPM, horizonte 3 ciclos, 60 s, 1024 MiB, máximo 512 MiB de artefactos. Cancelación real con un ciclo completo conservado: `CANCELLED_CHECKPOINTED`, captura 06. |
| Recuperación | Mismo Run ID, checkpoint verificado por hash, restauración exacta de 1 ciclo, 0 pasos físicos durante restore, 2 ciclos nuevos hasta 3. Terminal `MAX_CYCLES_NONCONVERGED`, `NOT_CONVERGED`. |
| Sin checkpoint | Nueva sesión sin corrida seleccionada: reanudación deshabilitada; captura 19. No se fabrica un checkpoint ni se inicia cálculo. |
| A/B paralelo real | Base y variante, 3000/3500 RPM, 1 ciclo/punto, 60 s/punto y 120 s agregados. Tres workers, cuatro puntos COMPLETE, manifiesto terminal en 20,094 s. Capturas 07–10; `packaged-processes-start.json`, `packaged-worker-windows.json`, `packaged-runs/dispatch.json`. |
| Resultados no periódicos | Cuatro puntos `INSUFFICIENT_CYCLES`/`MAX_CYCLES_NONCONVERGED`. Curvas exploratorias punteadas y diferencias definitivas de potencia/torque no definidas. Capturas 09–10. |
| Señales y ausencia de datos | Inicio sin corrida: curvas sin valores, sin inventarlos. Corrida real reabierta: presión y mapa discreto disponibles, captura 22. |
| Histórico y CSV | Histórico sintético de 30 puntos importado, incluyendo puntos inválidos; curvas A/B, exportación de tabla CSV + JSON compañero y reapertura del CSV desde Desktop. Capturas 11–12. Puntos y unidades idénticos al original, sin recalcular. |
| Resoluciones y controles | 980×680: capturas 05, 14, 15; 1360×900: 09–13, 20–22; 1920×1080: 16–18. Sin controles de guardado recortados; perfil y tabla accesibles por pestañas. |
| Limpieza | Tras finalizar despacho sólo queda el principal; tras cerrar no queda ningún `Dino2T.exe`: `packaged-processes-terminal.json` y `packaged-processes-after-close.json`. |
| Datos entregados al solver | Comparación exacta de **todo** el `native_configuration` de las cinco corridas con el proyecto resuelto a su RPM. Identidades vinculadas al manifiesto congelado del paquete; checkpoints verificados. `packaged-verification.json`. |

Pruebas automatizadas en fuente: **66 PASS, 1 SKIP** en 282,96 s; suites de Desktop, MODELO, distribución, ejecución/resultados y persistencia. El skip exige raíz histórica externa; la importación real de los 30 puntos se probó en el EXE. Pruebas finales focalizadas: **2 PASS**. Verificación posterior de artefactos: **PASS**. No se repitieron benchmarks, campañas científicas ni auditorías históricas.

Para los tres tamaños exactos se utilizó escala Qt efectiva de 100% (`QT_SCALE_FACTOR=0.8` sobre Windows al 125%); también se comprobó el arranque con el escalado habitual sin override. El ensayo 1920×1080 ocultó temporalmente la barra de tareas y luego la restauró. No se extrapola esta prueba a otros DPI/monitores.

## Recursos y límites

Preflight de dependencias y almacenamiento PASS antes del único build: estimación 1,5 GiB de distribución + 1,2 GiB de temporales/copia y reserva de 2 GiB. No se borró evidencia histórica. Cinco corridas durables, unos 9,8 MB en total. Pico observado: 318,74 MiB; cada ejecución quedó bajo sus 1024 MiB y su límite de tiempo. Ver tiempos y tamaños por corrida en `packaged-verification.json`.

## Limitaciones que permanecen

- READY_TRIAL expresa usabilidad funcional de este candidato; no es versión estable ni validación predictiva.
- El motor creado y el histórico son **sintéticos**. Las ejecuciones nuevas son breves y no convergidas; no permiten atribuir mejoras definitivas de prestaciones al escape.
- Las capacidades de geometría, topología e inversión angular siguen limitadas al modelo existente; los datos desconocidos conservan su identificación.
- MUSCL y la reconstrucción espacial V2 continúan opt-in: las cinco configuraciones no contienen identidad de reconstrucción espacial. Brent no se activó; el valor por defecto sigue siendo bisección. Los schemas físicos existentes con sufijo V2 no se confunden con la reconstrucción espacial experimental.
- Los bloqueos científicos por datos experimentales incompletos y presupuesto/viabilidad de periodicidad/GCI siguen separados de esta aceptación de producto.
- Curvas exploratorias requieren sus artefactos originales; el CSV histórico reutilizable debe conservar su JSON compañero. Esto se verificó sin alterar contratos.
- En ventana compacta hay desplazamiento interno para parámetros avanzados y filas de tablas, y el explorador inferior ocupa espacio mientras está abierto; puede cerrarse. Perfil y tabla de escape se consultan en pestañas, sin scroll exterior redundante.

No quedaron defectos que impidan los recorridos solicitados. El siguiente paso es la revisión del candidato TRIAL por el dueño; no se publica, no se reconstruye ni se abre otra investigación de empaquetado.
