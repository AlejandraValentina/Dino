## Implementación
- [x] Comprobar repositorio y referencia confirmada; preservar eliminación ajena de redme.txt.
- [x] Componentes/paleta compartidos y shell accesible.
- [x] Resumen, cuatro archivos como copia y preparación real.
- [x] Simulación/contexto/estados/gráficos y ocho vistas coherentes.
## Comprobación
- [x] Suite pertinente y OpenSpec estricto.
- [x] Windows visible 100/125/150 %, anchos representativos y capturas inspeccionadas.
- [x] Revisión independiente puntual y correcciones.
- [ ] Commit fuente, rc5 preservando rc1–4; recorrido EXE, dos puntos y cancelación.
- [ ] Comparación exacta con resultados preservados, documentación y commit evidencia.
## Pendientes
Aceptación manual final no atribuida; no archivar ni iniciar validación experimental.

## Evidencia de fuente (17/09/2026)
- Base e30356a2b3034f88e48e4aaa2d8b81d769a4dfae main; única modificación
  previa: eliminación ajena de redme.txt, preservada fuera del commit.
- Suite: 258 pruebas OK, 69,976 s; build/windows/cae-tests.log.
- Revisión independiente /root/review_rc2_hardening, solo lectura: encontró
  NameError en Detalles por bloque duplicado. Corregido; ocho pruebas CAE OK
  incluyen Detalles sin worker. 12 workspaces y 17 externos OK después de ajustes.
  La invocación inicial por módulos de dos suites falló por rutas de importación;
  se ejecutaron correctamente mediante unittest discover, sin cambios de producto.
- Validación: openspec validate implementacion-ui-cae-final --strict --no-interactive.
- Autorrevisión: capturas de Windows nativo bajo E:/MotorSim distribucion/UI CAE rc5.
  Se inspeccionaron Resumen 2T/4T, vacío, Simulación con histórico, motores,
  Geometría, Resultados, comparación y externos/curvas. Contexto lateral amplio,
  colapsado debajo en compacto; teclado y ausencia de scroll global en pruebas.
- Correcciones visuales: selector truncado, acción primaria sin fondo por cascada,
  altura de tabla y propagación de mínimos de panel. El capturador ahora espera
  eventos de layout antes de grabar, evitando capturas transitorias solapadas.
- Capturas no son aceptación manual ni ejecución nueva de los históricos R2.
  QWidget.grab sobre ventana Windows real. Monitor físico 1440×900: tamaño
  solicitado 1920×1080 limitado a 1920×881 lógicos; 1366×768 al125 % a1366×705;
  900×650 al150 % a900×587. Full HD físico permanece por verificar.
