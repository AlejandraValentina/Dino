# Diseño del programa

Este cambio es el registro durable único de `MOTORSIM_2T_COMMERCIAL_CORE`; no
reemplaza ni edita contratos históricos. Los componentes nuevos se separarán en
módulos tipados con esquema/versionado explícito, conservarán su configuración
primaria y provenance, y se conectarán a la integración P5-C/P6 existente cuando
la topología del componente sea compatible. No se duplica el solver 1D.

El harness de referencia continúa independiente de anchors P8 y de E13
histórico. Su contrato congelado actual conserva CFL 0,4, 400 ciclos y los
umbrales ya preregistrados. El bloqueo KT100 actual ocurre en la frontera de
reservorio existente; ninguna fase posterior puede cambiarla de forma implícita
ni reclasificar los recibos r5. Las fases independientes pueden avanzar con
fixtures analíticos y evidencias propias.

Toda métrica nueva documenta ecuación, dominio, unidades, especies/ledgers de
origen y comportamiento ante denominadores cero antes de usarla en campañas.
Todo estado persistente importante prueba round-trip, restart y replay. La
configuración experimental P9 permanece pendiente de datos y se mantiene fuera
de la ejecución automática.

## Fases y dependencias

Las fases se registran en `tasks.md`. Un bloqueo local conserva su evidencia y
permite continuar fases independientes. `Commercial Core Ready` requiere la
integración completa definida por la autorización de la usuaria, incluidos dos
casos de referencia trazables; un módulo aislado no satisface ese gate.

## Geometría de puertos `GENERIC_2T_PORTS_V1`

La primera capacidad se implementa como configuración JSON independiente del
Project v6: los proyectos históricos conservan su esquema y cálculos actuales.
La configuración identifica conductos por `id`/rol y lumbreras por `id`, rol,
función geométrica, coeficiente de descarga y provenance. Una lumbrera bridged
se representa como sus aperturas individuales con un `group_id` común; las
áreas se suman por conducto sin fingir que el puente es otra ventana.

Las ventanas rectangulares usan posición axial desde PMS, positiva hacia PMI,
mm desarrollados y `piston_position` existente. Para transfer/escape,
`Aeff=Cd*w*max(0,min(h,x(theta)-top-roof_travel*position))`. Para piston-port
intake se reutiliza `intake_results`: `d=top+h-skirt`,
`Aeff=Cd*w*max(0,min(h,d-x(theta)))`. El coeficiente es una entrada positiva
finita; no se estima ni calibra. Perfil explícito: knots finitos 0–360°,
estrictamente crecientes, área no negativa, extremos idénticos; evaluación
piecewise-linear, periódica. Los perfiles explícitos se reservan a aperturas de
escape; transfer e intake conservan geometría de ventana/piston-port. Muestreo
derivado a cada grado inclusive sirve para visualización/persistencia, mientras
el evaluador continuo y los eventos exactos
son la fuente para integración futura.

La serialización incluye SHA-256 canónico de geometría/config y de perfiles
derivados; al leer se regeneran y comparan los perfiles. Estos hashes prueban
binding/integridad del artefacto, no son evidencia física. El coeficiente y el
área no se conectan al P5-C histórico en este primer tramo; integración con
topología variable requiere un adaptador nuevo y pruebas de ledgers por ducto.
