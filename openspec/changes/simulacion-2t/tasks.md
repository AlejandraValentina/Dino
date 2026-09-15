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
- [x] 11. Diagnosticar localmente el rechazo preservando la serie; comprobar cuadratura, reconstruir una vuelta e identificar si requiere corrección o decisión numérica.
- [x] 12. Implementar la duplicación adaptativa autorizada con perfiles A/B/C y comprobar el intervalo local, retorno físico y controles del integrador.
- [x] 13. Ejecutar una serie A/B/C acotada desde los estados originales, registrar coste/precisión y detener sin extender presupuestos.

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

## Diagnóstico localizado posterior — 15/09/2026

Inicio en `54821600bd46b034cd15f8d88ae8b5be066c48c7`, rama main, árbol limpio,
un commit por delante de la referencia origin/main. Commit y archivos de
`results/simulacion-2t/viabilidad-20260915/` preservados; se compararon SHA-256
antes/después y se registraron en el diagnóstico. No se hizo push ni se tocó
autenticación. La orden actual autoriza diagnóstico y correcciones demostradas,
no cambios silenciosos de método, modelo, tolerancias o presupuestos.

### Condición que falla, sin cambiar la aceptación

Se leyeron los 30 resúmenes existentes por resolución. Las métricas de
repetibilidad alcanzan tres vueltas seguidas desde la vuelta 8 / 9 / 9 para
0,5° / 0,25° / 0,125°, respectivamente. Esto **no es convergencia completa**:
`balances_passed=False` en las 30 vueltas de cada una, por auditoría independiente
>0,001; `convergence.passed` sigue False y el contador compuesto permanece en cero.
Ni el calor positivo ni la repetibilidad sustituyen ese requisito.

En la última vuelta, máximos entre resoluciones: diferencia relativa m=3,35e-6,
U=3,17e-7, Y absoluta=1,27e-6, W relativa=5,70e-6 y curva p relativa=2,13e-6;
todos cumplen sus respectivos límites de repetibilidad. Los balances siguen
rechazados según la tabla original de esta tarea, que no se modifica.

Sensibilidad diagnóstica entre finas: W=0,0037073 relativo, p máxima=0,0012242,
curva=0,0014002, máximo por enlace de masa=0,0033007 (todos <0,01), pero
**Delta Y_E=0,0089694048 >0,005**; Y_I/K/C=0,00168946 / 0,00077414 / 0,00050642.
La diferencia gruesa Y_E=0,0168160 es mayor, pero la tendencia favorable no
satisface el límite fino. Comparaciones diagnósticas, no acreditación formal:
faltan las tres resoluciones convergidas. No se forzó esa condición al calcularlas.

### Cuadratura, tiempos y trazabilidad

- Antes del replay, cinco pruebas de flujos prescritos aprobaron: constante,
  lineal con inversión y distintos donantes, integral cuadrática y su error
  de trapecio conocido, eventos no uniformes, extremos repetidos de duración
  cero y conversión grados/18000 a segundos. Un signo de transporte incorrecto
  inducido sigue siendo rechazado. No se usan valores esperados del propio auditor.
- Una sexta prueba fuerza el descarte de un intento calculado y comprueba que
  ni el libro RK4 ni el auditor incorporan ese intento. Se acepta solo el medio
  paso posterior, con el mismo inventario/libro que su cálculo separado.
- El auditor original evalúa extremos de **todos los pasos aceptados**. Cambiar
  solo la información usada, reconstruyendo desde el CSV de 0,5°, da máximos
  0,113440 / 0,058788 / 0,029994, frente a 0,113369 / 0,058870 / 0,030091 del
  auditor de pasos aceptados. La escasez de nodos CSV no explica el rechazo.
  No se interpoló una salida ni se sustituyó el auditor por pesos RK4.
- Replay de **una única vuelta**, la 30 de 0,5°, desde el estado guardado al final
  de la 29, a los ángulos originales 10620–10980°. No es un arranque formal ni
  un mecanismo de checkpoint. Reproduce **exactamente** estado final y auditoría
  originales: 728 pasos aceptados, 16 no uniformes junto a eventos, cero rechazos,
  duración física total 0,020000000000000167 s. Pasos contiguos, ningún tramo omitido.
- Los cuatro tiempos de etapa y el extremo coinciden con el paso registrado:
  discrepancia angular cero. Pesos [1,2,2,1]/6 frente al incremento del libro:
  diferencias máximas masa/F=6,78e-21 kg, entalpía=3,56e-15 J. **Esto verifica la
  implementación RK4, no es la segunda auditoría independiente.**
- Cero signos de flujo incorrectos. Donante/entalpía/Y de cada etapa y extremo
  concuerdan: diferencias máximas h relativa=5,68e-16, Y absoluta=1,12e-16.
  Los estados y flujos registrados son contemporáneos. Los 721 nodos de cada
  vuelta CSV son estrictamente crecientes; la frontera compartida entre vueltas
  no agrega un intervalo temporal. La auditoría no se construye desde ese CSV.

### Causa demostrada y descomposición

La discrepancia principal procede de los enlaces exteriores: I cuando la falda
está cerrada (180–270° y 450–540° en esta vuelta), E cuando el escape del cilindro
está cerrado (270–450°). El registro local contiene los seis enlaces por bandas
de 30°. Dos bandas aisladas, sin calor ni trabajo en el CV, permiten comparar
directamente inventario y entrada neta (signo positivo hacia el CV):

| CV / intervalo | Magnitud | Delta inventario | Integral RK4 neta | Trapecios independientes netos |
| --- | --- | --- | --- | --- |
| I / 180–210° | masa kg | +1,668394e-7 | +1,668394e-7 | −5,955713e-6 |
| I / 180–210° | energía J | +3,604604e-5 | +3,604604e-5 | −2,049855 |
| I / 180–210° | fresca kg | +2,043372e-7 | +2,043372e-7 | −5,906428e-6 |
| E / 300–330° | masa kg | +8,499085e-8 | +8,499085e-8 | −1,751367e-6 |
| E / 300–330° | energía J | +4,836327e-6 | +4,836327e-6 | −1,030669 |
| E / 300–330° | fresca kg | −5,856707e-7 | −5,856707e-7 | −7,638749e-7 |

En toda la vuelta, diferencia RK−trapecio del enlace exterior I: +3,762690e-5 kg,
+12,605984 J, +3,754939e-5 kg fresca. En enlace E→exterior: −1,116628e-5 kg,
−6,268392 J, −1,060118e-6 kg fresca. Signos de enlace fijos según el diseño.
La demostración no atribuye el error al calor prescrito del cilindro.

A 200–200,5°, I: Delta p de etapas = +90,4507 / −100,0414 / +287,2195 /
−588,5336 Pa; extremo aceptado +90,4572 Pa. Caudal exterior→I = −0,00357975 /
+0,00382914 / −0,00637686 / +0,00926221 kg/s; extremo −0,00358001.
A 300–300,5°, E: Delta p = +13,3280 / −15,3785 / +43,2213 / −90,0630 Pa;
extremo +13,3283 Pa. Caudal E→exterior = +0,00105017 / −0,00116345 /
+0,00189106 / −0,00281439 kg/s; extremo +0,00105020.

Las etapas de entrada a E transportan h=553500 J/kg e Y=0 del reservorio;
las de salida usan T/Y de E. La elección es correcta para esos estados auxiliares,
pero el paso fijo provoca retornos numéricos que alteran el resultado aceptado.
Las etapas 2/3 comparten tiempo; no son muestras sucesivas de una trayectoria densa.

**Error de trayectoria demostrado:** E aislado del cilindro, sin calor/trabajo,
p inicialmente superior al exterior, debe descargar hacia equilibrio conservando
Y. Sin embargo, el paso de 0,5° eleva ligeramente p y reduce Y_E. El mismo intervalo
de 0,5° se comprobó con dos discretizaciones, desde exactamente el mismo estado:

| Diagnóstico 300–300,5° | Pasos | p_E final −100000 [Pa] | Cambio Y_E (referencia: cero) |
| --- | --- | --- | --- |
| RK4 0,5° | 1 | +13,328288 | −0,00015287985 |
| RK4 0,125° | 4 | +0,885767 | −0,00002690636 |

Refinar **la integración** reduce el defecto de trayectoria, no lo elimina ni
acredita la serie. Refinar solo la salida de auditoría prácticamente no cambia
su fallo. No se realizó una escalera ni un nuevo barrido de casos/resoluciones.

### Resultado, coste y parada

- No se encontró defecto de implementación o cuadratura que corregir. El núcleo,
  parámetros, método, tolerancias y aceptación compuesta permanecen idénticos a
  54821600. Se añaden controles de diagnóstico, no una corrección física disfrazada.
  No hay serie oficial posterior: la repetición autorizada estaba condicionada a
  una corrección demostrada. Los resultados anteriores siguen no acreditados.
- **Única propuesta pendiente:** control local RK4 por comparación de un paso
  con dos medios pasos, detallado en design.md, sin implementarlo. 12 RHS frente
  a 4 por intento, más pasos/rechazos cuando se refine; tolerancias locales por
  fijar/aprobar. No garantiza coste/precisión ni autoriza superar mínimos/topes.
- Replay: 0,219 s, 40,77 MiB, 2912 RHS, una vuelta. Intervalo adicional: cinco
  pasos en total, 20 RHS; su `seconds=0.0` significa inferior a la resolución
  del reloj utilizado, **no coste físico nulo**. El proceso que cargó la traza y
  ejecutó ese intervalo duró 0,793 s (herramienta), pico 60,13 MiB. Equipo/versiones
  iguales a la evidencia inicial. Sin exceder los presupuestos del protocolo.
- Archivos nuevos locales: `results/simulacion-2t/diagnostico-20260915/`,
  `diagnosis.json`, `accepted-steps.json`, `closed-interval.json`, `trace-checks.json`.
  Script reproducible de diagnóstico fijo en `tests/diagnose_simulation_balance.py`;
  no telemetría general ni salida sobrescrita. Los resultados quedan excluidos de Git.
- Suite pertinente final: `.\.venv\Scripts\python.exe -m unittest discover -s tests
  -p 'test_simulation_*.py' -v`: **21/21 aprobadas en 0,275 s**. Incluye seis controles
  nuevos y quince previos. No se repite Qt/persistencia: producción e interfaz no
  cambiaron. OpenSpec estricto aprobado. Sin nueva inspección visual ni aceptación manual.
- Revisión puntual independiente de solo lectura: sin hallazgos bloqueantes;
  confirmó evidencia de error de trayectoria y precisó cómo informar el reloj del
  ensayo corto. Autorrevisión del principal de la instrumentación, comprobación
  posterior de pesos/tiempos/donantes, documentación y preservación de resultados.
- Entrega 5 **En curso: decisión numérica pendiente**. Se prepara commit documental,
  de pruebas e instrumento localizado; no hay reintento de publicación, archivo de
  cambio, integración Qt ni avance a otra entrega.

## Evidencia del ensayo adaptativo autorizado — 15/09/2026

Esta evidencia corresponde a las tareas 12/13 y no modifica los resultados
históricos anteriores. Inicio en `main`, `783970d90d8470d1f552dbdf11b7781133ea6915`,
árbol limpio e igual a la referencia local `origin/main`. Commit y directorios
originales conservados; sus SHA256 se comprobaron antes y después del ensayo.
Sin push, consulta de credenciales ni cambios de configuración global.

### Implementación y regresión local

`motorsim/adaptive.py` conserva los dos medios pasos, sin Richardson; compara
individualmente los doce componentes m/U/F con el estimador /15 y los perfiles
fijos de design.md. Control proporcional 0,9 y exponente 1/5, factor 0,2–2,
tratamiento explícito de cero/no finitos y reducción en cada rechazo. Cada rama
mantiene sus acumuladores; F_s se captura fuera de los intentos, F_C continúa
analítica. Auditoría independiente en ambos medios pasos aceptados, incluido el
punto intermedio. Eventos y exportación común a 0,5° no sustituyen esos pasos.
Se cuentan también las evaluaciones de extremos que calculan RHS: normalmente
15 por intento (12 etapas y 3 extremos), más el inicio de cada ciclo; un intento
interrumpido puede costar menos. El presupuesto cuenta todas esas evaluaciones.
El mínimo 0,001° se exige a cada medio paso, sin tolerancia física artificial.

Intervalo 300–300,5° desde el estado literal de la evidencia anterior, sin
alterarlo ni alimentar la serie formal con él. Resultado local:

| Método | Cambio Y_E | RHS reales | Tiempo s |
| --- | ---: | ---: | ---: |
| Fijo histórico 0,5° | −0,000152879850 | 4 etapas históricas | — |
| A | −0,000011022007 | 121 | 0,006279 |
| B | −0,000006908630 | 136 | 0,006230 |
| C | −0,000004036773 | 196 | 0,008000 |

La deriva disminuye aproximadamente 13,9/22,1/37,9 veces; no desaparece.
Todos completan el intervalo sin agotar límites. El ensayo separado con presión
inicial de E inferior al reservorio admite entrada física; no se anulan flujos
ni se impone Y. Comparación local completa, con presión, m/U/F/Y y masa en ambos
sentidos: `results/simulacion-2t/adaptativo-local-20260915/comparison.json`.
`summary-final.json` contiene el conteo corregido; sustituye al conteo inicial
de `summary.json`, que se conserva con sus hashes de las fuentes originales.

### Única serie formal y coste

Comando ejecutado una vez:
`.\.venv\Scripts\python.exe -m motorsim.prototype --output results/simulacion-2t/adaptativo-20260915`.
Cada perfil parte del caso original S2T-0D-01; no hay continuación entre perfiles.
Python 3.11.0, Windows 10.0.19045 AMD64, Intel i5-10400 a 2,9 GHz, 12 CPU lógicas;
Qt no cargado. Parámetros y entorno completos en `case.json`/`environment.json`.

| Perfil | Convergencia completa | Ciclos completos (+ parcial) | Parada | s | Pico MiB |
| --- | --- | ---: | --- | ---: | ---: |
| A | No | 18 (+19) | 60 s por ejecución | 60,000 | 26,207 |
| B | No | 11 (+12) | 60 s por ejecución | 60,000 | 34,262 |
| C | No | 7 (+8) | 180 s globales | 57,015 | 41,828 |

La serie registra 180,110 s incluyendo cierre/escritura final: la integración
se detuvo al alcanzar el tope global, sin extenderla para acabar el ciclo.
Ninguna ejecución llegó a 30 ciclos, 512 MiB o dos millones de RHS. No se lanzó
otra serie ni se modificaron tolerancias para intentar obtener un resultado favorable.

| Perfil | Intentos | Medios pasos aceptados | Rechazos error / físico / no finito | RHS totales (etapas + extremos) |
| --- | ---: | ---: | --- | --- |
| A | 88773 | 177290 | 127 / 1 / 0 | 1331603 (1065268 + 266335) |
| B | 89810 | 179444 | 86 / 2 / 0 | 1347150 (1077712 + 269438) |
| C | 85798 | 171476 | 59 / 1 / 0 | 1286967 (1029568 + 257399) |

| Perfil | Máximo propuesto autorizado ° | Medio paso mínimo ° | Media ° | Máximo real ° |
| --- | ---: | ---: | ---: | ---: |
| A | 0,5 | 0,0010012213 | 0,0385665329 | 0,0887996161 |
| B | 0,25 | 0,0010001903 | 0,0237333965 | 0,0489866740 |
| C | 0,125 | 0,0010001870 | 0,0147747914 | 0,0282873044 |

Los CSV `profile-*-attempts.csv` registran propuesta, medio paso, error, causa y
RHS acumulados de cada intento. Se comprobó sobre ellos E <= 1 y medio paso
>= 0,001° en todos los aceptados, y dos medios pasos por intento aceptado.

### Resultados del último ciclo completo de cada perfil

| Perfil | W indicado C J | W cárter J | p máxima C Pa | Y_I | Y_K | Y_C | Y_E |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A | 16,4349633 | −3,3651205 | 1330075,43 | 0,98550943 | 0,97634931 | 0,56160010 | 0,37569610 |
| B | 16,4807541 | −3,3653063 | 1331281,86 | 0,98573406 | 0,97699551 | 0,56206279 | 0,37779044 |
| C | 16,5977916 | −3,3661354 | 1334390,39 | 0,98667551 | 0,97865857 | 0,56316336 | 0,37962940 |

Residuos independientes normalizados (magnitudes adimensionales; límite 0,001):

| Perfil / volumen | Masa | Energía | Fresca |
| --- | ---: | ---: | ---: |
| A / I | 7,892706e-3 | 7,819416e-3 | 7,867605e-3 |
| A / K | 7,766539e-7 | 1,030596e-6 | 6,605787e-7 |
| A / C | 8,333321e-7 | 6,320002e-7 | 4,184468e-7 |
| A / E | 8,099840e-3 | 7,203279e-3 | 7,813646e-4 |
| A / global | 7,462293e-3 | 9,474212e-3 | 5,022387e-3 |
| B / I | 4,546109e-3 | 4,505227e-3 | 4,531906e-3 |
| B / K | 3,206877e-7 | 4,393231e-7 | 2,657957e-7 |
| B / C | 4,317189e-8 | 3,332466e-8 | 3,719211e-8 |
| B / E | 5,228243e-3 | 4,653139e-3 | 5,215051e-4 |
| B / global | 4,466760e-3 | 5,763218e-3 | 2,903093e-3 |
| C / I | 2,744366e-3 | 2,721198e-3 | 2,736371e-3 |
| C / K | 2,129934e-7 | 2,639108e-7 | 1,951430e-7 |
| C / C | 8,590239e-8 | 6,499510e-8 | 4,440851e-8 |
| C / E | 3,241316e-3 | 2,890752e-3 | 3,309921e-4 |
| C / global | 2,712801e-3 | 3,527325e-3 | 1,748217e-3 |

Fallan I (los tres balances), E (masa/energía) y global (los tres), aunque los
balances discretos máximos son 8,393e-15 / 1,095e-14 / 4,326e-15. El peor
independiente es energía global: 0,947421 % / 0,576322 % / 0,352732 %, superior
al 0,1 % en los tres perfiles. Ningún ciclo satisfizo la aceptación completa.

Comparación diagnóstica a igual fase, pero ciclos distintos (18/11/7):

| Par | Diferencia relativa W | Diferencia relativa p máxima | Diferencia curva p | Diferencias absolutas Y_I / Y_K / Y_C / Y_E |
| --- | ---: | ---: | ---: | --- |
| A–B | 0,00277844 | 0,00090621 | 0,00103254 | 0,00022463 / 0,00064620 / 0,00046269 / 0,00209434 |
| B–C | 0,00705139 | 0,00232955 | 0,00264597 | 0,00094145 / 0,00166306 / 0,00110058 / 0,00183896 |

No acredita sensibilidad: no existen soluciones completamente convergidas y
varias diferencias crecen entre el primer y segundo par. `comparison-diagnostic.json`
incluye los seis enlaces y marca explícitamente esa limitación. Los archivos
`step-*-summary.json` conservan también los estados/balances del ciclo parcial;
`step-*-last-two.csv` y `step-*-partial.csv` separan ciclos completos y parcial.
Todos los resultados nuevos están bajo directorios ignorados de `results/simulacion-2t/`.

### Comprobación final y cierre de este ensayo

- Suite final, tras corregir el conteo y ejecutar la serie:
  `.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_adaptive.py -v`:
  **10/10 aprobadas, 0,138 s**; y
  `.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_simulation_*.py' -q`:
  **21/21 aprobadas, 0,396 s**. Incluyen retorno físico, rechazo local con estado
  positivo, ramas/acumuladores, eventos/calor, mínimo real, RHS/presupuesto,
  auditoría del punto intermedio y cancelación observable.
- Una revisión puntual independiente de solo lectura encontró un subconteo de
  RHS en evaluaciones de extremos. Corregido antes de la serie, con prueba que
  contrasta las llamadas reales a Model.evaluate. Autorrevisión del principal
  de la corrección, documentación y trazas; sin otra campaña de revisión.
- `openspec validate simulacion-2t --strict --no-interactive`: aprobado en el
  estado documental final. `git diff --check`: sin errores de espacios.
- **Controlador:** los controles ejecutados acreditan el comportamiento
  especificado, dentro del alcance probado; el estimador no es una cota garantizada.
- **Defecto local:** reducido, no eliminado; no se impuso invariancia artificial.
- **Viabilidad completa:** no acreditada dentro del protocolo; balances y coste
  impiden cerrar. La entrega 5 sigue abierta, sin validación experimental,
  integración Qt, cambios de JSON, inspección de interfaz, archivo ni otra etapa.
  Commit propio del ensayo; publicación no intentada por instrucción expresa.
