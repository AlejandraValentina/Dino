# MODELO — segunda vertical funcional de fuente

Trabajo y comprobación gráfica: 2026-10-30. Cierre documental y commit: 2026-11-03. Base: c279af9/a663b9f. Revisión: SELF_REVIEW. No se reconstruyen los tres modos ni se repite la evaluación comercial. Se ejecutan las prioridades del dueño; no se encontró una especificación UX adicional de DeepSeek versionada que sustituya esas instrucciones.

## Implementado

- Selector único de componentes, sin una segunda barra de navegación visible. Resumen, cilindro/culata, cárter, admisión/conductos, lumbreras/transferencias, escape, combustión, pérdidas, proyecto y avanzado. Los controles existentes conservan sus rutas de aplicación y persistencia.
- Separación efectiva de cilindro, volumen de cárter, dimensiones de lumbreras y provenance/operación avanzada. Cada sección larga tiene scroll propio. Aplicar/Descartar quedan fuera del desplazamiento de componentes; prueba de visibilidad en ventana compacta.
- Resumen: diámetro, carrera, biela, cilindrada, compresión geométrica, cámara derivada, volumen de cárter, compresión primaria, admisión, distribución y estado cargado/borrador. Fuentes desconocidas no se reclasifican automáticamente como medidas.
- Esquema dimensional de diámetro y recorrido PMS–PMI. No se dibuja una culata, squish, espesor de pistón ni posición de biela ficticios. La culata disponible es compresión/volumen derivado.
- Lumbreras: cotas independientes desde PMS y barras de intervalos de apertura obtenidas de `TwoStrokePortSet.event_angles` y `area_at`. No es un mapa circunferencial. Las láminas no reciben una distribución de pistón ficticia. Las ventanas fuera de la carrera visible se identifican.
- Dimensiones, cotas, distribución y áreas reutilizan los datos del mismo borrador. Cambiar tablas/diámetro/carrera/biela actualiza la vista previa. Un borrador inválido conserva la última geometría válida con aviso.
- Edición de **apertura** en grados sólo para ventanas rectangulares, transfer/escape, techo fijo y Cd positivo: `top_mm = piston_position(stroke, rod, opening)`, rama estricta 0–180°. Se conservan altura y ancho; cierre y duración son derivados. No se habilita inversión para perfiles efectivos, techo móvil o admisión por láminas/pistón. Múltiples intervalos no se reducen a una duración única; se ven en Distribución.
- Se preserva la precisión fuente de las dimensiones no editadas; dar formato a la tabla no debe reescribirlas.
- Después del editor se avanzó con el siguiente componente desbloqueado: **escape**. Superposición con origen y escala comunes A/B, escala dimensional igual en ambos ejes, rótulos limitados al ancho disponible, identificación #N y cotas/deltas exactos del tramo seleccionado. Clic en perfil y selección de tabla sincronizados. Sin cambios de topología, malla o backend.

## Verificación gráfica real

Mouse/teclado Windows sobre Desktop de fuente. Proyecto de prueba `synthetic-editor-v2`, motor `SYNTHETIC_EDITOR_V2` creado por diálogo, guardado y reabierto. No se ejecutaron campañas ni builds; las corridas breves de la suite de regresión existente no son campañas periódicas.

| Comprobación | Resultado / captura |
|---|---|
| 980×680 nativos | Resumen y acciones visibles (01,09), edición de diámetro 56→57 mm (02), tabla de lumbreras con sus cinco filas (07) |
| Cárter y derivados | Edición gráfica 356,08→365 cm³. Cilindrada 129,12 cm³, cámara 7,73 cm³ y compresión primaria 1,354:1 visibles tras reapertura (09) |
| Grados y sincronización | Transferencia primaria 115→105°. Cota 34,597071032 mm, cierre 255°, duración 150° en tabla y distribución (03,05); se conservan tras reabrir (09) |
| Rechazo y recuperación | 200° rechazados sin guardar como válidos (04); Descartar recupera los 105° aplicados y las marcas válidas (05) |
| 1360×900 nativos | Distribución y cotas por lumbrera (05,06), edición/delta de escape (08) |
| Duplicación y persistencia | `escape-plus20` duplicado desde el motor base. Primer tramo base 83 mm; variante 103 mm. Guardado en variante actual y proyecto, cierre y reapertura |
| 1920×1080 nativos | Escape superpuesto y cotas (11); cotas de lumbreras sin posiciones circunferenciales inventadas (12) |
| Escape compacto final | Perfil legible, identificadores sin cotas solapadas, tramo seleccionado 103 mm y ΔL +20 mm (10). Tabla/acciones requieren desplazamiento en este componente |

Se midieron los rectángulos de ventana con Win32. Windows está al 125%; el proceso de comprobación usó `QT_SCALE_FACTOR=0.8` para obtener esos tamaños nativos con escala efectiva 1. No se cambia la configuración por defecto del producto ni la del sistema. Para las capturas 1920×1080 se ocultó temporalmente la barra de tareas y se restauró inmediatamente; no se escaló una captura de menor tamaño. En los otros tamaños se capturó directamente la región de la ventana.

## Pruebas

Regresión registrada mediante `run_logged.py`: **42 PASS, 1 SKIP**, 284,64 s; el omitido requiere la raíz histórica externa en el entorno aislado. `regression/desktop-model-editor-v2-regression.summary.json` contiene el recibo.

Después de ajustar el contenedor compacto y el perfil se ejecutaron pruebas focalizadas. `synchronization-final.txt`: **6 PASS** en inversión restringida/eventos, intervalos desconectados, sincronización tabla/cotas/distribución/áreas y persistencia, borrador y rechazo, navegación/acciones compactas y escala común/selección/dimensiones de escape. La tabla de eventos también actualiza el borrador, y los valores derivados del resumen permanecen de sólo lectura. `final-ui-regression.txt`: **9 PASS** de interfaz después de esos cambios de organización. No se presenta una autorrevisión como independiente ni se repiten corridas al cerrar documentalmente la entrega.

Las dos expectativas antiguas de navegación se adaptan al selector y al resumen inicial. No se modifican contratos físicos, solver ni expected values científicos. Los fallos iniciales se conservan en `initial-tests.txt`.

## Estado y límites

Aceptación funcional de fuente del conjunto. rc7/rc9 intactas, sin nuevo TRIAL, push ni promoción de V2/MUSCL/Brent. Es geometría de ingeniería sintética, no validación predictiva.

Fuera del alcance: forma de culata/cárter, mapa circunferencial sin posiciones identificadas, inversión de perfiles arbitrarios, nuevos tipos/topología de escape o cierres físicos. Continúan las dependencias científicas externas y el bloqueo presupuestario de E1.3.

Pendientes de producto concretos: admisión y conductos de transferencia todavía comparten su editor; el escape compacto conserva desplazamiento para recorrer todas las filas/acciones; hay IDs/roles técnicos y números extensos en tablas. No se generan investigaciones ni tareas artificiales para mantener activa la cola.
