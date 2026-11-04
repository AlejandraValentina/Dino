# Technical report exclusion state labels

## Correction

The scalar study response report now translates internal execution and periodicity state codes in user-facing exclusion prose. For example, `INSUFFICIENT_CYCLES` is shown as “Ciclos insuficientes” and `NOT_STARTED` as “No iniciada”. The point table uses the same shared state-label mapping.

The original report JSON and embedded study manifest retain the unmodified state strings, so scientific records are not rewritten or hidden. Metric qualification remains PERIOD_1-only and source/hash checks are unchanged.

## Verification

- Focused regression: `python -m pytest -q tests/test_desktop_technical_report.py tests/test_desktop_design_study.py` — **46 passed** (`tests-final/report-exclusion-state-labels-final.summary.json`).
- Regression asserts that user-facing reasons contain translated labels, do not contain the internal token in those reasons, and still include the exact raw status and periodicity in the embedded original JSON.
- Native Desktop generated the HTML from a synthetic fixture at visible size 1440 × 837; Chrome headless rendered the actual exported report at 1360 px.
- Receipt: `native-study-report-v7-receipt.json`.
- HTML SHA-256: `288b8ca9a7d4002e25c08d5266f2d61f1055369c919164d918088a1edbeb5bd3`.
- Browser image SHA-256: `19a60d56abf14f49161ffc50d9d0f62053842e202958a6f8018f0499b24d331d`.
- Screenshots: `native-desktop-export-v7.png` and `chrome-rendered-study-response-v7.png`.

All values and artifacts in this visual check are synthetic presentation fixtures, marked `NOT_CLAIMED`; no physical run or campaign was made.
