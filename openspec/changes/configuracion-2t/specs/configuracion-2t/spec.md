## ADDED Requirements

### Requirement: Editor de lumbreras incompleto y persistente
El editor MUST permitir añadir, editar y eliminar filas individuales con nombre,
función Escape/Transferencia, distancia superior u, altura h y ancho desarrollado w.
MUST explicar origen en borde superior periférico del pistón en PMS, positivo hacia
abajo, no cara del cilindro/cúpula; ancho desarrollado, no cuerda. MUST identificar
rectángulos como aproximación. Datos nuevos incompletos MUST ser guardables con
null para números ausentes; números informados MUST ser positivos finitos con
coma/punto. Entrada inválida MUST conservarse y bloquear guardado sin volverse null.

#### Scenario: Edición y protección
- **WHEN** se añade, edita o elimina una lumbrera
- **THEN** se marca pendiente; guardar/reabrir conserva las filas, eliminar no reaparece y cancelar protege los cambios.

### Requirement: Eventos y área geométrica
La aplicación MUST reutilizar x del mecanismo sin descentrado y calcular
A=w*max(0,min(h,x-u)), entre 0° PMS y 180° PMI en rango 0–360°.
MUST mostrar apertura, cierre, duración, máximo efectivo y curva para la fila
seleccionada. Cruce MUST ser acotado y verificable, no muestra redondeada.
MUST NOT exigir compresión/cárter ni multiplicar por N. Eventos dependen de S/L/u;
área depende además de h/w. Faltantes, inválidos o incompatibles MUST retirar los
resultados afectados explicando su causa. La curva MUST identificarse como área
geométrica sobre pared, no flujo, caudal, barrido ni potencia.

#### Scenario: Caso sintético independiente
- **WHEN** S=56, L=100, u=32, h=10, w=20 mm
- **THEN** apertura=90°, cierre=270°, duración=180° y área máxima=200 mm².

#### Scenario: Parcial o sin apertura
- **WHEN** la carrera no descubre toda la altura o no supera u
- **THEN** el máximo usa la altura efectivamente descubierta; si u>=S se indica No se abre, ángulos ausentes, duración cero y área cero con dimensiones válidas.

### Requirement: Cárter y admisión pendientes
MUST existir volumen libre del cárter con pistón en PMI opcional, cm³ positivo finito,
de cárter individual sin conductos externos, con procedencia en observaciones.
MUST NOT deducirlo, calcular presión o compresión del cárter. Admisión MUST figurar
Pendiente de definición, sin eventos ni alternativas anticipadas.

#### Scenario: Cárter no informado
- **WHEN** falta volumen de cárter
- **THEN** la ficha puede guardarse y los cálculos de lumbreras no se bloquean.

### Requirement: Compatibilidad y límites de la sección
MUST añadir pestaña Configuración 2T conservando editor y gráficos Qt actuales.
En 4T MUST NOT calcular ni mostrar resultados 2T, conservando entradas al alternar.
JSON v3 MUST guardar solo entradas y referencia documentada; MUST leer v1/v2 sin
lumbreras/volumen informados y sin escritura automática. MUST conservar guardado
seguro, sobrescritura y protección de cambios. MUST NOT añadir admisión, perfiles,
puentes, válvula de escape, conductos o simulación.

#### Scenario: Alternancia y archivos antiguos
- **WHEN** se cambia a 4T y vuelve a 2T o se abre un archivo anterior
- **THEN** alternar conserva los datos; un archivo antiguo inicializa lista vacía y volumen null sin modificar bytes hasta guardar.

### Requirement: Evidencia del primer tramo
MUST registrar pruebas focalizadas, regresiones y comprobación Windows cuando sea
posible, separada de aceptación manual. MUST mantener entrega 3 En curso por admisión
pendiente, sin archivar ni comenzar entrega 4 o simulador.

#### Scenario: Entrega parcial explícita
- **WHEN** se registra este tramo
- **THEN** tasks y README distinguen implementación y pruebas de la admisión pendiente; commit separado y push normal solo si autenticación disponible.
