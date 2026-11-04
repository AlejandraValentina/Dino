# Cross-study response plot in the technical report

## Outcome

Added an observed response plot to the existing exported HTML report for cross-study comparisons. The report contains separate panels for brake power, brake torque, and BMEP. It renders only endpoints from exact RPM and operating-context pairs when both source points are classified `PERIOD_1` and the metric is finite. Markers are not connected, interpolated, fitted, or recalculated. Missing metrics, non-periodic endpoints, invalid RPM, and incompatible pairs remain excluded with their reasons listed; unpaired points and source manifests remain in the report.

## Verification

- Focused regression command: `python -m pytest -q tests/test_desktop_technical_report.py tests/test_desktop_design_study.py`.
- Native Desktop acceptance: `verify_native_report_export_v4.py` used the real Desktop report-export action with synthetic, explicitly labeled fixture data; no solver or physical campaign was run.
- HTML renderer check: Chrome headless rendered the exported HTML at 1360 px width. The browser screenshot shows the observed points, exclusion rows, and empty panels for metrics with no eligible values.
- Receipt: `native-report-export-v4-receipt.json`.
- Exported report SHA-256: `9d9171d46bb1ad5bbc65aadd8e120158658506e7de91d4d0ef70eeb782e5bdc3`.
- Rendered browser screenshot SHA-256: `140481eb04533348610c1a19b1d85a488a488c7fc9aa54a1f08a1fceba2d921b`.
- Evidence image: `chrome-rendered-response-plots-v4.png`.

The acceptance fixture retained `NOT_CLAIMED`, source manifest hashes, a non-periodic pair exclusion, and an unpaired point. Its values are synthetic presentation data and are not predictions or validation evidence.

## Residual limitation

The existing wide “Puntos y procedencia” report table is difficult to read at typical browser widths because it contains many provenance columns. This task did not change report data or provenance contracts; the issue is recorded for a future product task if prioritized.
