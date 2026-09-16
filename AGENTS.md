# MotorSim — Instrucciones de trabajo para Codex

## Lectura y autoridad

Continuación actual de `ejemplos-precargados`: cuatro JSON físicos v6 versionados
en examples/projects, generador canónico, carga real y próxima candidata con
los mismos archivos. Sin solver ni campañas; conservar menús y paquetes previos.

Orden actual: `refinamiento-ui-final`, solo presentación/flujo en ocho workspaces.
Preservar física, worker, formatos, reglas y todas las candidatas/evidencias.
La nueva rc4 se distingue por commit, sin sobrescribir la rc4 de ejemplos ni rc3.
Pruebas UI, históricos y un punto/cancelación breve del paquete; sin campañas.
Una revisión independiente puntual; commits locales, sin publicar ni archivar.

Orden actual: `ejemplos-precargados` añade cuatro proyectos sintéticos desde las
referencias canónicas y su carga protegida; candidata rc4 conservando rc3.
Sin cambios físicos/formatos ni campañas. Se permite usar resultados existentes
para comprobar el paquete. Revisión puntual y commits locales, sin publicar/archivar.

Orden actual: `reorganizacion-ui-final` autoriza únicamente arquitectura visual UX,
reutilizar editores/controladores, navegación por tareas y análisis embebido.
Preservar física, contratos, worker, candidatos rc1/rc2 y evidencia. Leer el cambio.
Pruebas UI y paquete final con un punto/cancelación breve, sin campañas científicas.
Revisión puntual independiente, commits locales sin publicar ni archivar.

Leer README.md y el cambio solicitado dentro de `openspec/changes/` antes de
modificar archivos. `base-escritorio` es la entrega inicial; su límite de nombre,
tipo y archivos pertenece a esa entrega. El cambio autorizado actual es
`cuatro-tiempos-basico`: proposal.md, design.md, specs/cuatro-tiempos-basico/spec.md y tasks.md.
Continuación autorizada: `distribucion-windows` es ahora el cambio activo.
Leer sus proposal/design/spec/tasks. Preparar candidata 0.1.0-rc1 Windows x64
PyInstaller onedir con GUI y worker, probar el ZIP extraído y registrar evidencia.
Esta orden sustituye exclusivamente la prohibición de empaquetar: sin ampliar física,
publicar, etiquetar o archivar. Preservar 18194d7/da27ee25 y evidencia anterior.
Tres puntos completos de regresión (2T B3000 y barrido 4T B2500/3000), cancelaciones
breves y máximo conjunto 300 s de integración; no repetir campañas científicas.
Los presupuestos R2 siguientes son históricos, no el presupuesto de distribución.
Hardening autorizado: preservar rc1/f46613e y d6f0c63; corregir tiempos futuros y
defectos concretos de distribución. Si cambia código, construir rc2 limpia. Máximo
una reproducción focalizada de parada y un punto B100/3000 por ciclo 2T/4T;
sin campañas. Clasificar causa sin inventar evidencia; revisión independiente puntual.
Bloque autorizado de entregas 7 y 8: configuración 4T, JSON v6, modelo de tres
volúmenes I/C/E, ejecución e integración condicionadas a los criterios numéricos.
Preservar 6cbed360 y toda evidencia anterior. Entrega 6 conserva herramientas
implementadas y mediciones/validación experimental pendientes, sin bloquear 4T.
La prohibición anterior de iniciar 7 queda sustituida por esta autorización.
Perfiles/tolerancias/física fijados por la orden; máximo 12 ejecuciones previstas,
720 s de integración conjuntos, 60 s por punto. No lanzar etapas dependientes
si falla su condición previa; continuar las independientes. Un único cambio.
Continuación R2 autorizada: vía de estabilidad práctica definida en design.md;
preservar R1 fallida, af11976/b862900 y evidencia. Reutilizar A/B/C sin integrar.
Continuar C50 e integración/protocolo si sus condiciones aprueban, sin reiniciar
los 51,125 s consumidos del presupuesto conjunto.
Commits locales lógicos sin publicar, sin autenticación/configuración global.
No archivar ni ampliar física fuera del bloque autorizado; empaquetado según la continuación anterior.
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
