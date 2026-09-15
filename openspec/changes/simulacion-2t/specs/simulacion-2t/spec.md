## ADDED Requirements

### Requirement: Definición documental y límite de autorización
Esta tarea MUST entregar un solo modelo recomendado, caso sintético y experimento
acotado en design.md, diferenciando datos, parámetros, derivados y aproximaciones.
MUST NOT implementar solver, interfaz, formato JSON, dependencias ni ejecutar
simulaciones. MUST preservar entrega 4 y evidencias previas sin repetir sus pruebas.
La entrega 5 MUST figurar En curso: definición del primer caso, no implementada.
Los requisitos de prototipo siguientes son criterios propuestos para una fase
posterior, condicionados a aprobación física y autorización explícita de código.

#### Scenario: Preparación válida
- **WHEN** OpenSpec aprueba la estructura documental
- **THEN** se registra únicamente validación de documentos; solver, evidencia numérica y resultados físicos siguen pendientes y no autorizados.

### Requirement: Un modelo abierto con límites explícitos
El diseño MUST definir balances de masa, energía y carga fresca/residual, cierre
del gas, estados/contornos, flujo reversible con área efectiva declarada, aporte
energético, calor/pérdidas, volumen variable del cárter y circuito fijo. MUST citar
fuentes primarias y diferenciar decisiones propias de afirmaciones sustentadas.
MUST explicar el papel efectivo de longitudes/diámetros y la conexión de
transferencias; no deducir almacenamiento completo de las ventanas existentes.
La propuesta 0D sin inercia/ondas MUST identificarse como reducción de capacidad
pendiente de aprobación, sin sintonía ni etiqueta 1D.

#### Scenario: Evaluación del alcance del escape
- **WHEN** se revisa el modelo antes de autorizar el núcleo
- **THEN** se conoce que solo representa volumen agregado y restricción concentrada, no propagación/reflexión ni efecto del orden de conos a igual volumen/área limitante; diferir ondas requiere aprobación expresa.

### Requirement: Caso reproducible y referencias independientes
El diseño MUST fijar un único monocilíndrico 2T atmosférico de chispa y falda,
geometría completa, régimen/condición, p absolutas/T, estados iniciales,
coeficientes y parámetros energéticos. MUST identificar valores como sintéticos,
sin motor real ni mediciones, indicar claves v5 reutilizadas y entradas adicionales
sin cambiar archivos/proyectos. MUST definir controles analíticos independientes,
resoluciones, balances, convergencia y presupuestos antes de ejecutar.

#### Scenario: Datos adicionales ausentes del editor
- **WHEN** se entrega esta definición
- **THEN** estados, contornos, Cd y energía quedan documentados en el caso, sin agregarlos a JSON ni precargar proyectos de la usuaria.

### Requirement: Observación del futuro prototipo condicionado a aprobación
Después de autorización independiente, el prototipo MUST evaluar el circuito
abierto completo; MUST informar p_C(theta), P-V, W indicado por ciclo y estados,
flujos/retornos y balances definidos en el diseño, con caso/resolución identificados.
Un cierre geométrico MUST bloquear flujo; invertir presión MUST invertir donante,
entalpía y fracción fresca. MUST NOT ocultar estados no físicos, recortarlos para
continuar ni presentar ausencia de convergencia como resultado aceptado.
El calor prescrito y la mezcla ideal MUST distinguirse de combustión/barrido
predictivos. MUST NOT inferir potencia al eje, consumo, emisiones o detonación.

#### Scenario: Cálculo elemental cerrado
- **WHEN** una prueba adiabática cerrada o de calor a volumen fijo aprueba
- **THEN** acredita solo ese balance elemental, no el ciclo 2T con intercambio de gases ni el coste del sistema completo.

### Requirement: Viabilidad futura acotada y trazable
La futura prueba MUST aplicar el protocolo de design.md con tolerancias previas,
control de estados/balances, comparación de resolución y evolución entre ciclos.
MUST medir tiempo/memoria del proceso completo, informar progreso y terminar por
cancelación, fallo, ciclos/tiempo/memoria o falta de convergencia sin reintentos
indefinidos. MUST NOT relajar umbrales después de un fallo para declarar éxito.
El objetivo temporal de la hoja MUST seguir siendo una meta hasta medirlo.

#### Scenario: Presupuesto agotado
- **WHEN** se alcanza cualquiera de los límites previamente fijados sin cumplir criterios
- **THEN** la futura ejecución termina con causa y evidencia parcial marcada no aceptada, sin afirmar viabilidad ni iniciar campañas adicionales.

### Requirement: Registro documental y parada
MUST usar proposal/design/spec/tasks del único cambio, con referencias mínimas
de estado en documentos existentes. MUST separar tareas documentales realizadas
de aprobación y prototipo no autorizados, validar OpenSpec y crear commit propio.
MUST NOT reintentar la autenticación bloqueada, cambiar configuración global,
archivar cambios o iniciar entrega 6. La entrega MUST identificar decisiones
pendientes antes del núcleo y no pedir aceptación de una implementación inexistente.

#### Scenario: Fin de esta tarea
- **WHEN** se registran documentos y commit
- **THEN** se entrega modelo/caso/viabilidad propuesta y aprobaciones pendientes, conservando la entrega 5 en definición y deteniendo el trabajo antes del solver.
