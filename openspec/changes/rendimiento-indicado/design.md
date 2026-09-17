## Decisiones
Corrección UX rc6: las decisiones originales de solo consulta abajo describen la
primera candidata. Ahora la vista detecta compatibilidad mediante configuration_key
y source_path de la procedencia; no usa curvas ajenas como actuales. La apertura
manual conserva el histórico explícitamente identificado hasta cambiar el proyecto.
SimulationView conserva el barrido de sesión; PerformanceView solo referencia el
objeto validado. Las entradas RPM se sincronizan con sus controles existentes;
Calcular rendimiento delega en start_performance → start, sin duplicar ejecución.
Señales pequeñas de contexto/actividad/idle actualizan la vista. Solo se grafican
resultados validados al terminar; progreso toma eventos existentes del worker.
Se conserva el destino de finalización para no sacar al usuario de Rendimiento.
Esta corrección no requiere una nueva candidata antes de mostrar evidencia fuente.

Decisiones de la primera candidata:
Función pura de W_C, RPM y ciclo guardados: 2T P=W_C*rpm/60,T=W_C/(2*pi);
4T P=W_C*rpm/120,T=W_C/(4*pi). Acepta trabajo finito (incluido negativo), RPM
finitas positivas; entradas de aplicación siguen validadas por lectores actuales.
Sin redondear datos ni modificar fuentes. CSV en W/N·m; UI en kW/N·m.
Rendimiento lee load_sweep y puede reutilizar el barrido cargado. No depende del
editor ni crea procesos. Cada punto convergido usa su propio resultado y ciclo;
rechazar mezcla de ciclos. Estados no convergidos conservan huecos y cortan segmentos.
QPainter para gráfico combinado de dos escalas y secundarios, puntos/segmentos
rectos, clic y tabla accesibles. Se reutilizan Header/Panel/Columns y QSS.
Derivados de Comparar se añaden después de aprobar las mismas reglas existentes.
## Comprobación
Analítica independiente 2*pi/4*pi a3000rpm, invalidación, históricos, fallidos,
inversión A/B y CSV. Suite conservada; Windows/EXE con barridos2T/4T históricos.
No ejecutar solver. rc6 desde fuente limpia, preservar rc5 y evidencia. Aceptación
manual pendiente; revisión puntual según AGENTS, sin archivar ni publicar.
