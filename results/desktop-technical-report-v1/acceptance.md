# Desktop technical report and reproducible packaging evidence

## Delivered

- The Results view can export a standalone HTML technical report from imported result records; it does not rerun the solver.
- The report records source provenance, schema/validation state, project and selected variant context, exact RPM records, status/periodicity and available metrics. Exact raw source rows are retained in the report appendix. Pair differences are descriptive and use exact common RPMs; compatibility warnings remain visible.
- SVG plots are included only when the available records expose metrics under the existing periodic classification semantics. Synthetic, legacy, exploratory, and validation-not-performed status are labeled; no experimental claim is inferred.
- Windows trial builds now carry a deterministic inventory of packaged inputs and reject changes in that input scope, while unrelated dirty work remains untouched and is summarized in build metadata.

## Verification

- Focused report/build-provenance tests: 12 passed at the initial implementation.
- Expanded relevant Desktop regressions: 50 passed, 1 skipped (the skip is recorded by pytest); report/build focused regressions after the legacy classification fix: 7 passed.
- A first broader invocation including an older Desktop test hung and was interrupted; it is not counted as a pass.
- The final Windows trial was built from commit `95a4574dd463fb3b230d26eeb2ac8d49c189a611`. The package metadata says `trial=true`, `packaged_inputs_clean=true`, 226 inputs, manifest SHA-256 `fbec6ec8df7de96a71dfcd42e80aaa8ef46481cc43993b51cd97e8f40eaeb149`. It was built on Windows 10 x64 with Python 3.11 / PyInstaller 6.22.3.
- In the actual packaged app, the synthetic 30-point CSV and paired JSON were imported, the results view showed curves/status, and the UI exported the HTML report. The report contains all 30 original records (27 classified `PERIOD_1`), SVG, exact IDs/hashes, and synthetic / validation-not-performed labels.
- Captures and hashes, including the EXE, ZIP, report, screenshots and build metadata, are in `receipt.json`. Artifacts are under the external artifact root at `Windows/...` and `desktop-technical-report-v1/...`.

## Automation caveat

The GUI automation returned nonzero after the functional assertions and second screenshot, during the post-close pywinauto COM visibility wait. A retry encountered a stale UI Automation COM provider before interacting with the app. Therefore the functional interactions and resulting artifacts are evidenced, but the automation process itself did not exit cleanly; no fully green packaged GUI run is claimed. The verifier was adjusted to send `WM_CLOSE` and count top-level app windows, but this environment's UIA close wait remains unreliable.

## Limits / next useful product step

Current manual variants, RPM sweeps, exact-RPM comparisons, history, CSV exchange and technical report cover important engineering workflows. A general parameter-space/design-of-experiments explorer is still absent: RPM sweep varies operating point, not engine design variables. The report also summarizes selected points rather than reproducing every pressure/flow trace. These limits do not alter the solver or its evidence contracts. No physical campaign, new prediction claim, or model promotion was made here.
