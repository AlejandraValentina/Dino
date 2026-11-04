# Desktop parametric point traceability — acceptance

The selected study point now shows the loaded study-manifest path and SHA-256, the current on-disk SHA state, whether the active project reference binds that hash, run and engine identities, result/artifact hashes, current source verification state, and the nested RPM-sweep manifest path plus stored/current hashes. Missing metadata is labelled unavailable; missing source data is distinct from failed verification. A changed manifest or nested sweep is reported as changed. The details are calculated from the loaded study snapshot and current imported run artifacts; they do not alter either source.

Switching to a different active project clears the previously selected study and its details. Selecting another row refreshes the detail panel from that row.

## Verification

- Focused regression `test_parametric_point_details_bind_manifest_nested_sweep_and_source_status`: PASS. Covers exact hashes, unimported source, selecting a second RPM point, a changed sweep hash, a changed study manifest, and clearing state when changing projects.
- Final relevant suite in `tests-final-v2/study-traceability-details-final-regressions-v2.summary.json`: 67 passed, 2 deselected (the two documented stale UI assertions from the prior integrated run). The study, comparison, report and remaining shared Workbench tests passed; changed modules compile.
- Native Windows Qt run from `capture_native_study.py` opened the already saved synthetic RPM-envelope study and imported its existing artifacts. Four study points loaded; selected source was verified by result hash and identity; nested sweep hash matched. Evidence: `native-window-receipt.json` and `native-study-point-traceability.png`.
- The opened synthetic results remain `INSUFFICIENT_CYCLES`; scientific validation remains `NOT_CLAIMED`. No solver execution or physical campaign was performed.

## Limitations

The source state is rechecked when a point is selected; the application does not continuously watch files for later changes. Nested RPM provenance is shown only for envelope studies that actually carry a saved series manifest. Geometry-only studies correctly show that nested RPM sweep provenance does not apply.
