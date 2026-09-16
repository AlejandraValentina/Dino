## Implementación y construcción
- [x] Leer orden, Git limpio main y preservar 18194d7/da27ee25; registrar único cambio.
- [x] Centralizar comando fuente/paquete, errores, recursos y diagnóstico.
- [x] Acerca de, ayuda breve y ejemplos generados desde referencias.
- [ ] Entorno aislado fijado, receta/spec, avisos/licencias y commit fuente.
- [ ] Construcción Windows x64 onedir y ZIP desde referencia limpia.
## Comprobación
- [ ] Suite pertinente y revisión puntual de contratos de distribución.
- [ ] Extraer fuera del repo; verificar rutas reales GUI/worker, cwd/entorno independientes.
- [ ] Recorrido del ejecutable: persistencia, inválidos, alternancia, protección y antiguos.
- [ ] Referencia/proyecto, proceso único, cancelación/cierre, errores controlados y procedencia.
- [ ] Lectores/comparación/barrido/importación/CSV con evidencia histórica.
- [ ] Tres puntos completos comparados con referencias; tiempos/budget acumulados <=300 s.
- [ ] Capturas reales 150 % y compacto; inspección separada de pruebas.
- [ ] ZIP final/SHA256/tamaño, README/hoja de ruta y commit de evidencia.
## Pendientes separados
- [ ] Equipo Windows sin Python instalado, solo si existe entorno autorizado.
- [ ] Uso realmente sin conexión, solo si existe aislamiento sin afectar sesión.
- [ ] Aceptación manual de la usuaria; no atribuida a automatización.
- [ ] Validación experimental; fuera de este encargo.

## Registro de preparación
16/09/2026: Windows 10 19045 AMD64, Python 3.11.0 x64. Entorno .venv-build
independiente, PySide6 6.11.2 y PyInstaller 6.22.3; versiones completas fijadas.
224 pruebas aprobadas (36,193 s), incluidos cinco controles de distribución sin
integraciones. Revisión independiente puntual review_windows_distribution:
sin defectos reproducibles; no acredita el protocolo final aún pendiente.

Paquete trial explícitamente marcado source_dirty/trial construido desde trabajo
posterior a da27ee25, abierto directamente fuera del repo con recursos y ejemplos.
Detectado y corregido nombre ZIP truncado por with_suffix sobre versión con puntos;
no hubo ejecuciones físicas ni cambios de modelo. Automatización externa UIA usa
HWND del proceso y teclado para diálogos Qt: evita bloqueos de Invoke modal.
Recorrido trial de editor: guardar incompleto/Guardar como Unicode, rechazar texto
inválido, Cancelar/Descartar cambios, alternar ciclos, leer v1 sin reescribirlo.
Evidencia trial: E:/MotorSim distribucion/Prueba á rc1/Comprobación (no final).
Herramientas UIA son solo de prueba, excluidas del paquete. Ayuda y licencias se
incluyen; no se asignó licencia nueva al código MotorSim.
