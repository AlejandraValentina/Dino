# Factorial contrast CSV source-binding roundtrip

## Defect and correction

The factorial CSV exporter already declared the source-binding columns, but built their values from the wrong object shape: verified outcomes are nested `{manifest, imported}` records, not flat rows. As a result, all nine `CONTRAST` rows contained four null IDs and four null hashes despite four correctly bound `POINT` rows. The read-only importer therefore truthfully classified those exports as missing bindings.

Contrast rows now derive their ordered source ID and result-hash arrays from the exact four `POINT` rows that are written to the same CSV. Existing historical CSVs without those fields remain accepted only with an explicit missing-binding status; no values are inferred for them.

## Verification

- `python -m pytest -q tests/test_desktop_design_study.py tests/test_parametric_factorial_snapshot.py` — **37 passed**.
- Regression directly compares every contrast's source arrays with the four source fields on the CSV point rows.
- End-to-end regression writes the factorial CSV, reimports it as a read-only snapshot, checks all 4 POINT/9 CONTRAST rows and `MATCHES_POINT_ROWS`, and checks the Desktop snapshot view reports that the four source POINT rows are linked.
- Existing nonperiodic, source-tampering, immutable export, and legacy missing-binding tests remain in the same focused suite.
- `py_compile` and `git diff --check` pass.
- Inputs are synthetic source-verification fixtures. No solver, campaign, or physical result was generated.

## Scope

This changes CSV provenance binding only. Contrast values, formulas, qualification rules, scientific status, and solver behavior are unchanged.
