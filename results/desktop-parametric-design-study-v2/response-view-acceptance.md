# Parametric response view — acceptance

## Implementation

The Desktop comparison panel now includes a response plot selector for brake power, brake torque and BMEP. For single-factor studies, the plot uses parameter values on the x axis and includes only imported points classified PERIOD_1/PERIOD_2 whose selected metric status is DEFINED and whose value is finite. Points use markers without connecting, fitting or interpolating them. Baseline and alternative values remain separated, and absent/nonperiodic points stay visible in the table with their original state.

Two-factor factorial studies deliberately do not produce a one-dimensional response curve. The panel explains that it retains the four-point matrix in the table and does not infer factor effects. Existing run/result records are read-only; no metric is recomputed.

## Verification

The expanded regression set passed **58 tests** in 144.48 s across design study, Desktop, technical reports, crankcase, port geometry, engine configuration and functional exhaust comparison. Response-specific assertions verify periodic filtering, missing transient values, marker-only series, selected-metric switching, factorial refusal to collapse dimensions, and the row/table status display. `compileall` passed for the plot and results page.

Synthetic fixtures were used for presentation tests. The real 2×2 integration remains documented separately and all four results were nonconverged, so no response metrics were plotted from it.

## Limitations

No fit, optimizer, uncertainty propagation or response surface is offered. Factorial response modeling and design-space visualization remain outside this vertical slice. Experimental validation is still external and this view makes no predictive claim.
