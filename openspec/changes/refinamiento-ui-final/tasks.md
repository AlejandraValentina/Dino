## Implementación
- [x] Comprobar main limpio5e6f474 y preservar rc3/rc4 previas.
- [x] Componentes visuales y navegación jerarquizada, encabezados y foco.
- [x] Resumen operativo y configuración geométrica/2T/4T contextual.
- [x] Simulación y resultados separados en paneles adaptables.
- [x] Comparar bilateral y externos secuencial con estados vacíos útiles.
## Comprobación
- [x] Suite/regresiones y OpenSpec estricto.
- [x] Inspección de ocho vistas en Windows100/125/150%, anchos representativos.
- [x] Revisión independiente puntual y correcciones afectadas.
- [ ] Commit fuente limpio y nueva rc4; recorrido EXE con punto/cancelación e históricos.
- [ ] README/ayuda/evidencia y commit final, sin publicar/archivar.
## Pendientes preservados
Aceptación manual final, escritorio físico1920×1080, equipo sin Python/offline
aislado y validación experimental separados de esta implementación.

## Evidencia obtenida en esta entrega (16/09/2026)
Automáticas: `.venv\Scripts\python.exe -m unittest discover -s tests`, 247
aprobadas en 36,169 s; log `build/windows/refinement-tests-approved.log`.
Conserva las 245 anteriores y añade estados vacíos/procedencia y columnas compactas.
Incluye navegación/ciclo, borradores, errores, cierre/cancelación, proceso activo,
consulta sin worker, ejemplos y persistencia. No son aceptación visual/manual.
`openspec validate refinamiento-ui-final --strict --no-interactive`: aprobado.

Windows visible automatizado: `tests/verify_workspaces_windows.py`, históricos R2
existentes y datos externos identificados sintéticos, sin nuevas integraciones.
Capturas reales `E:\MotorSim distribucion\Refinamiento UI`: `final-100-1366`,
`final-125-1366`, `compact-150-900`, `final-100-1920`. Ocho vistas inspeccionadas
en cada escala; 18 capturas por recorrido incluyendo vacíos y curvas desplazadas.
Se corrigieron botones sin texto, expansión vertical de Resumen, ancho mínimo
que impedía apilar, separación excesiva de derivados y procedencia sin resultado.
1920×1080 solicitado resulta 1920×881 Qt al 100 %; 1366×768 al 125 % resulta
1366×705 lógicos; 900×650 al 150 % resulta 900×587. El sistema limita la altura
al monitor físico 1440×900. Capturas QWidget.grab: Windows nativo, no offscreen,
pero no prueban una pantalla física 1920×1080. Desplazamiento vertical local
permite consultar el contenido; las tablas conservan su desplazamiento propio.

Revisión independiente: `/root/review_rc2_hardening`, solo lectura, sin defectos
concretos identificados; 12 pruebas workspaces aprobadas y dos capturas inspeccionadas.
Autorrevisión del principal: diff UI, todas las vistas/escala y separación de
estados. El ajuste posterior de altura de los motores se comprueba de forma focalizada.
Comprobación focalizada final: 12 pruebas aprobadas en 2,881 s y capturas renovadas
en `release-100-1366`, `release-125-1366`, `release-150-900`; motores inspeccionados
en las tres escalas. Se aprovecha la altura disponible sin aumentar el mínimo compacto.
