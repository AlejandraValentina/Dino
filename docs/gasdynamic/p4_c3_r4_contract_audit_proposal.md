# PROPOSAL / NOT APPROVED / NO CONTRACT CHANGE

## Auditoría focal de C3 — R4

Fecha: 2026-09-28  
Base auditada: `fd5ff9e`  
Alcance: lectura de los documentos C3 indicados, `p4_c3_return_audit.py`,
`dev_orchestrator/p4_sci_04b.py` y los artefactos R3. No se ejecutó el solver ni
una campaña.

## Dictamen

C3 contiene dos verificaciones distintas:

* **A — referencia de retorno:** comprobar, en el snapshot causal preregistrado,
  que el estado/flujo de interfaz productivo es consistente con una solución
  Exact Riemann independiente. Esto mide discrepancia de modelo numérico
  HLLC frente a la referencia exacta, no cierre de la actualización discreta.
* **B — balance de momento:** comprobar que el cambio de momento almacenado en el
  volumen de control coincide con los flujos de momento y la fuente geométrica
  que realmente definen el update productivo, en ambas etapas SSPRK2. Esto mide
  identidad de conservación discreta.

El auditor R3 mezcla esos objetivos en B. `_recompute_stage` usa ExactRiemann
en la interfaz y en la pared, mientras `p4_sci_04b.py` actualiza con HLLC. Además,
el productor usa estados reconstruidos (`lf[0]` y `rf[-1]`) y el auditor usa los
estados de celda (`primitive[0]` y `primitive[-1]`). Por ello
`max_abs_residual=5.840234051652552e-06` no es una medida pura de cierre
discreto HLLC.

Esto no demuestra que el residuo sea inválido como diagnóstico de la comparación
que efectivamente se hizo; demuestra que no puede interpretarse como verificación
de la identidad del update productivo.

## Evidencia cuantitativa offline

El snapshot seleccionado conserva estados y permite recalcular un punto sin
avanzar la solución. En `sample_time_pre_step = 0.0026532366020821743 s`:

| término de momento integrado | auditor Exact/celda | HLLC con estado productivo | diferencia |
|---|---:|---:|---:|
| cara izquierda | 38.96076990845837 N | 38.96090451400843 N | +1.3460555006616914e-04 N |
| pared | 46.55101699696457 N | 46.60017727523689 N | +4.916027827231785e-02 N |

El efecto combinado sobre el incremento SSPRK2 de ese paso es
`-2.8187660724276252e-08 kg*m/s`. La mayor parte de la diferencia de pared
no es únicamente HLLC-vs-Exact: el estado reconstruido productivo tiene
`u=-7.696712366983549e-05 m/s`, mientras el auditor usa la celda con
`u=-0.2807982084376723 m/s`. Manteniendo los mismos estados de celda, la
diferencia HLLC-vs-Exact es `+1.3460555006616914e-04 N` en la izquierda y
`-2.2596389030127284e-05 N` en la pared.

No es posible descomponer offline el máximo global `5.840234051652552e-06`
fila por fila con los dos artefactos pedidos: el JSON de momento conserva
1,940 residuos y términos ya reconstruidos, pero no conserva para cada fila
los estados primitivos/reconstruidos necesarios para reevaluar HLLC y Exact
con las mismas entradas. Por tanto no se atribuye ese máximo a HLLC, Exact o
reconstrucción sin evidencia adicional.

## Qué debería demostrar B

B debe usar, por etapa, los estados pre-step y el mismo volumen, áreas, fuente
`p_i (A_{i+1}-A_i)`, signos y combinación SSPRK2 del update. Para acreditar
identidad discreta, la evaluación debe producir los flujos HLLC desde estados
reconstruidos independientes, sin leer campos de flujo del operador productivo.
No debe reutilizar `interface_flux_observed` ni otro término ya calculado por
el productor.

“Independiente” no exige un tercer modelo físico: exige una segunda evaluación
del mismo contrato numérico. La implementación auditora puede compartir EOS,
geometría y definición de reconstrucción, pero debe tener una ruta HLLC
separada, con tests de paridad y sin importar/reusar el resultado de la ruta
productiva. ExactRiemann queda reservado para A y como diagnóstico comparativo.

## Siguiente paso propuesto, sin cambiar la física

1. Añadir instrumentación durable de estados pre-step por etapa, incluyendo
   estados reconstruidos de las dos caras externas, ghost de pared, `dt`, áreas,
   fuente y momento antes/después. Esto no cambia el solver.
2. Implementar en el auditor una evaluación HLLC independiente para interfaz y
   pared. Calcular B desde esos resultados y desde los estados almacenados, no
   desde campos productivos.
3. Probar la independencia con: (a) paridad contra una tabla congelada de
   microestados HLLC, (b) mutación controlada del flujo productivo que no cambie
   el auditor, y (c) comparación de entradas y salidas sin aliasing ni lectura
   de nombres de campos productivos.
4. Mantener A separado: ExactRiemann contra el flujo observado HLLC, con la
   selección causal de snapshot ya fijada.

La parte objetiva de B es la consistencia algebraica del balance, incluyendo
identidad de entradas, signos, etapas y orden de redondeo documentado. La parte
que sigue requiriendo decisión humana es qué magnitud de discrepancia numérica
es aceptable para el objetivo científico y cómo se relaciona con refinamiento,
CFL y el benchmark de referencia. No se propone ningún valor de threshold
post-hoc.

## Criterio preregistrable alternativo

Antes de una nueva ejecución, registrar una de estas opciones: (i) identidad
discreta HLLC en un conjunto de microcasos y en el fixture C3 a varias etapas,
con tolerancia derivada de una auditoría de redondeo; (ii) estudio de
refinamiento temporal/espacial del residuo B usando la misma implementación
independiente; o (iii) benchmark separado de HLLC-vs-Exact para A y balance
HLLC para B, con reglas de fallo fijadas antes de observar resultados. La
elección y cualquier threshold pertenecen al gate humano; esta propuesta no
los adopta.

Este documento no modifica `tasks.md`, OpenSpec, contratos aprobados ni
artefactos de resultados. Es una propuesta de siguiente paso solamente.
