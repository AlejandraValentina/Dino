# MotorSim — Instrucciones de trabajo para Codex

## Lectura y autoridad

Orden más reciente: `p1-r3-fronteras`. P1_R3_PASS_BOUNDARIES_SEPARATED:
contrato1D_CONTRACT_V1_R3 adoptado antes del código; T05 PASS y NR01 diagnóstico.
P2A revalidado completo: T01–T10/T12 PASS, T11 FAIL (amplitud CFL0,6 frente0,2:
0,08336382706 >0,08). 52 casos individuales PASS no acreditan P2A.
STOP P2A BLOCKED, revisión independiente coincide;3/3 reparaciones consumidas.
No más fixes, cambios de umbral/CFL, P2B ni P3 sin nueva decisión autorizada.
Human gate de P2 pendiente. Conservar v1/R2, T02/T06, baseline0D e históricos.
Sin publicar, archivar ni modificar UI/JSON/EXE/configuración global.

Antecedente histórico:
Orden más reciente: `p1-r2-contacto`. P1_R2_PASS_CONTACT_OBSERVABLE adopta
1D_CONTRACT_V1_R2 sin alterar v1/T06. P2A NO reanudado: T05 tiene ramas
incompatibles, SCIENTIFIC_CHANGE_REQUIRED. Excepción de velocidadcero retirada;
solo fixes de contabilidad y exterior no reflectivo retenidos. No iniciar P2B/P3
ni modificar BC sin nueva decisión científica. Ver tareas y evidencia del cambio.

Antecedente: `p1-r1-contacto`, etapa P1_R1_SCIENTIFIC_AMENDMENT.
Estudio acotado del observable T02, sin cambiar solver ni P1 congelado.
Resultado P1_R1_CONTACT_ACCURACY_UNRESOLVED: B supera2dx en N400; STOP.
Sin R1 adoptado ni autorización efectiva de fixes P2, T05, P2B o P3.
Las órdenes siguientes conservan su valor histórico; ver tareas del cambio.

Orden vigente: `p2-nucleo-gas1d`. P1_HUMAN_ACCEPTED; contrato P1 congelado.
Implementar/verificar únicamente P2 aislado mediante dev_orchestrator. P2A
first-order precede obligatoriamente a P2B MUSCL/SSP-RK2 con gate y revisión.
Máximo3 reparaciones de implementación, nunca cambiar P1 para pasar. Sin UI,
JSON, acoplamiento 0D, EXE ni P3. P0 y producción anterior conservan hashes.

Antecedente histórico:
Orden vigente: `p1-contrato-gas1d`. Registrar P0_HUMAN_ACCEPTED sin modificar
baseline congelado; ejecutar solo P1 contractual por dev_orchestrator, con cero
reparaciones automáticas y revisión independiente de solo lectura. Sin solver,
UI, JSON de producto, paquetes ni P2. P2–P9 permanecen deshabilitadas. El rango
público 2T 2500–15000 aprobado en d2932da se conserva; no confundirlo con el
estado histórico de P0. Documentos normativos: docs/gasdynamic y cambio P1.
Las órdenes siguientes son históricas y no sustituyen esta autorización.

Orden actual: `positividad-transporte-2t`, candidato conservativo de especie por
etapa RK4, microcasos, campaña baja y regresión histórica; alta RPM solo tras gate.
Mantener física, tolerancias, mínimo, donor, dominio público y candidatas. Integrar
en producción únicamente si aprueba conservación, invariantes e intervención.
Sin clipping, regularización interna, 1D ni cambios de dev_orchestrator.
La infraestructura anterior está registrada en e739cfd/bd0a119 y queda separada.

## DEV ORCHESTRATOR

dev_orchestrator/ es infraestructura de desarrollo y no forma parte del producto ni
del paquete distribuible. El código de motorsim/ no debe depender de ella.

- No incluirla en PyInstaller ni ZIPs; sin dependencias runtime nuevas.
- Puede leer tests/results/specs y ejecutar checks autorizados, no modificar física.
- Detenerse ante SCIENTIFIC_CHANGE_REQUIRED; no cambiar contratos para aprobar.
- Reparaciones/reintentos acotados; sin agentes externos ni encadenamiento autónomo.
- Revisor de solo lectura; el stub dummy no acredita revisión científica independiente.
- Registrar cambios previos, no borrarlos ni atribuirlos a la ejecución.
- No archivar, publicar, modificar configuración global ni empaquetar en esta tarea.

## Órdenes anteriores conservadas

Orden posterior a fase A bloqueada: mapear1500/1750/2000/2250/2500/2750/3000
y diagnosticar1000/2000 mediante observación y análisis offline. Mantener solver,
perfil, positividad, mínimo y dominio público. Sin warm-start, campaña alta/4T,
corrección, candidata ni archivo. Revisión independiente puntual de instrumentación
y conservación. El diagnóstico de2000 puede compartir la ejecución del mapa.

Continuación actual de `rendimiento-indicado`: campaña candidata 2T 1000–15000,
ocho RPM obligatorias, mismo perfil B/100 Pa y solver. Separar validación por
ciclo; 4T permanece 2500–3500. Fase B (29 puntos, UI ampliada y exploración
superior) solo después de GO numérico. No cambiar física para superar fallos.
Registrar fase A y decisión antes de empaquetar; sin publicar ni archivar.

Orden actual: `rendimiento-indicado`, derivación de potencia/par indicados desde
W_C/ciclo/RPM de resultados validados. Vista CAE y CSV nuevos; rc6 si aprueba.
No física, solver, pérdidas mecánicas ni valores al eje. Reutilizar históricos,
sin nuevas integraciones; revisión puntual, commits locales, sin publicar/archivar.

Corrección UX rc6 autorizada: Rendimiento asociado al proyecto, reutilización
automática compatible y CTA explícita que invoca el barrido existente. Esta orden
sustituye el límite de solo consulta para esa vista. Comprobar cálculo, cancelación
y capturas Windows sin campañas generales. No empaquetar rc7 en esta tarea;
mantener física, fórmulas, formatos y candidatas anteriores.

Continuación posterior a d15ec98: controles RPM permanentes y recálculo repetible.
Conservar la curva anterior al recalcular/cancelar/fallar, separar compatibilidad
del motor y del plan RPM. Recorrido explícito de tres cálculos y cancelación por
ciclo 2T/4T autorizado; no rc7, cambios numéricos ni campañas adicionales.

Orden actual: `implementacion-ui-cae-final` traslada la referencia visual confirmada
`Desktop/code.html` a Qt Widgets y prepara rc5. Mantener modelos, contratos,
worker, formatos y candidatas anteriores. Pruebas UI, dos puntos 2T/4T y
cancelación; revisión puntual independiente, commits locales sin publicar/archivar.

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
