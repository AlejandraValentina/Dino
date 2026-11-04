DINO_PARAMETRIC_RPM_ENVELOPE V1 — acceptance

Capability: Desktop now prepares an explicit, uniform RPM grid for each explicit geometry design and delegates each geometry group to the existing power-curve sweep runner. Every design × RPM point retains its run identity, path, periodicity, classification, checkpoint state and result artifact hash in the study manifest. The matrix is capped at 30 combinations, 5 geometry points, 6 RPM points and 600 s aggregate; the aggregate budget is allocated evenly across design groups, with no silent redistribution. Existing per-point, memory, sweep and cancellation limits remain in force.

Results: the project-linked manifest reopens through the Results selector. Existing RPM performance curves remain the primary RPM visualization. The design response plot is suppressed for mixed RPM data so the same geometry is never reduced to a misleading one-dimensional response. The comparison table groups all RPM rows under the same design identity and calculates deltas only against baseline at the same exact RPM. Undefined/nonperiodic metrics remain blank and their classifications remain visible.

Verification:
- Regression: `tests/test_design_study.py tests/test_desktop_design_study.py tests/test_power_curve_sweep.py`: 35 passed in 154.89 s.
- Final focused pass: 7 passed in 52.89 s for RPM envelope, cancel/resume, project-manifest registration and tamper rejection. It includes the explicit no-overwrite-on-cancel assertion and rejection of changed manifest metadata before reuse. The earlier 35-test regression pass predates this last metadata guard.
- `compileall` passed for implementation, tests and evidence scripts.
- Storage preflight passed for the artifact root with 2 GiB estimated output and 2 GiB reserve.
- One real synthetic engineering integration: two geometry settings (83 / 88 mm exhaust section) × 3000 / 4000 RPM, one cycle per point, 512 MiB process cap, 45 s per point and 180 s total. It completed in 48.406 s. The existing importer reopened all four run artifacts. All four report `MAX_CYCLES_NONCONVERGED` / `INSUFFICIENT_CYCLES`; power, torque and BMEP remain undefined. This is a functional synthetic smoke only, not a periodicity or predictive validation.
- Native Windows Dino Desktop source window: opened the manifest from the project study selector, imported four points, displayed four table rows under two consistent design labels and suppressed the mixed-RPM 1D response. The receipt binds the screenshot SHA-256 and manifest SHA-256.
- The first logged-run bootstrap failed before solver import because the child process lacked the repository import root; no solver was called. The evidence script was corrected relative to its own path, then the single integration completed. A first UI wait condition exited before the asynchronous import; it was corrected and the final native-window check passed.

No solver source, equations, classification rules, thresholds, experimental evidence, or V2/MUSCL settings were modified. The synthetic results are explicitly unvalidated.
