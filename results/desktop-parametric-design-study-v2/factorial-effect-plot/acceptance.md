# Gráfico de efectos factoriales 2×2

Estado: integrado y verificado con fixtures sintéticos; no se ejecutó solver ni campaña científica.

## Capacidad

Resultados ahora muestra un gráfico horizontal firmado para los tres contrastes factoriales existentes por métrica. Potencia, torque y BMEP usan escalas separadas en sus unidades correspondientes y comparten un cero visual dentro de cada grupo. Efectos positivos y negativos se distinguen por dirección y color. Si la métrica no pasa las verificaciones existentes (cuatro fuentes exactas, hashes/identidades, PERIOD_1 y condiciones compatibles), no se dibujan barras ni se reemplazan los valores ausentes por cero.

La tabla numérica conserva valores, estados y fórmulas como fuente exacta; el aviso mantiene explícito que son contrastes descriptivos y no validación predictiva. No se alteró `_factorial_effects_from_study` ni ningún resultado guardado.

## Verificación

- `python -m pytest tests/test_desktop_design_study.py -q -k 'factorial_effect_plot_uses_verified_signed_values_and_renders or factorial_ui_keeps_four_rows_and_shows_unavailable_effects_for_transient_points or factorial_contrasts_require_four_verified_periodic_exact_context_points'` — 3 passed.
- `python -m pytest tests/test_desktop_design_study.py -q` — 36 passed.
- `git diff --check` — limpio.
- `factorial-effect-plot-synthetic.png` es una captura renderizada con Qt sobre Windows (1440×900), generada con valores sintéticos positivos/negativos y un grupo deliberadamente no disponible. Sirve sólo como evidencia de presentación, no representa un motor ni predice desempeño.

## Limitaciones

La figura no incorpora incertidumbre, ajuste, inferencia causal ni validación. Cada métrica se autoescala por separado; la advertencia lo declara para evitar comparar visualmente longitudes entre unidades distintas. La tabla conserva la lectura precisa.
