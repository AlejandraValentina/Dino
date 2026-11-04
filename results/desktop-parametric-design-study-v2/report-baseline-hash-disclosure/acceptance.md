# Compact baseline digest in cross-study report

The report header now shows the first 12 characters of the shared engine baseline SHA-256. Opening the disclosure reveals the exact 64-character digest. The source comparison JSON embedded in the report remains unchanged and contains the complete digest.

## Verification

- `python -m pytest tests/test_desktop_technical_report.py tests/test_desktop_design_study.py -q`: **46 passed**.
- A visible 1360 × 900 Desktop window exported a synthetic presentation-only comparison. No solver or scientific run was executed.
- Chrome rendered the exported HTML at 1360 px. Captures: `desktop-export-view.png` and `chrome-report-1360.png`.
- `acceptance-receipt.json` records the HTML and capture SHA-256 values and verifies the compact summary, expandable digest, and exact JSON digest.
- Source states, study manifests, scientific eligibility, and numerical values are unchanged.
