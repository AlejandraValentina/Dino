# Manifest-backed study budget and lifecycle summary

Results now shows the budget recorded in the study manifest, cumulative elapsed seconds when present, complete versus incomplete/not-started point counts, the saved study status, and a translated stop reason. Legacy manifests without timing data report it as unavailable. The UI explicitly says it does not estimate remaining solver time.

## Verification

- `python -m pytest tests/test_desktop_design_study.py tests/test_desktop_technical_report.py -q`: **47 passed**.
- Focused synthetic regression covers cancellation, partial/nonconverged and not-started points, missing budget/time fields, and the absence of runtime estimation.
- A visible Desktop Results window rendered the summary at 1360 px from a synthetic manifest. No solver execution occurred.
- `native-receipt.json` contains the screenshot SHA-256 and the observed summary text.
- No budget, solver, cancellation, checkpoint, or result data is written or reclassified by this presentation-only change.
