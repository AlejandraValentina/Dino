## Autoridad y progresión
P1 queda congelado por inventario SHA256 en recibo de aceptación humana separado.
P2A implementa primero EOS, malla, HLLC/HLLE, BC y Euler FV. P2B no existe hasta
PASS de T01–T12 y revisión independiente. Máximo tres reparaciones de bugs
después de la primera ejecución; no cambios de umbrales/métodos/casos para pasar.
La implementación inicial y tests unitarios preceden al commit fuente y ejecución.

## Separación
gas1d no es importado desde 0D/UI; no nuevos formatos públicos. EOS inmutable,
mesh compartida, flux vector completo y rechazo de etapas según P1. Estado son
integrales C_i; geometría en SI. Scalar flux HLLC=f_mass*Y_donor, algebraicamente
idéntico a la ecuación estrella, sin clipping ni corrección posterior del estado.

## Referencias y evidencia
Solución exacta de Riemann por raíz de presión y ramas analíticas, sin llamar
HLLC; integración adaptativa Gauss por piezas y promedios conservados. Casos
analíticos de contacto/onda/nozzle según P1. Evidencia completa comprimida gzip
determinista por subcaso, métricas y figuras SVG fuera de UI, ledgers por paso.
Presupuesto120s por subcaso de P1, sin optimización numba/Cython/GPU/multiproceso.
Un timeout es fallo de infraestructura, nunca PASS científico.

## Orquestador
P2 requiere evidencias P0/P1 aceptadas. Configuración max_repair_attempts=3;
el runner no edita código: reparaciones concretas se registran y se verifica
solo lo afectado sin encadenamiento. Stub conserva su procedencia; dictamen
independiente read-only se adjunta con hashes y gate reevaluado explícitamente.
No reusar cierre P0/P1 para fingir un PASS de P2. P3–P9 deshabilitadas.

## P2B autorizado — 18/09/2026
P1_R4_HUMAN_ACCEPTED y P2A_HUMAN_ACCEPTED registrados por orden explícita;
no registrar P2_HUMAN_ACCEPTED. FIRST_ORDER y sus archivos actuales quedan
congelados por hashes. Nueva ruta MUSCL_SSPRK2 y selector de método aislado;
no refactorizar ni alterar el camino first-order verificado.

MUSCL en rho/u/p/Y con minmod de gradientes entre centroides. Ghost periódico
trasladado por L; en extremos usar el estado exterior de la BC existente en
centro reflejado respecto de la cara. La BC se vuelve a evaluar sobre el estado
interior reconstruido para obtener el flujo de cara, sin cambiar sus ecuaciones.
Si una extrapolación no es admisible, anular todas las slopes de esa celda,
contador explícito, sin cambiar el promedio. Fuente p_i*(A_R-A_L) en cada stage.

SSP-RK2: predictor C1=Cn+dtL(Cn), segundo Euler C2=C1+dtL(C1),
Cnuevo=.5Cn+.5C2. Validar C1,C2 y Cnuevo; comprobar CFL en ambos RHS.
Rechazo: rehacer paso completo desde Cn y ledgers anteriores, dt/2 hasta12
reducciones. Contar RHS/fallbacks/downgrades realmente evaluados incluso si
el intento se rechaza; ledger aceptado pesa cada etapa1/2. Sin limiter nuevo.

La orden actual aplica expresamente los criterios de refinamiento R4 a MUSCL,
aunque el documento histórico R4 limitaba su adopción a first-order y conservaba
T11original para MUSCL. Se registra esta extensión de ámbito por instrucción
más reciente; NO se editan archivosP1–R4 ni se restaura la cota8%. Misma métrica,
parejasCFL y transiciones400→800→1600, mismas cotas cuantitativas padre.

Política: max_repair_attempts se define por fase y el runner lleva attempts local;
P2B es subfase nueva con3 reparaciones de bugs, sin modificar política global.
No reintentos automáticos de ciencia. Registro manual acotado de cada reparación.
T01–T12 completos si no hay STOP científico; incluir T12 temprano para no ocultar
fallo de positividad. No rescatar fallo de método con clipping/otro limiter.
Control FIRST_ORDER: hashes exactos, comparación de todos los registros previos
y regresiones focalizadas realmente ejecutadas. P0 histórico por hashes/offline.
Presupuesto por caso120s original; T10_800 ya tenía240s por coste enR3.
Si el coste second-order supera límite, reportar infraestructura sin cambiar
silenciosamente presupuestos contractuales ni resultados.
