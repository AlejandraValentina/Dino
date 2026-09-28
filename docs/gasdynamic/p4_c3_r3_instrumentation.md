# P4-C3-R3 — adquisición focal y auditoría independiente

## Alcance

Se ejecutó una única adquisición N=100, CFL=0,2, con el fixture C2 existente
hasta `t=0,004 s`. No se modificaron física, operador, malla, CFL, eventos,
umbrales ni camino productivo. P9 permanece STOPPED/NOT AUTHORIZED.

## Instrumentación

Cada etapa SSPRK2 conserva estados conservativos y primitivos, estado de cámara,
`dt` y la geometría (`areas`, `volumes`, `faces`, `centers`). El auditor no
consume `momentum_face_fluxes`, `momentum_source_sum` ni ningún término de
momento generado por el operador. Recalcula offline la cara izquierda mediante
la referencia ExactRiemann independiente, la cara derecha desde la presión de
pared y la fuente `sum(p_i*(A_right-A_left))`; las unidades son N para fuerzas
y kg·m/s para momento.

`wave_speed_middle` identifica velocidad de onda. Nunca se presenta como
presión; `p_star` sólo aparece como el valor separado de ExactRiemann.

## Resultado de la única adquisición

La revisión supervisora detectó antes del cierre definitivo que el primer
cálculo de auditoría era inválido: el comparador mezclaba `stage_b` con el
flujo observado de `stage_a`, y la reconstrucción de la pared usaba `A*p_last`
en vez de la reacción de pared reflectante de Riemann. Sus números no son
resultados finales y fueron regenerados tras corregir ambos defectos. No se
modificaron física, operador, malla, CFL, eventos, umbrales ni camino
productivo. Artefactos vigentes: `results/p4-c3-r3-20260928/`.

* Retorno: `PASS`; primer sample admisible en `t=0,00265438651636827 s`, con
  flujo de masa positivo `0,000269858712383056 kg/s`.
* Conservación: `PASS`; residuo normalizado máximo
  `1,3929103469155642e-15`, frente al criterio existente `1e-10`.
* Admisibilidad: `PASS`.
* ExactRiemann: `INCONCLUSIVE`; errores relativos por componente
  `(mass,momentum,energy,species)` =
  `(2,258600676877695e-07, 4,112451082484666e-07,
  8,368494691992387e-04, 1,129300338438305e-07)` y máximo
  `8,36849469199239e-04`. No existe un threshold contractual aprobado para
  igualdad HLLC–ExactRiemann y no se inventó uno.
* Balance independiente de momento: `INCONCLUSIVE`; residuo absoluto máximo
  reconstruido `4,437570053531734e-05`. No existe threshold cuantitativo
  aprobado para este cierre y no se inventó uno.

## Decisión

`P4_SCI_C3_INCONCLUSIVE`. El auditor clasifica automáticamente: no contiene
un PASS codificado. Al quedar C3 inconcluso, E13 no se ejecutó ni se aplicó a
G2; no hubo una nueva campaña. La propuesta E13-R1 conserva la aprobación
humana documentada de A–J, pero su evaluación sigue bloqueada por el gate C3.
