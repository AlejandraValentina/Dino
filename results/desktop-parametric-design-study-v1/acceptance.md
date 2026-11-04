# Parametric design study V1 — acceptance evidence

## Functional result

The first Desktop parametric study executes a single supported factor: the
length of an existing partitioned exhaust section. Dino prepares an immutable
engine document for each selected value, then delegates each point to the
existing `DINO_ENGINEERING_RUN_V1` execution path. No solver or physical model
was changed.

The controlled synthetic integration used the new-engine Desktop fixture at
3000 RPM and one cycle per point. It completed in 19.015 s total: baseline
83 mm and design 85 mm. Both points are execution-complete but classified
`MAX_CYCLES_NONCONVERGED` with `INSUFFICIENT_CYCLES`; power, torque, BMEP and
their delta are undefined and render as dashes. The point importer reports
internal mass, species and energy conservation residuals around 1e-16 to 1e-15,
but `audit_status=NOT_PERFORMED`. This is a functional synthetic check, not a
periodic result, prediction, experimental validation or independent audit.

The existing Desktop results importer reopened both run artifacts. An explicit
zero-step study resume reverified run/result/diagnostic hashes and both solver
identities, set `reused_verified=true`, and did not launch another solver cycle.
The exact study manifest SHA-256 and per-point artifact hashes are recorded in
`receipt.json`; artifacts remain under the external `DINO_ARTIFACT_ROOT` and
were not rewritten except for derived study-manifest reuse metadata.

## Desktop evidence

[`captures/parametric-comparison-real-window-1360x900.png`](captures/parametric-comparison-real-window-1360x900.png)
was captured from a visible Windows Dino Desktop source window with the actual
study loaded. The comparison table shows both values and their nonconverged
states while withholding undefined metrics. The actual available display was
1440×900; Qt constrained the outer window to 1440×837.

## Tests

- `compileall` over the study module and touched Desktop pages: PASS.
- `tests/test_design_study.py tests/test_desktop_design_study.py tests/test_desktop_technical_report.py tests/test_packaging_build_provenance.py`: **16 passed**.
- `tests/test_desktop_rpm_curves.py tests/test_dino_desktop_ux_v2.py tests/test_engine_configuration_v1.py`: **33 passed**.
- Regressions include immutable baseline and distinct point identities, baseline/unique value validation, missing explicit displacement rejected without inference, cancellation/checkpoint resume, cumulative resumed-time accounting, prepared-config hash tampering, verified point reuse, Desktop menu/results integration, report output and packaging provenance.

## COM automation incident

The prior technical-report receipt records that its functional checks and
screenshots completed, then the Windows automation failed during a
post-close `pywinauto` UIA visibility wait. The retry encountered the UIA COM
provider before it could interact with Dino. This is consistent with the test
harness holding a UIA COM element after its native window/provider was torn
down, not a COM failure inside Dino. The current verifier closes by Win32
`WM_CLOSE` and observes `IsWindowVisible`, avoiding further UIA COM calls after
destruction. This session verified that source Desktop renders and opens the
study in the real Windows desktop, but could not rerun the pywinauto COM path:
`pywinauto` is absent from the active Python environment. The packaged Windows
verifier was not rebuilt or rerun.

## Limits

V1 exposes only existing exhaust-section lengths that pass Dino's
`PARTITIONED_LENGTH_EDIT_V1` adapter. It rejects missing explicit
`geometry_identity.displacement_cc` rather than deriving or inventing it. No
cross-study historical cache, multi-factor design, cylinder/port/crankcase
axes, prediction claim, or experimental validation is included.
