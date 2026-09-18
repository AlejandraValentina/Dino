# P1-R5E — evidencia completa y revisión científica R5

Adquisición de evidencia separada de adopción contractual. Dos integraciones
nuevas, solver y contratos P1–R4 intactos. Propuesta exacta en r5-candidate.md;
revisión independiente científica PASS registrada en scientific-review.json. Las tablas se calculan
desde finales, sin usar los estados parciales de300s.

## Matriz acústica 3x3
A_ref: pico de primitivas de integrales conservadas de referencia T03.
Eabs=|A-A_ref|, Erel=Eabs/A_ref; E_A=Eabs/10Pa.

| N | CFL | A Pa | A_ref Pa | Eabs Pa | Erel | E_A |
|---|---|---|---|---|---|---|
| 400 | 0.2 | 9.14443393229 | 9.98699441143 | 0.842560479141 | 0.0843657705642 | 0.0842560479141 |
| 400 | 0.4 | 9.1483281148 | 9.98699441143 | 0.838666296637 | 0.0839758451929 | 0.0838666296637 |
| 400 | 0.6 | 9.14993965974 | 9.98699441143 | 0.837054751697 | 0.0838144808351 | 0.0837054751697 |
| 800 | 0.2 | 9.62864623751 | 9.99674574511 | 0.368099507599 | 0.0368219335556 | 0.0368099507599 |
| 800 | 0.4 | 9.63078348491 | 9.99674574511 | 0.365962260199 | 0.0366081392415 | 0.0365962260199 |
| 800 | 0.6 | 9.63281855416 | 9.99674574511 | 0.363927190949 | 0.0364045660686 | 0.0363927190949 |
| 1600 | 0.2 | 9.84430525461 | 9.99918625753 | 0.15488100292 | 0.0154893607271 | 0.015488100292 |
| 1600 | 0.4 | 9.84536868558 | 9.99918625753 | 0.153817571947 | 0.0153830089755 | 0.0153817571947 |
| 1600 | 0.6 | 9.8463535082 | 9.99918625753 | 0.152832749329 | 0.0152845186991 | 0.0152832749329 |

| Pareja CFL | S400 | S800 | S1600 |
|---|---|---|---|
| 0.2_0.4 | 0.000389418250415 | 0.000213724740024 | 0.000106343097286 |
| 0.4_0.6 | 0.000161154493981 | 0.000203506925027 | 9.84822618193e-05 |
| 0.2_0.6 | 0.000550572744396 | 0.000417231665051 | 0.000204825359106 |

## Perfiles, fase y estabilidad

| N | CFL | L1 p | L2 p | Error velocidad relativo | Error posición m |
|---|---|---|---|---|---|
| 400 | 0.2 | 0.00341506124908 | 0.0119844783495 | 3.31494586006e-05 | 1.49172563702e-05 |
| 400 | 0.4 | 0.00347541441305 | 0.0121360003189 | 3.99537615174e-05 | 1.79791926828e-05 |
| 400 | 0.6 | 0.003707094851 | 0.012619885546 | 0.000105221771474 | -4.73497971631e-05 |
| 800 | 0.2 | 0.00120798645828 | 0.00460879589863 | 3.72688864354e-05 | 1.6770998896e-05 |
| 800 | 0.4 | 0.00121933551006 | 0.00464874454574 | 3.81443152386e-05 | 1.71649418574e-05 |
| 800 | 0.6 | 0.00125128513104 | 0.00471622058713 | 2.94522145396e-05 | 1.32534965429e-05 |
| 1600 | 0.2 | 0.000350750888028 | 0.00150683269947 | 3.09070269449e-05 | 1.39081621252e-05 |
| 1600 | 0.4 | 0.000355799198152 | 0.00152029670109 | 3.08827981534e-05 | 1.3897259169e-05 |
| 1600 | 0.6 | 0.000376836004091 | 0.00154533622456 | 3.30278779008e-05 | 1.48625450554e-05 |

| N | CFL | Máximo balance paso | Máximo balance etapa | Admisible | HLLC | HLLE | Tiempo s |
|---|---|---|---|---|---|---|---|
| 400 | 0.2 | 3.11150297412e-16 | 1.59385508251e-16 | True | 718998 | 0 | 18.750 |
| 400 | 0.4 | 2.2948451126e-16 | 1.5177958122e-16 | True | 359898 | 0 | 9.219 |
| 400 | 0.6 | 2.03413105613e-16 | 1.48542315889e-16 | True | 240198 | 0 | 6.125 |
| 800 | 0.2 | 2.6519347554e-16 | 1.55903605274e-16 | True | 2877998 | 0 | 74.203 |
| 800 | 0.4 | 2.39194227358e-16 | 1.55744243832e-16 | True | 1439798 | 0 | 37.515 |
| 800 | 0.6 | 1.75121884091e-16 | 1.52746131192e-16 | True | 1197701 | 0 | 30.469 |
| 1600 | 0.2 | 4.65742228849e-16 | 1.59160444382e-16 | True | 11515998 | 0 | 304.844 |
| 1600 | 0.4 | 4.91126417582e-16 | 1.59498039492e-16 | True | 5759598 | 0 | 153.578 |
| 1600 | 0.6 | 1.22263010731e-16 | 1.57088637639e-16 | True | 4838574 | 0 | 125.234 |

Los errores E_A, L1p y L2p disminuyen en ambas transiciones para cada CFL.
La fase no es monótona en todos los casos: CFL.2 aumenta de400 a800 y .6
cambia de signo; no se oculta. Todos los errores relativos de velocidad están
entre2.945e-5 y1.053e-4, dentro del límite original1e-2; sus valores finos
están cerca de3.1e-5–3.3e-5 y no hay separación sistemática entre CFL.
No se impone una nueva monotonía de fase. La referencia es acústica lineal
de pequeña amplitud, no una solución exacta del Euler no lineal a amplitud finita.

La sensibilidad .4/.6 crece400→800 pero cae800→1600. Las otras dos parejas
disminuyen en ambas transiciones; las tres son menores en1600 que400.
Esto, junto con los errores de perfil/pico y conservación/admisibilidad,
es compatible con régimen preasintótico, no demuestra causalidad ni un límite
asintótico universal. No se elimina N800 ni se agrega una cota ajustada a datos.

## Fundamento matemático del delta propuesto
SSP preserva una propiedad convexa de estabilidad del paso Euler, bajo sus
hipótesis, a discretización espacial fija. No ordena diferencias entre CFL
sobre distintas mallas. Fuente primaria: Gottlieb, Shu y Tadmor2001, §2:
https://www.cfm.brown.edu/people/sg/SSPsiamreview.pdf .

Contraejemplo lógico independiente, no ajuste al solver: e_a=h² y e_b=h³
convergen monótonamente; para h=.9,.45,.225, su diferencia absoluta vale
.081,.111375,.039234375. Por desigualdad triangular,
|A_a-A_b|<=|A_a-A_ref|+|A_b-A_ref|: convergencia individual a referencia
común implica convergencia de diferencias, no monotonía en cada transición.
Minmod cambia de rama/anula pendientes en extremos y el máximo celular
es sensible a fase/malla; son mecanismos plausibles, no una identificación
causal demostrada. No se afirma TVD universal de este Euler/HLLC.

El cambio propuesto retira explícitamente la garantía transición por transición
para segundo orden; NO es equivalente a R4. Conserva error de referencia
estrictamente decreciente por CFL, todos los gates padre y S_fina<S_gruesa
para cada pareja. Los perfiles corroboran que convergencia del pico no está
ocultando deterioro del perfil. FIRST_ORDER mantiene R4 íntegro.

## T10 y adquisición
- order_100_200_density_L1: 1.86132927197.
- order_100_200_fresh_L1: 1.86050063189.
- order_200_400_density_L1: 1.89430821594.
- order_200_400_fresh_L1: 1.89411641807.
- order_400_800_density_L1: 1.90660166169.
- order_400_800_fresh_L1: 1.90688958599.

T10_800: 526.656s; pasos12541; RHS25082; HLLC20065600; HLLE0; dt [1.93733219992e-07, 1.16954323005e-06].

T03_0.2_N1600: 304.844s; pasos3601; RHS7202; HLLC11515998; HLLE0; dt [1.1379648046e-07, 3.6661003203e-07].

Timeout anterior300s; nuevo600s exclusivamente para estos casos. Sin optimizar.
Primer intento de preparar fase falló antes de comandos/integraciones por
lectura cp1252 del roadmap; corregida lectura UTF8. Preservado en setup-failure.
Normalización de ruta relativa corregida en reproductor offline antes de emitir
study.json; ninguna repetición física por ese error. No reparaciones científicas.
El runner nativo conserva BLOCKED/review_not_approved: no tiene reviewer real
conectado. No se sustituye su archivo; dictamen independiente se adjunta separado.

Evidencia: acquisition/artifacts/cases, provenance en study.json (hash de cada
artefacto, configuración, inputs y referencia; solver compatible4620200).
Las ocho soluciones acústicas reutilizadas y T10 anteriores conservan originales.
Comando de reproducción: `.\.venv\Scripts\python.exe -m dev_orchestrator.p1_r5_review --acquisition results/p1-r5e-20260918/acquisition --output results/p1-r5e-20260918/study.json`.

Decisión: **P1_R5_PASS_CFL_SECOND_ORDER_CONTRACT**. Adoptado el delta exacto
1D_CONTRACT_V1_R5 antes del cierre P2. R4 conserva FAIL histórico en segundo
orden; no se reescribe evidencia anterior. Evaluador reforzado para exigir12/12
y todas las comparaciones, observación independiente sin cambios numéricos.
