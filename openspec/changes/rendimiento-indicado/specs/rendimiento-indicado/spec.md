## ADDED Requirements
### Requirement: Derivados indicados comunes
El sistema SHALL derivar potencia y par del W_C y RPM guardados: 2T P=W_C*rpm/60,
T=W_C/(2*pi);4T P=W_C*rpm/120,T=W_C/(4*pi). SHALL rechazar ciclo inválido,
RPM no positiva/no finita y trabajo no finito. No integrar curvas ni aplicar pérdidas.
#### Scenario: Referencia analítica
- **WHEN** W_C es2*pi para2T o4*pi para4T, a3000rpm
- **THEN** resulta T=1N·m y P=100*pi W.
### Requirement: Vista Rendimiento
La navegación SHALL incluir Rendimiento debajo de Simulación, usando CAE existente.
SHALL reutilizar automáticamente el último barrido compatible de sesión o conservar
el compatible ya seleccionado. Sin curva SHALL ofrecer Calcular rendimiento para
el proyecto actual y Abrir barrido existente como acción secundaria. Entrar no
SHALL abrir diálogos ni iniciar cálculos. La acción explícita SHALL delegar en el
barrido actual: plan_rpms, captura, validaciones, worker, persistencia y cancelación.
SHALL mostrar fuente/ciclo/estado/RPM, resumen de mayores valores entre puntos
calculados, cantidad convergida y rango; no atribuir máximos físicos del motor.
#### Scenario: Cambio de proyecto
- **WHEN** el proyecto abierto cambia de ciclo o geometría
- **THEN** se retiran curvas incompatibles sin borrar resultados; abrir un histórico
  explícitamente lo identifica como análisis histórico y conserva sus datos guardados.
#### Scenario: Cálculo explícito y finalización
- **WHEN** se pulsa Calcular rendimiento con un proyecto válido
- **THEN** usa el barrido existente, muestra punto/RPM/ciclos/tiempo/convergidos/pendientes
  y Cancelar; al terminar presenta automáticamente el barrido validado en la misma vista.
#### Scenario: Reutilización desde Simulación
- **WHEN** se completa un barrido compatible desde Simulación y se entra a Rendimiento
- **THEN** muestra sus curvas sin pedir seleccionar el archivo.
### Requirement: Gráficos y consulta fieles
SHALL presentar gráfico combinado RPM/potencia indicada[kW]/par indicado equivalente[N·m],
ejes etiquetados azul/ámbar, puntos y segmentos rectos sin suavizar/interpolar/extrapolar.
SHALL incluir W_C y pmax secundarios, tabla y selección con detalle/abrir resultado.
SHALL mostrar advertencias de magnitudes indicadas sin pérdidas ni valores al eje.
#### Scenario: Punto no convergido
- **WHEN** hay puntos fallidos/cancelados/no ejecutados
- **THEN** no muestran valores ficticios, no unen curvas a través del hueco ni permiten abrirlos como convergidos.
### Requirement: Resultados comparación y CSV
Resultados individuales SHALL mostrar ambos derivados. Comparar SHALL añadirlos
solo bajo compatibilidad existente (incluidas mismasRPM). CSV nuevos SHALL
incluir indicated_power_W e indicated_torque_Nm con precisión completa.
#### Scenario: Lectura histórica
- **WHEN** se abren resultados anteriores con trabajo/ciclo/RPM
- **THEN** deriva al presentar/exportar, sin reescribir los originales.
### Requirement: Comprobación y candidata
SHALL mantener suite y física, comprobar UI/EXE con históricos2T/4T y generar rc6
si aprueban, preservando rc5, capturas/evidencia y aceptación manual separada.
#### Scenario: Redimensionado
- **WHEN** el ancho es reducido
- **THEN** apila secundarios sin scroll horizontal global y conserva acceso por teclado.
