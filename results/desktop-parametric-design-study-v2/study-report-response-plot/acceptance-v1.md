# Single-study parametric response in the technical report

## Implementation

The existing technical-report export now adds response panels for brake power, brake torque, and BMEP to scalar geometry studies. It does not flatten factorial studies or RPM envelopes. Each marker requires a scalar finite design value, a terminal manifest point, one imported result matching source run ID, artifact directory and SHA-256, current result/run/diagnostic-manifest integrity checks, exact RPM agreement, `PERIOD_1`, and a finite metric marked `DEFINED`.

The report lists excluded points and reasons per metric. It does not connect, interpolate, fit, recalculate, or present periodicity as physical validation. Missing metrics and transients remain visible as exclusions. A stale project study reference or changed result/diagnostic source artifact fails closed for the affected output.

## Verification

- Focused regression command: `python -m pytest -q tests/test_desktop_technical_report.py tests/test_desktop_design_study.py` — **45 passed** (logged summary: `tests-final-v3/single-study-report-response-plot-verified.summary.json`).
- Additional final test-only assertion verifies mismatch against the project’s stored study reference; the report unit module passes **15 passed** after that assertion.
- `py_compile` and `git diff --check` pass.
- Native Desktop export button produced the report from an explicitly synthetic fixture in a visible 1440 × 837 Desktop window. No solver or campaign ran.
- Chrome headless rendered the exported HTML at 1360 px. The screenshot shows two exact response markers, the transient and not-started exclusions, and empty torque/BMEP panels.
- Receipt: `native-study-report-v5-receipt.json`.
- HTML SHA-256: `472812b108e8a658f45caf2ea7f6ed4b20b2630c19617807fb2c16db5eba5142`.
- Browser screenshot SHA-256: `ff49a3326ec66a82c445270ab856b5ccdd194efffc11ab65c7bd7dcb3ff45c96`.
- Desktop screenshot: `native-desktop-export-v5.png`; rendered report screenshot: `chrome-rendered-study-response-v5.png`.

All plotted values and source artifacts in this GUI verification are synthetic presentation fixtures and remain `NOT_CLAIMED`; they are not solver output or scientific validation.

## Limits

The report graphic is intentionally limited to scalar studies. Factorial studies remain matrices, and RPM envelopes remain indexed by design and RPM. Multiple imported cycle rows for one source run are treated as ambiguous and excluded rather than selecting a cycle implicitly.
