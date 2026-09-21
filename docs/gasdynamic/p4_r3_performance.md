# P4-R3 — optimización sin cambio científico

Orden5e36dbe4 acepta R2/P4B, no P4. Referencia escalar intacta:
motorsim/exhaust1d.py y motorsim/hybrid_exhaust.py. Receipt de aceptación
congela también benchmarkR2 y contratoP4C. Sin UI/JSON/P5 ni compilados.

## Perfil previo, antes de cambios mayores

Tres ventanas100µs con cProfile: apertura inicial, combustión350°, reapertura
cercana480°. MismaN250/CFL.4; la última usa snapshot reconstruido únicamente
para perfilar, no como checkpoint. No nueva campaña baseline completa:
se conserva263,328s y35379RHS/8861357HLLC/0HLLE históricos. CPU/RAM/cuentas
detalladas sólo para las ventanas nuevas; no inventar valores históricos.

Ventanas:17,531s instrumentados,591RHS; las cifras incluyen overhead de cProfile.
Costes inclusivos: primitivas30,67%, HLLC28,44%, MUSCL19,88%, fuentes0D3,47%,
CFL2,59%. Son ramas anidadas; no sumarlas con EOS ni validaciones internas.
Top self: generadoresEOS13,95%, all11,01%, validateEOS8,18%, comprensiones
exhaust7,52%, generadoresexhaust7,57%, HLLC6,52%, isfinite6,27%, MUSCL5,15%.

Clasificación aproximada, con solapamientos explícitos:
A matemática: HLLC/MUSCL/CFL ~51% inclusivo, mezcla operaciones y overhead.
B redundancia:2036 conversiones de malla frente a unos806 estados nuevos,
~60% de conversiones repetidas, potencial~18% del total instrumentado.
C objetos: comprensiones/generadores visibles >29% self, incluye aritmética;
no es una medición aislada del allocator. Conteo de allocations no disponible.
D evidencia: observe~12% inclusivo, principalmente primitivas ya contadas;
escritura gzip fuera de ventanas. No se eliminará evidencia contractual.
E bucles escalares vectorizables: las ramas primitivas/HLLC/MUSCL dominan ~79%
inclusivo. Esto satisface la condición de autorización NumPy del apartado8.
F geometría: CFL~2,6% inclusivo incluye widths recalculados; geometría0D es
menor y se cacheará sin alterar sus fórmulas. No atribuir todo ese2,6% a geometry.

## Bloques y equivalencia

Bloque1: caché acotada de primitivas por identidad de arrays inmutables,
geometría inmutable y fuentes0D por estado/tiempo idénticos. Mismas fórmulas,
validación de cada estado nuevo y SSPRK2. SCALAR_REFERENCE sigue disponible.
Comparar ciclo completo contra artifactR2 antes de continuar; perfil intermedio.
Bloque2 condicionado al perfil: batching float64 NumPy, mismas ramas/fallbacks.
No cambios CFL/eventos/reintentos/precisión/umbrales ni pérdida de ledgers.

Equivalencia: exigir mismo número de pasos/stages y eventos, mismos gates.
Para cambios de orden aritmético, registrar máximos absolutos/relativos por
campo; referencia de roundoff previa: rtol1e-10, atol1e-13 para estados/flujos
y rtol1e-10, atol1e-8Pa para presiones. Es tolerancia de comparación numérica,
no cambio de gates científicos. Si cambia materialmente, rechazar bloque.
Conservar todas las medidas, no escoger la más rápida. Performance exige
dos ciclos finales<=20s con margen; 20–30s: NEAR_TARGET; >30s:
COMPILED_BACKEND_DECISION_REQUIRED. Sin periodicidad/G2 antes de PASS.

## Bloque1 medido y autorización del batching

G1 completo226,773529s, speedup1,1612×: insuficiente. Equivalencia exacta en
todos los campos comparados, eventos, etapas, conteos y gates. Perfil intermedio
13,709230s instrumentados: HLLC36,67%, MUSCL24,29%, primitivas15,83%, fuentes
cacheadas1,41%. No extrapolar estos tiempos instrumentados al ciclo completo.

NumPy2.3.0 instalado sólo en venv, declarado en requirements-experimental.txt;
no dependencia de la ruta productiva/legacy. Batch EOS/MUSCL/HLLC/CFL y avances
independientes float64, conservando orden algebraico. Fallbacks excepcionales
delegan en HLLC/HLLE escalar congelado, con registros de cara/celda. BC y P3
siguen escalares originales. Inventarios conservan math.fsum.
