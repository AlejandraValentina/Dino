# Parametric study V2 — acceptance evidence

## Capability added

V2 adds exact single-factor adapters for transfer-port top, height, width and
discharge coefficient, the intake-port discharge coefficient, and explicit
crankcase BDC volume. Port definitions are rebuilt by Dino's existing
`TwoStrokePortSet`; generated port profiles and the displayed transfer opening/
effective-width or intake effective-area summaries stay synchronized. Crankcase
BDC volume is applied through `CrankcaseGeometry`/`SliderCrankChambers2T`, its
volume/compression metadata is refreshed, and initial species inventories are
rescaled to preserve the engine editor's existing density and composition
policy. The solver, equations, mesh topology and project persistence schema
were not changed.

The interface labels each selected axis with its native unit. Values receive
explicit `SYNTHETIC_ASSUMPTION` parametric-point provenance and the parent
engine identity. Unsupported fields are not offered: exhaust windows remain
excluded because their summaries bind multiple power-valve positions; cylinder
bore/stroke/rod length, cylinder compression ratio, intake dimensions and
multi-factor designs remain outside this adapter set.

## Controlled synthetic run

The source Desktop engineering workflow executed a two-point, one-cycle study
at 3000 RPM varying `port:primary-window:top_mm` from 38.4086278447 to
39.4086278447 mm. Both solver runs ended normally at the requested one-cycle
horizon, but both are `MAX_CYCLES_NONCONVERGED` / `INSUFFICIENT_CYCLES`.
Power, torque and BMEP remain undefined; the result page shows dashes and no
power delta. Internal conservation is carried from the workflow and visible in
Desktop, while `audit_status=NOT_PERFORMED`.

The study manifest SHA-256, engine identities, result hashes and per-point
conservation residuals are in `receipt.json`. Raw run artifacts remain at the
external artifact root. No artifact was re-run to obtain a target output.

## Windows Desktop evidence

[`captures/parametric-transfer-port-real-window.png`](captures/parametric-transfer-port-real-window.png)
shows the actual source Desktop window on Windows, with the loaded study under
RESULTADOS → Comparar. It shows both selected port-top values, nonconverged and
insufficient-cycle states, no definitive performance values, and the existing
transient warning. The actual available screen was 1440×900 and the captured
outer window was 1440×837.

## Automated verification

`compileall` passed for `motorsim/design_study.py` and
`motorsim/desktop/execution_page.py`. The combined focused and model/Desktop
regression suite reported **77 passed** in 182.17 s. It covers study adapters,
unit-aware Desktop selection, port event/area regeneration, crankcase volume
and initial species fractions, safe result imports, reports, packaging
provenance, existing port/crankcase models, exhaust comparison, RPM Desktop
flows and compact UI.

After relocating the duplicate-values assertion back into its dedicated test,
three focused checks passed: duplicate/baseline input rejection, transfer-port
adapter and crankcase adapter (**3 passed**).

## Limits and scientific status

This is functional integration evidence only. A one-cycle run does not establish
periodicity; conservation shown here is internal workflow evidence and was not
independently audited. Neither this study nor any result is experimental
validation or a predictive-performance claim. The legacy starter project
without explicit `geometry_identity.displacement_cc` continues to fail closed
rather than receive an inferred displacement. The prior report-export COM/UIA
teardown issue is analyzed in V1's acceptance record; this V2 visual check used
the live source application and no packaged build.
