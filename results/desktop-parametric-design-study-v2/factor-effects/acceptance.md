# Factorial 2×2 direct contrasts — acceptance

**Task:** `DESKTOP-PARAMETRIC-FACTOR-EFFECTS-V1`
**Evidence class:** Desktop integration using synthetic fixtures only. No solver execution, physical campaign, or experimental validation.

## Implemented

Desktop now exposes descriptive direct contrasts for a saved `FACTORIAL_2X2_V1` study in **Results → Compare**, and includes the same qualified section in its technical HTML report. It uses the four exact design combinations and the imported source artifacts bound by the manifest's run IDs, result hashes, identities, and RPM.

For ordered outcomes `y(A₁,B₁), y(A₁,B₂), y(A₂,B₁), y(A₂,B₂)`, it reports:

- Main effect A: `((y₂₁ + y₂₂) − (y₁₁ + y₁₂)) / 2`.
- Main effect B: `((y₁₂ + y₂₂) − (y₁₁ + y₂₁)) / 2`.
- Interaction: `(y₂₂ − y₂₁) − (y₁₂ − y₁₁)`.

The comparison is descriptive, not causal or predictive. It is withheld unless all four exact sources are terminal, hash and identity verified, `PERIOD_1`, at the same exact RPM, and compatible in the existing study comparison context. Metrics additionally require four defined values. Missing, stale, transient, nonperiodic, undefined, or incompatible points keep their rows and reasons but produce no numeric effects; no values are imputed or interpolated. Source/run results and solver contracts are unchanged.

A native-window review also exposed `None=…` labels when point rows omitted redundant labels. The factorial table now resolves labels from the factor definitions in the manifest and falls back to parameter IDs.

## Verification

- `python -m pytest tests/test_desktop_design_study.py -k factorial -q` — 5 passed.
- `python -m pytest tests/test_desktop_technical_report.py -k factorial -q` — 2 passed.
- Integrated relevant suite through `scripts/agents/run_logged.py` — **54 passed**, 0 failures, 213.172 s; summary at `tests-final-v2/parametric-factor-effects-final-v2.summary.json`.
- Native PySide6 window on the Windows platform, shown at 1480×881, with synthetic artifacts: 4 exact matrix rows, 9 contrast rows, then one synthetic point changed to `INSUFFICIENT_CYCLES`; all effects became blank while the four designs and nonperiodic classification remained visible.
- Screenshots and their SHA-256 values are recorded in `native-window-receipt.json`; replay with `capture_native_synthetic.py`.
- `git diff --check` — clean.

The formula example is synthetic test data only (power 10, 14, 20, 28 kW), producing A=12 kW, B=6 kW, interaction=4 kW. It is not a Dino prediction or validated engine result.

## Limitations

This is a direct-contrast view for the existing 2×2 design only. It does not calculate uncertainty, confidence intervals, causality, optimized designs, or predictive claims. V2/MUSCL, solver physics, and scientific validation contracts were not changed.
