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
