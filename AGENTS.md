# MotorSim — Instrucciones de trabajo para Codex

## Lectura y autoridad

Leer README.md y el cambio solicitado dentro de `openspec/changes/` antes de
modificar archivos. `base-escritorio` es la entrega inicial; su límite de nombre,
tipo y archivos pertenece a esa entrega. El cambio autorizado actual es
`simulacion-2t`: proposal.md, design.md, specs/simulacion-2t/spec.md y tasks.md.
Entregas 1 y 2 completadas y aceptadas por la usuaria; 3 y 4 comprobadas técnicamente
sin aceptación manual atribuida. Se preserva el trabajo existente y se comprueba Git.
Entrega 5: modelo/caso/protocolo de `simulacion-2t/design.md` aprobados expresamente
para implementar y ejecutar únicamente el prototipo de consola de viabilidad.
Biblioteca estándar, controles elementales antes del caso y tres resoluciones
con los límites previos. Sin integración Qt, cambios JSON, ondas ni barridos.
Realizar revisión puntual y pruebas afectadas; commit propio y un push normal,
sin reintentos de autenticación ni configuración global. No iniciar entrega 6.
No alterar retrospectivamente requisitos ni verificaciones de entregas anteriores.

La [hoja de ruta](docs/HOJA_DE_RUTA_MotorSim.md) define el orden, los objetivos y
las exclusiones; la especificación del cambio activo define requisitos y aceptación.
Su `tasks.md` es el único listado detallado de tareas. La sección «Estado de avance»
de la hoja resume las entregas, sin duplicar ese listado.
Al retomar una sesión, leer esos archivos y README, contrastarlos con código y
pruebas y continuar lo pendiente; no reiniciar ni generar planificación equivalente.
Una entrega autorizada permite avanzar por sus tareas, archivos y pruebas sin
pedir permiso para cada paso. La siguiente entrega requiere nueva autorización.
No inventar decisiones de producto o física que la hoja deje abiertas: informar
la decisión pendiente y detener únicamente el trabajo que dependa de ella.

La usuaria decide alcance y autorización. Estos archivos no inician tareas por
sí mismos. Una petición documental solo autoriza documentación; implementar la
aplicación requiere una petición explícita. No interpretar «documentos completos»
o «ready to apply» de OpenSpec como autorización ni como código terminado.

Los requisitos observables tienen una única fuente: la especificación del cambio
activo. Tras un cierre autorizado, las especificaciones consolidadas estarán en
`openspec/specs/`. La ruta antigua en docs/ es una referencia, no requisitos
alternativos. Si hay una contradicción material nueva, identificarla y no ampliar
silenciosamente el alcance ni escoger la interpretación más exigente.

## Responsable y coordinación

Un Codex principal implementa, prueba e integra el cambio. También coordina el
trabajo: no se construye un orquestador externo, servicio de agentes ni plataforma
multiagente. Hay un único escritor de código por tarea. La elección del modelo
(Astra u otro disponible) pertenece a la configuración del entorno de la usuaria;
no se codifica ni modifica en MotorSim.

Se realiza una revisión puntual al terminar, preferentemente en otra sesión o
con un subagente de solo lectura si está disponible. No requiere agentes
permanentes ni bloquea el trabajo por no disponer de subagentes. Sin revisión
independiente, hacer una pasada separada y declararla como autorrevisión, no como
auditoría independiente. El principal conserva la responsabilidad de integrar.

## Code Review Rules

Revisar únicamente el diff del cambio, su especificación y evidencia de pruebas.
Informar defectos reproducibles, pérdida de datos, requisitos incumplidos o una
comprobación necesaria ausente. Cada hallazgo debe indicar archivo/ubicación,
requisito afectado y reproducción o razonamiento concreto. No inventar evidencia.

Separar defectos de mejoras opcionales. Estas últimas no bloquean la entrega ni
se convierten en requisitos. El revisor no modifica código ni requisitos; el
principal corrige los defectos y vuelve a comprobar lo afectado. No encadenar
revisores o rondas generales indefinidas: ante un bloqueo persistente, entregar
el estado verificable y el impedimento concreto sin declarar éxito.

## Flujo y límites

- Trabajar solo sobre el cambio solicitado; no generar otro plan, otra auditoría
  general ni una etapa futura para ejecutar la tarea actual.
- Mantener tasks.md como único registro detallado de avance. Marcar tareas únicamente con
  evidencia de ejecución; no confundir preparación documental con implementación.
- Respetar la especificación del cambio autorizado. En `base-escritorio` el alcance
  era solo nombre, tipo y archivos, sin geometría. `caracteristicas-motor` incorpora
  ficha y cilindrada geométrica; no autoriza simulación física, rendimiento,
  gráficas ficticias ni arquitectura de solvers.
- Elegir pocos módulos, Python estándar y PySide6. Mantener datos y
  archivos separables de los widgets. No añadir dependencias preventivas.
- No importar código, contratos, fases o infraestructura de proyectos anteriores.
- No modificar requisitos o aceptación para ocultar un fallo o facilitar el cierre.
- Usar comandos con salida y límites de ejecución razonables. No repetir una
  operación bloqueada sin hipótesis nueva; no dejar procesos duplicados o esperas
  indefinidas. Entregar lo verificado y la limitación del entorno.
- No sincronizar specs ni archivar el cambio por el solo hecho de completar
  documentos. Archivar únicamente con trabajo comprobado y cierre autorizado.
- Al completar el cambio autorizado, detenerse. La física requiere otra definición.

## Cuidado del repositorio y entrega

Preservar cambios ajenos, comprobar el estado de Git antes de editar y no
reescribir historia ni descartar trabajo para resolver diferencias. No subir
credenciales, entornos virtuales o datos personales. No modificar configuración
global de Codex, permisos o preferencias del equipo sin autorización específica.
No codificar `E:\dino` como ruta de aplicación.

Actualizar README con instrucciones reales de instalación, ejecución y pruebas
cuando existan. Distinguir pruebas automatizadas, recorrido manual de Windows,
revisión y comprobaciones pendientes. Una prueba sin pantalla no valida Windows.

La entrega informa brevemente archivos cambiados, comprobaciones ejecutadas y
resultados, pendientes y referencia Git. No requiere otro informe obligatorio.
No declarar que funciona el simulador por haber terminado su base de escritorio.

Referencia del formato: https://developers.openai.com/codex/guides/agents-md
