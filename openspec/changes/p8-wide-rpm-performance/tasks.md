# Tasks

- [x] Record supervisor authorization and the bounded P8-only scope; keep P4
      blocked, experimental validation not performed, independent review
      pending, and P9 stopped.
- [x] Preserve the approved S2T-0D-01 mechanics and frozen P5-C/P6/P7 fixture;
      use exactly two fixed preparation cycles, with no periodic convergence,
      warm start, or steady-state claim.
- [x] Implement two deterministic unmeasured preparation cycles 180->900 with
      P7 disabled, CFL 0.4, repeated mechanical event cuts, clean accounting
      reset, and exact geometry-only rebase 900->180.
- [x] Use one repeated authoritative event-cut builder for preparation,
      measured execution, and restart continuation; include the exact 350/390
      P7 boundaries and 370 restart cut only where P7 is enabled.
- [x] Correct P5-C stored-topology external accounting to intake minus exhaust;
      reconcile accepted P7 heat to the gas ledger without changing burn law;
      retain mass/energy residual terms and tests.
- [x] Add P7 post-event zero-hook, geometry/rebase, preparation-state,
      deterministic replay, restart, species, admissibility, CFL and accounting
      tests without tolerance relaxation.
- [x] Execute the five-anchor campaign and regenerate consolidated JSON, CSV and
      all `anchor-*.json` from that campaign.
- [x] Execute required P8/P7/P6/P5-C/P5-B/P5-A/P3 and focal P4
      coupling/exhaust regressions: 9 passed, 1 deselected for the P8 contract;
      40 passed for P7/P6/P5-C; 92 passed and 7 subtests passed for lower
      regressions.
- [x] Retry OpenSpec strict with a repo-local npm cache; exact command and
      outcome are recorded below.
- [ ] Independent review remains pending; do not claim it without evidence.
- [x] Verify conditional closure with all five anchor gates true and no failures.

## Current evidence

The final campaign status is `P8_WIDE_RPM_PERFORMANCE_VERIFIED_CONDITIONAL`.
All five anchors have heat > 0 and all measured gates are true; `failures=[]`.
The result is conditional on P4 remaining blocked/not granted and does not
claim periodic convergence, steady state, or experimental validation.

The durable evidence records two preparation cycles, zero preparation heat, the
900->180 geometry proof, repeated event cuts, accepted P7 heat, gas/ledger heat
residual, mass and energy ledger terms, exact restart state and CFL. The P5-C
external ledger is intake into the stored topology minus exhaust outflow;
internal interfaces cancel. No residual is hidden or relaxed.

## Validation record

- Campaign: `P8_WIDE_RPM_PERFORMANCE_VERIFIED_CONDITIONAL`; `failures=[]`;
  five anchors have `heat>0` and all gates are true.
- Regression command: `.\\.venv\\Scripts\\python.exe -m pytest -q
  tests/test_p8_performance.py -k "not campaign" tests/test_p7_prescribed.py
  tests/test_p7_full_topology.py tests/test_p6_species.py
  tests/test_p5c_integrated.py tests/test_p5b_integrated_coupling.py
  tests/test_p5b14_complete_fixture.py tests/test_p5_intake_transfer_foundation.py
  tests/test_coupling_adapter.py tests/test_coupling_preflight.py
  tests/test_coupling_riemann.py tests/test_exhaust_port.py tests/test_hybrid_exhaust.py
  tests/test_p4_sci_04a.py tests/test_p4_sci_04b.py tests/test_p4_r1e.py`
  -> P8 contract `9 passed, 1 deselected`; P7/P6/P5-C `40 passed`;
  lower regressions `92 passed, 7 subtests passed`.
- OpenSpec strict: valid with the repo-local writable npm cache.
- `git diff --check`: no errors.
- Independent review: pending.
- P4: `BLOCKED / NOT_GRANTED`; P9: `STOPPED`.

No P4 acceptance, independent review, publication, archive, commit, push or P9
work is claimed.

## Revalidación sobre P4 cerrado — 2026-09-29
- [x] P8 revalidado sobre `P4_PASS` mediante provenance y auditoría focal; cinco anchors y todos los gates vigentes PASS.
- [x] Outputs conservan semántica `BOUNDED_TRANSIENT_INDICATED`; no se declara periodicidad ni validación experimental.
- [ ] Revisión independiente permanece pendiente; P9 sigue detenido.

## Revalidación tras recuperación G2-v2 — 2026-09-29

- [x] P8 conserva los cinco anchors y todos los gates históricos; `p8_performance.py` y runtime asociado sin cambios, 141 pruebas focales PASS y 1 campaña completa excluida por no haber cambiado P8.
- [x] Recibo nuevo `results/p5-p8-revalidation-g2-v2-recovery-20260929/receipt.json`; semántica `BOUNDED_TRANSIENT_INDICATED`, sin validación experimental.
- [ ] Nueva revisión independiente P4–P8 pendiente; P9 no autorizado.
