## Context
Un cilindro de referencia, sin multiplicar áreas o volúmenes por N. Se reutiliza
piston_position de kinematics.py y GeometryPlot; no se rehace el editor.

## Decisions
- Lumbrera rectangular idealizada descubierta por el borde superior periférico
  del pistón. u se mide hacia abajo desde ese borde en PMS, no desde la cara del
  cilindro ni una cúpula. h en mm; w en mm desarrollado sobre la pared, no cuerda.
- A(θ)=w*max(0,min(h,x(θ)-u)), mm². PMS 0°, PMI 180°, rango 0–360°.
  Apertura se calcula por bisección de x(θ)=u en [0,180], 60 iteraciones acotadas
  (resolución angular muy inferior a 1e-9°). Cierre=360-apertura; duración=cierre-apertura.
  No se redondea a muestras; la curva es una muestra por grado solo para dibujo.
- Si u>=S: no hay apertura efectiva, ángulos ausentes, duración=0. Máximo efectivo
  w*max(0,min(h,S-u)), no siempre w*h. Se reutiliza requisito L>S/2 del mecanismo.
- Eventos dependen de S/L/u; áreas además h/w. Nombre y función identifican la fila,
  no alteran el cálculo. Ni diámetro, compresión, N ni volumen de cárter intervienen.
  Errores, ausencia e incompatibilidad se explican por resultado. Valores fuera
  del rango numérico no se presentan como datos ausentes ni se corrigen al guardar.
- Datos incompletos guardables: nombre vacío, función null sin elegir, dimensiones
  null. Función informada es escape o transfer. Números informados positivos finitos;
  coma/punto aceptados con el parser existente. Texto inválido permanece en el editor
  y bloquea guardado, incluso al cambiar de fila o temporalmente a 4T.
- Volumen libre de cárter en PMI: cm³, individual, sin conductos externos. Opcional,
  positivo finito; procedencia en observaciones existentes. No se deduce ni calcula.
- JSON plano v3 conserva claves v2 y añade ports (lista), crankcase_volume_bdc_cm3
  (número/null), two_stroke_reference (identificador fijo `rectangular-peripheral-tdc-developed-bdc-v1`).
  Cada port guarda name (texto), function (escape/transfer/null), top_mm, height_mm,
  width_mm (números/null). Todas estas claves se requieren en v3; referencia distinta
  se rechaza para no interpretar medidas bajo otra convención. Lectura v1/v2 deja
  lista vacía y volumen null; abrir no escribe. No se guardan curvas/eventos.
- La pestaña muestra lista y editor de la selección, botones Añadir/Eliminar,
  resultados y área con gráfico existente. En 4T se oculta editor/resultados y se
  retienen los datos en memoria y JSON. Seleccionar una fila no marca cambios;
  añadir/editar/eliminar sí. No se agrega un sistema de admisión.

## Risks / Trade-offs
Aproximación rectangular; no es CAD, área efectiva de flujo, caudal o barrido.
La admisión pendiente impide declarar completada toda la entrega 3. Pruebas,
inspección Windows y aceptación manual siguen siendo evidencias separadas.
