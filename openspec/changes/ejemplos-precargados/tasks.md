## Implementación
- [x] Comprobar main limpio, rc3 y referencias canónicas; preservar evidencia.
- [x] Definición común de cuatro ejemplos e identificación sintética.
- [x] Menú de carga protegida, proyecto editable sin ruta, origen de simulación real.
- [x] Integrar los cuatro JSON en empaquetado rc4 sin cambiar formatos.
## Comprobaciones
- [x] Pruebas de campos, variantes, dirty/ruta, guardado y cancelaciones.
- [x] Entradas 2T/4T y comparación por fixtures/históricos sin integrar.
- [x] OpenSpec estricto y revisión puntual.
- [ ] Commit limpio y candidata rc4; recorrido/captura real del EXE.
- [ ] README/ayuda y registro final de evidencia, sin publicar ni archivar.
## Pendientes
Aceptación manual final y pendientes históricos de distribución/validación
experimental conservados; no se cierran mediante ejemplos sintéticos.

## Evidencia
Git inicial limpio en main,343818a; remoto origin conservado, sin operaciones de red.
Suite completa:245 pruebas aprobadas en29,941s (`build/windows/examples-suite.log`).
Después se actualizó la cabecera de preparación cuando el origen ya era Proyecto
actual:7 pruebas específicas aprobadas en6,426s, incluidas entradas efectivas.
OpenSpec1.3.1 estricto aprobado. Revisión independiente de solo lectura por
review_rc2_hardening, sin hallazgos concretos:6 pruebas y proceso DiagnosticProcess
comprobaron conservación de ejecución activa al cargar otro ejemplo. Sin física.
El principal conserva la responsabilidad y probó además fallo/cancelación de guardado.
Comparación 2T/4T con fixtures explícitos:única diferencia geométrica compresión;
no constituye convergencia ni evidencia experimental.
