# Tasks — reference-engine-hybrid-harness

- [x] Freeze harness scope, observables, thresholds, streak rules and cycle cap
      in the machine-readable preregistration; commit before KT100 execution.
- [x] Implement configuration validation and reusable geometry/topology setup.
- [x] Implement cycle-relative event orchestration over existing P5-C/P6/P7.
- [x] Implement `REFERENCE_PERIODIC_CONVERGENCE_V1` and restartable detector.
- [x] Implement primary trajectory/cycle evidence, source bindings and JSON-safe
      checkpoint/restore.
- [x] Implement offline audit, conservation recomputation, replay comparison
      and malformed-evidence rejection.
- [x] Self-test period-1, period-2, detector persistence, initial-state
      checkpoint/restore, malformed evidence and conservation recomputation;
      P5/P6/P7/CFL product regression paths pass.
- [x] Create KT100 V2 configuration with complete provenance and run preflight.
- [ ] Execute the fixed five-point campaign; stop each case only on convergence
      or the preregistered maximum.
- [ ] Verify independent restart/replay and audit for campaign anchors.
- [ ] Compare V1/V2 as `MODEL_FORM_DIFFERENCE`; perform only preregistered local
      sensitivities after base campaign completion.
- [ ] Run relevant P4–P8 regressions, OpenSpec strict, `git diff --check`,
      `git lfs fsck`, and verify the frozen P9 hash.
- [ ] Independent punctual review; local commits only, no push/archive.

Initial status: preregistration approved by punctual independent review and
strictly validated. No KT100 V2 simulation has been run under this harness.
