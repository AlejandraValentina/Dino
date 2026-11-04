# Parametric design exploration V1/V2 — factorial 2×2 acceptance

## Delivered capability

Desktop now offers **SIMULAR → Más opciones → Estudio factorial de diseño 2×2**. It composes exactly two existing adapters, each at the engine baseline and one explicit alternate level. Four immutable configurations are generated in baseline / A / B / A+B order. Every point goes through the existing engineering runner, artifact importer, cancellation, manifest and resume path. The project base engine is not mutated. The maximum is four points; the existing per-point and aggregate budgets and memory limit still apply.

The result table and technical HTML report show both factor names, values and units for each design. They do not report main effects, interaction terms, fitted curves or interpolated values. Metrics are shown only when the imported result marks them defined and periodic; otherwise they remain absent. All points remain EXPLORATORY with explicit synthetic-assumption provenance.

## Real synthetic integration

A controlled integration run used a synthetic engine, transfer-port top (38.4086 / 39.4086 mm) and crankcase BDC volume (356.0807 / 361.0807 cm³), 3000 RPM, one cycle/design, 45 s point budget, 180 s aggregate budget and 512 MiB process limit. Storage preflight passed for a 2 GiB estimate with a 2 GiB reserve. The run took 50.187 s and completed four engineering executions. The existing importer then reopened all four artifacts: each was `MAX_CYCLES_NONCONVERGED` / `INSUFFICIENT_CYCLES`, one cycle, with brake power, torque and BMEP `UNDEFINED`. The exact run and artifact hashes are in `factorial-receipt.json`; full output is in `factorial-run-logged/`.

This verifies adapter composition and result plumbing only. It is not a periodicity campaign, experimental validation, or predictive claim.

## Automated verification

- Expanded study, Desktop, technical-report, crankcase, port, engine-configuration and exhaust-comparison suites: **56 passed** in 147.67 s.
- Focused factorial preparation, budget/topology rejection, cancelled-manifest reopen, UI preflight and report rendering: **10 passed**.
- `compileall` passed for the changed implementation modules.
- The first `run_logged` attempt stopped before any solver work because the standalone evidence script lacked the repository import path. The script now resolves the repository root from its own location; the single accepted smoke run then passed. No duplicate solver run was caused by the failed bootstrap.

## Scientific and product limits

The factorial is a descriptive 2×2 collection of existing solver runs, not an optimizer or response-surface model. Only one alternate level per factor is supported. It can combine only two parameters already exposed by consistency-preserving adapters. No solver, physical equations, tolerances, experimental contracts or existing results were modified. Validation against measured data remains blocked on external records; no predictive claim is made.

The earlier COM/UIA incident remains classified as report-window teardown automation after the UIA provider was destroyed, not a Dino solver or report-generation COM failure. See the existing V1 acceptance record for the observed sequence; this change did not re-open or alter that diagnosis.
