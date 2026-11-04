# Factorial contrast traceability

Selecting a `CONTRAST` row in an imported factorial CSV now presents its exact stored source run IDs and result SHA-256 values in the read-only detail panel. The binding is labeled as matching the four `POINT` rows; legacy rows without recorded bindings state that the values are absent and are not reconstructed.

## Verification

- `python -m pytest tests/test_desktop_design_study.py tests/test_desktop_technical_report.py -q`: **46 passed**.
- Tests cover a source-bound CSV round trip, exact ID/hash display on contrast selection, legacy missing bindings, and read-only behavior.
- A visible Desktop Results window opened a synthetic 2×2 CSV snapshot and displayed a selected contrast with four source run IDs and four result hashes. No solver execution occurred.
- `native-receipt.json` records the CSV and capture SHA-256 values and confirms source binding and read-only state.
