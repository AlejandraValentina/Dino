## Implementación
- [x] Leer orden y comprobar Git limpio, preservar rc1/rc2 y evidencia.
- [x] Navegación por tareas, ciclo, título y barra de estado.
- [x] Resumen real con ejecutabilidad y accesos a errores.
- [x] Geometría/formulario adaptables; workspaces Motor2T/4T y contexto.
- [x] Simulación jerarquizada, resultados integrados y series.
- [x] Comparación/externos integrados con estados progresivos.
## Comprobación y entrega
- [x] Conservar cobertura y añadir regresión específica UI.
- [x] Suite completa, OpenSpec estricto y revisión independiente puntual.
- [x] Windows multiescala/ancho: capturas realmente inspeccionadas.
- [ ] Commit fuente limpio, reconstrucción candidata, recorrido EXE.
- [ ] README/hoja de ruta/evidencia y commit final; sin publicar ni archivar.
## Pendientes preservados
Parada rc1 clasificada F, equipo sin Python, offline aislado, aceptación manual y
validación experimental no se cierran mediante este rediseño.

## Evidencia actual (16/09/2026)

Suite final: 238 pruebas aprobadas en 69,542 s, Qt offscreen explícito;
`build/windows/ux-suite-final.log`. Una corrida anterior se detuvo sin resultado
por falta de finalización; la corrida diagnóstica terminó aprobada. No se atribuye
un fallo de aplicación sin evidencia. OpenSpec1.3.1 estricto aprobado.
Capturas finales adicionales `100-final`, incluidas curvas completas de resultados
y externos, inspeccionadas después de las correcciones.

Revisión independiente de solo lectura por review_rc2_hardening, una pasada del
diff UX: tres hallazgos reproducidos y corregidos (atributos de diálogo en plot
externo; Escape ocultaba páginas embebidas; ejecutabilidad contaminada por borrador
del ciclo inactivo). Principal integró correcciones y pruebas focalizadas. También
se corrigieron enlaces de atención obsoletos y limpieza de resultados al abrir serie.
No se modificaron validadores científicos ni ejecución asíncrona.

Windows real automatizado con `tests/verify_workspaces_windows.py`; capturas/evidence.json
en `E:\MotorSim distribucion\UX final\100-1366`, `125-1366`, `100-1920`,
`100-900`, `150-900` y `150-final`. Se inspeccionaron Resumen, geometría,
ambos motores, simulación, resultados, barrido, comparación y externos/curvas.
Datos de prueba identificados y resultados históricos R2, sin nuevas integraciones.
100-1366 precede la corrección de enlaces; 150-final incluye correcciones de revisión.
1920 corresponde a ventana Qt de 1920×881 por límite del escritorio 1440×900,
capturada completa mediante QWidget.grab; no es captura de escritorio Full HD.
125 %: 1092×600 lógicos; 150 %: 900×520 lógicos. Foco/scroll local legibles;
sin scroll horizontal global. Mínimo640×480 cubierto por prueba UI.
No se atribuye aceptación manual de la usuaria. rc3 evita sobrescribir rc2 existente.
