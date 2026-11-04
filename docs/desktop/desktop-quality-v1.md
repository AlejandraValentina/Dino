# Desktop quality corrections — 2026-11-04

This change improves result presentation and traceability in the existing
PySide6 Desktop. It does not change the solver, physical models, result values,
periodicity classification, project schema, or scientific evidence.

## Changes

- Measurement-comparison CSV export now writes the underlying comparison rows,
  rather than the shortened strings rendered in the table. Imported values,
  uncertainties, and calculated differences retain Python's round-trip float
  representation. The on-screen table remains compact.
- The evidence drawer labels the actual imported source kind and source path
  when present. It no longer substitutes “audited/history” when the path is
  absent, nor labels the currently open engine's hash as the selected result's
  configuration hash. Result hashes continue to come from the selected point.
- Results curves now explicitly explain when two selected series have no exact
  RPM pair; no difference row or interpolation is implied.
- The performance-points table uses compact Spanish headings, full header
  tooltips, and columns that stretch to the available width. Curve controls
  have bounded widths and retain full explanations in tooltips.
- Two stale UX assertions were updated to reflect the existing Spanish source
  notice and the current component selector (the old duplicate navigation bar
  is intentionally hidden).

## Verification

Focused regression tests:

```text
13 passed
```

Coverage includes precision-preserving measurement and curve CSV export,
result-source labeling, missing exact-RPM pairs, exploratory opt-in, and the
updated small-window/navigation assertions. The expanded pre-correction Desktop
suite produced 35 passes and the two stale UX assertions described above; both
were then updated and passed in the focused run. No scientific campaign or new
solver calculation was run.

The actual `DinoDesktopWindow` was launched, shown, resized, and captured at
980×680 and 1360×900. Results and comparison views had no horizontal overflow
in either size. The UI fixture is explicitly `SYNTHETIC_UI_FIXTURE`; it is not
solver output or physical evidence. The smoke script uses isolated temporary
Qt settings and does not write a project or artifact.

Captures and their SHA-256 hashes are recorded in
`results/desktop-quality-v1/visual-receipt.json`.

## Limits

- The visual run used the current source application under Qt's offscreen
  platform. It was not a new packaged Windows build.
- This work did not make any synthetic, historical, exploratory, or
  non-converged result physically validated.
- Existing scientific-data availability and the limits of geometry carried by
  historical result files are unchanged.
