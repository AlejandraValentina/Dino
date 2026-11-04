# Factorial contrast CSV export — acceptance

**Task:** `DESKTOP-PARAMETRIC-FACTOR-EFFECTS-CSV-EXPORT-V1`
**Evidence class:** Native Windows Desktop integration with explicitly synthetic fixtures. No solver execution, physical campaign, or experimental validation.

## Delivery

`Results → Comparar` now exposes **Exportar matriz y contrastes factoriales CSV** only when a `FACTORIAL_2X2_V1` study is open. The standalone schema `DINO_PARAMETRIC_FACTORIAL_EXPORT_V1` contains exactly 13 records:

- Four `POINT` rows with factor IDs/labels/levels, exact RPM, execution and periodicity classification, cycles, source project/run/path, engine identity, result/artifact SHA-256, manifest path/hash, scientific-validation label, metric status and a qualification field.
- Nine `CONTRAST` rows (three metrics × two main effects and one interaction), including exact definition, units, source run IDs/hashes, status and reason.

Before writing, Desktop re-reads and hashes the manifest, verifies it still matches the project-bound study reference and the opened manifest, then verifies the four exact source artifacts and identities. Files are opened exclusively (`x`) so export never replaces an existing file. Numeric cells use Python's shortest round-trip float serialization; the existing source values and result artifacts are not modified.

Transient/nonperiodic points remain in the four source rows with their execution state; their performance values are blank and qualified `WITHHELD_NONPERIODIC`. Their contrast values remain blank with `UNAVAILABLE` and a reason. A `NOT_CLAIMED` scientific label is preserved in every record. The CSV is a reproducibility export, not a predictive claim or an automatic replacement for the existing single-study CSV importer.

## Verification

- Focused CSV regression: **3 passed**.
- Factorial regression: **8 passed**; report regression: **2 passed**.
- Integrated design-study, Desktop and technical-report suites via `scripts/agents/run_logged.py`: **57 passed**, 0 failures, 209.125 s. Summary: `tests-final/parametric-factor-effects-csv-final.summary.json`.
- Native PySide6 Windows window at 1480×881: clicked the visible factorial export control and reopened the resulting CSV. Receipt confirms 4 verified point rows, 9 contrast rows, schema, manifest binding and `NOT_CLAIMED`: `native-smoke-20261104T200320Z/native-window-receipt.json`.
- Native CSV SHA-256: `753e67bf1aaef28effdada5cf455c744310161300ae0c9ddf67821e9a356b834`.
- Native screenshot SHA-256: `930c866fd200d6b2b930f03bfacf89e24801558431b763c6a7a60a302ef56ac6`.
- Tampered manifest and existing output paths are rejected by regressions; the previous file bytes remain unchanged.
- `git diff --check` clean.

The native fixture's contrast values are intentionally synthetic and exist only to verify serialization and UI wiring. Its source label and project ID identify it as synthetic; it is not a Dino prediction or engine validation.

## Limitations

This export covers the existing 2×2 study only. It does not make the file importable as a saved study, infer missing points, estimate uncertainty, or establish causality/predictive validity. Solver, physical models and validation contracts were untouched.

## Reproduction

Run `python results/desktop-parametric-design-study-v2/factor-effects-csv/capture_native_export.py` from the repository root in an unlocked Windows desktop session. It creates a new timestamped synthetic fixture directory and does not run the solver or overwrite previous evidence.
