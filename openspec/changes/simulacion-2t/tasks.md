# Tareas de simulacion-2t

## Definición documental previa
- [x] 1. Comprobar Git/código/documentación pertinente y preservar entrega 4 y evidencias.
- [x] 2. Proponer un solo modelo físico, ecuaciones, conductos/transferencias y fuentes primarias.
- [x] 3. Fijar caso sintético completo, datos reutilizados/adicionales y límites de capacidad.
- [x] 4. Definir controles independientes y prueba futura con tolerancias, convergencia y presupuestos previos.
- [x] 5. Revisar puntualmente consistencia documental, validar OpenSpec y actualizar referencias de estado.
- [x] 6. Preparar commit documental propio y registrar publicación pendiente sin reintento de autenticación.

## Prototipo aprobado y autorizado por orden explícita del 15/09/2026
- [x] 7. Obtener aprobación explícita de reducción 0D sin ondas/inercia, transferencias sin almacenamiento y restantes aproximaciones/caso/protocolo de design.md.
- [x] 8. Obtener autorización de implementación/ejecución del prototipo acotado; no se infiere de esta definición.
- [x] 9. Tras autorización, implementar y comprobar balances/enlaces/energía con referencias elementales independientes.
- [x] 10. Tras autorización, ejecutar el caso completo y comparación de resolución, medir coste y registrar convergencia/fallo.

No se detallan aquí integración Qt, nuevos archivos ni entregas posteriores: no
están autorizados. Aprobar documentos no marca tareas 7–10 automáticamente.

## Evidencia de esta definición — 15/09/2026
Inicio main 545685b, árbol limpio y un commit por delante de origin/main.
Commit de entrega 4 conservado; publicación sigue pendiente por autenticación
conocida. No se repite push ni se consultan credenciales. Solo documentos: no
pruebas anteriores repetidas, solver, simulaciones, nuevas capturas o curvas.
Fuentes, caso y protocolo constan únicamente en design.md. Implementación y
aceptación manual previas permanecen separadas e intactas.

- Revisión documental independiente puntual: detectó posible rechazo sistemático
  de etapas RK4 cerca del fin del aporte al integrar F_C. Corregido en el diseño:
  evaluación analítica de F_C en todas las etapas del intervalo cerrado, conversión
  por diferencia analítica, sin recorte/renormalización. No se implementó ni probó
  ese algoritmo; autorrevisión del principal de la aclaración y del diff documental.
- Sustitución aritmética independiente para revisar referencias del documento:
  beta_crit=0.5282817877171742, q_sónico=0.04667117121212454 kg/s y
  q(beta=0.8)=0.038214552836718804 kg/s; volúmenes sintéticos coherentes.
  Esto no es una prueba del motor ni evidencia de viabilidad del solver.
- OpenSpec status/instructions/validate disponibles, sin reinstalar ni init/update.
  Validación estricta aprobada; status completo describe artefactos documentales,
  no implementación. Aprobaciones y tareas futuras 7–10 permanecen sin marcar.
- Solo archivos documentales propios preparados para commit separado. Sin cambio
  de código/tests/JSON, ejecución de suite previa ni nuevo intento de publicación.

## Evidencia del prototipo autorizado — 15/09/2026

- Inicio `main` en `6e29745`, árbol limpio, igual a la referencia local
  `origin/main`. Se preservaron entregas anteriores y remoto existente.
  La orden explícita de la usuaria acredita tareas 7/8; no es aprobación inferida
  desde documentos ni aceptación experimental del modelo.
- Implementación: tres módulos estándar (`simulation_case`, `simulation`,
  `prototype`), geometría y área rectangular reutilizadas. Caso sintético separado,
  cuatro CV, seis enlaces reversibles, RK4/eventos, F_C analítica en cada etapa,
  conversión por primitiva, trabajo C/K separado. Sin cambios de Qt, JSON v5,
  dependencias o configuración global. Salidas grandes excluidas de Git.
- Antes de integrar el motor: seis controles elementales independientes aprobados
  en 0,036 s (geometría, orificio, recipientes, adiabática, calor, mezcla). Durante
  preparación, una aserción de CSV exigía igualdad binaria con 140000 Pa y recibió
  139999,99999999997; corregida la aserción numérica, no el resultado ni el modelo.
- Revisión independiente puntual, solo lectura: detectó tendencia exigida incluso
  por debajo de los pisos de sensibilidad. Corregida **antes de la serie** con los
  pisos previos de 1 J y 1e-7 kg, cubierta por reproducción específica. No se añadió
  tolerancia de p/Y. Sin otros defectos concretos en la pasada. El revisor no
  ejecutó el motor; principal realizó autorrevisión y pruebas de la corrección.
- Quince controles nuevos aprobados antes de la serie. Incluyen cancelación real
  programada a los 0,05 s y comprobación de salida en menos de 1 s desde la solicitud,
  retorno inicial C→K con entalpía/fresca del cilindro, cierre, seis evaluaciones de
  enlace por etapa, dominio sin recorte, auditoría con error inducido, presupuestos
  y proceso de consola sin PySide6 importado.
- Una única serie completa, sin reinicios ni cambios posteriores de parámetros,
  método o umbrales. Comando ejecutado desde la raíz:
  `.\.venv\Scripts\python.exe -m motorsim.prototype --output results/simulacion-2t/viabilidad-20260915`.
  Los tres arranques son idénticos, 180°, 3000 rpm. Todas las corridas terminaron
  por **límite de 30 ciclos, no convergido**; ninguna excedió tiempo, RAM, RHS o
  dominio. Rechazos controlados: 2, 1 y 0, respectivamente, sin reparar estados.

| Paso | Ciclos / convergencia | Tiempo | Pico proceso | W_C / W_K [J] | p_C máxima [Pa] |
| --- | --- | --- | --- | --- | --- |
| 0,5° | 30 / No | 5,094 s | 24,6992 MiB | 16,634690 / −3,373391 | 1335402,759 |
| 0,25° | 30 / No | 10,016 s | 28,5313 MiB | 16,544720 / −3,368888 | 1332998,623 |
| 0,125° | 30 / No | 19,125 s | 33,4297 MiB | 16,483385 / −3,366819 | 1331368,705 |

Diagnósticos de la última vuelta; no son resultados convergidos aceptados.
Máximos normalizados entre los cuatro CV y el balance global de esa vuelta:

| Paso | Discreto masa / energía / fresca | Independiente masa / energía / fresca |
| --- | --- | --- |
| 0,5° | 2,10e-15 / 8,21e-16 / 1,07e-15 | 0,113369 / 0,112205 / 0,113119 |
| 0,25° | 1,97e-15 / 1,35e-15 / 2,11e-15 | 0,058870 / 0,058285 / 0,058716 |
| 0,125° | 2,73e-15 / 2,69e-15 / 5,89e-16 | 0,030091 / 0,029804 / 0,030002 |

- **Primer impedimento:** cuadratura independiente fuera de 0,001 desde la primera
  vuelta en las tres resoluciones. No aprueba ninguna vuelta; por eso no se alcanza
  el criterio completo de convergencia aunque m/U/Y/trabajo/presión se estabilicen.
  La cuadratura usa extremos de **cada paso aceptado**, no los pesos RK4 ni solo
  los nodos de 0,5° exportados. Incluye integral independiente de p dV y primitiva
  del calor. El cierre discreto no se presenta como segunda prueba independiente.
- Diagnóstico leído de CSV, sin otra corrida: con falda cerrada a 200°, I permanece
  cerca de 100090,45 / 100022,52 / 100005,60 Pa según resolución y sus caudales de
  extremo muestreados son −0,003580 / −0,001776 / −0,000882 kg/s. Esto muestra una
  discrepancia numérica cerca del equilibrio del reservorio; no se cambia el método
  ni se declara estable por la sola repetición entre vueltas.
- Sensibilidad: **no acreditada**, falta la condición previa de las tres resoluciones
  convergidas. No se fuerza trabajo positivo ni se interpreta como potencia al eje.
  F_s final = 4,69561e-5 / 4,67087e-5 / 4,65400e-5 kg; Q = 37,56490 / 37,36698 /
  37,23197 J. Hay aporte prescrito, pero no una predicción de combustión.
- Serie total medida: 34,719 s; Intel Core i5-10400 @ 2,90 GHz, 12 procesadores
  lógicos, Windows 10.0.19045 AMD64, Python 3.11.0. Pico residente de proceso Windows
  incluye runtime/resultados anteriores de la serie. Avance por vuelta y también
  a intervalos de 0,5 s; cancelación/presupuesto comprobados en cada paso.
- Evidencia local: `results/simulacion-2t/viabilidad-20260915/`, con manifiesto completo,
  entorno, resumen de serie, resúmenes de 30 ciclos por resolución y últimas dos
  vueltas (1442 filas/CSV). Incluye inventarios, P-V, flujos/sentidos, calor, trabajo,
  residuos absolutos y normalizados y causas de parada. No es formato de proyectos.
- Estado final del código, después de la última corrección funcional:
  `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`:
  **100/100 aprobadas en 8,547 s**; widgets `offscreen`, no inspección visual Windows.
  OpenSpec estricto aprobado. No hay nueva aceptación manual ni validación experimental.
- Tareas 9/10 acreditan implementación, controles y **registro de un fallo de
  viabilidad**. Entrega 5 sigue **En curso**, sin integración Qt; no se archiva ni
  inicia entrega 6. Se detiene la prueba; resolver el impedimento mediante cambios
  de método/modelo o una nueva campaña requiere decisión posterior.
- Código, caso, pruebas y documentación se preparan en commit propio. Se permite
  un único push normal según la orden actual; su resultado se comunica en la entrega,
  sin buscar credenciales, cambiar remotos/configuración ni reescribir historial.
