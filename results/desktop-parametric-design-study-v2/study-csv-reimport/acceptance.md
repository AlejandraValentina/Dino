# Parametric study CSV reimport — acceptance

**Task:** `DESKTOP-PARAMETRIC-STUDY-CSV-REIMPORT-V1`
**Evidence class:** Read-only Desktop import of an existing synthetic CSV fixture. No solver execution or scientific campaign.

## Implemented

The existing single-study `DINO_PARAMETRIC_DESIGN_STUDY_V1` CSV export now opens from **Resultados → Importar resultados…** as a dedicated **read-only snapshot** in the comparison workspace. It is intentionally separate from runnable projects and engineering-run curves.

The importer validates the expected schema and columns, one consistent study identity and manifest hash, unique point indices, finite RPM/decimal cells, factor-value JSON, and the minimum hashes when the export marked a source verified. It computes SHA-256 for the exact imported CSV bytes. Numeric values remain text (including factors nested in JSON), so presentation does not round them again. Rows retain original execution class, periodicity, cycles, metric cells, source path/run/identity/result hashes, verification status, manifest path/hash, and the `scientific_validation` value.

Desktop displays the selected points in a dedicated snapshot table and a read-only detail panel. Nonperiodic states and blank metrics remain unchanged. Source checks are labeled as recorded at export; the snapshot does not claim to reverify paths or artifacts that may not be available on the receiving machine. It does not rebuild a manifest, mutate the active project, make curves from the imported geometry points, or start runs from the imported CSV. Normal result controls are hidden for the snapshot and restored when a regular result dataset is opened.

Unrecognized CSV schemas continue to the existing report importer. A recognized but malformed study CSV is rejected; it is not treated as a historical report or a runnable study. Factorial contrast CSV and cross-study comparison CSV have different schemas and remain separate, explicitly queued import work.

## Verification

- `tests/test_parametric_study_snapshot.py`: **5 passed** (schema, round-trip precision, read-only status, validation failures, service dispatch and Desktop rendering).
- Focused existing study-CSV export regressions: **11 passed**.
- Native Qt Windows Desktop opened the previously accepted synthetic 2-point study CSV through `ResultsPage.load()`. It rendered `PERIOD_1` and `INSUFFICIENT_CYCLES` separately, preserved the transient metric as blank, and presented the source state as “Fuente no cargada al exportar”. No solver was invoked.
- Input SHA-256: `3a2e71ee547e31b94257afbb1a6d98e5aef1b49dab193836b9d03ef766834f67`.
- After-correction screenshot SHA-256: `ebe8046a4b445c743b80ef0e27d6c9e308b02d7813c47dac2728efee82ef114e`.
- Native receipt: `native-window-receipt-v2.json`; reproducible runner: `capture_native_snapshot.py`.
- Existing fixture is explicitly synthetic and has source status `NOT_LOADED`; it demonstrates presentation and import only, not validation or prediction.

The full relevant suite result is recorded in `tests-final/parametric-study-csv-reimport-final.summary.json`.

## Limitations

This CSV is a portable, read-only snapshot, not a signed container. Its displayed file hash identifies the bytes imported in this session; the embedded manifest/source hashes and source-verification state are retained as exported metadata. Current source availability and scientific validation are not inferred from those historical fields.
