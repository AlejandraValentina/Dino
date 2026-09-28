# P4 diagnostic audit — 2026-09-28

## Scope and result

This is a read-only scientific diagnosis performed after the independent P8
reproduction in `results/p8-audit-20260928/`. P8 reproduced all five anchors and
its conditional status; that does not change P4 or authorize P9.

The result is **`SCIENTIFIC_CHANGE_REQUIRED`** for P4. P4 remains
**`BLOCKED / NOT_GRANTED`**, and P9 remains **`STOPPED / NOT AUTHORIZED`**.
No production physics, solver, thresholds, or P4 contracts were changed, and no
new P4 simulation was launched.

## Evidence chain

The durable P4 record has three distinct conclusions:

1. The conservation/admissibility/CFL controls and the foundational P4A/P4B,
   B1/B2, C1/C2 and E13-G1 evidence pass. The R10A audit corrected the spatial
   error metric, front tracking, energy-density expression and cycle labels. It
   found mixed localized/distributed nonclosure, not a reproducible single
   detector or accounting defect.
2. R11–R13A support a reproducible period-2 response across backend, CFL and
   mesh checks. This is evidence for a numerical period-2 orbit, not a period-1
   steady state. R12 still found one branch nonclosure, while R13A showed an
   eventual N400 even-branch closure after the earlier failed comparison. That
   history does not satisfy the unchanged E13-R1/P4 gate by itself.
3. C3 remains inconclusive: the return snapshot is present, but the durable
   artifact does not expose the required exact-Riemann comparison or independent
   momentum-face terms. Therefore the return-coupling gate is unproven, not
   passed and not disproven by a localized numerical bug.

The latest R4 performance result is a separate operational blocker: the second
hot G1 measurement is 26.599 s against the <=20 s target. It cannot justify a
scientific change or be reclassified as a P4 physics pass.

## Classification

| Question | Finding |
|---|---|
| Defecto numérico localizado | Not identified |
| Transitorio lento | Insufficient as the sole explanation; long-horizon data show repeatable period-2 structure |
| Órbita periódica | Period-2 supported, but not contractual P4 closure |
| Métrica de cierre defectuosa | Not identified after R10A corrections |
| Evidencia insuficiente | Yes, for C3 exact return/momentum and for the required E13-R1 closure |

The appropriate blocker is therefore scientific-contractual evidence
insufficiency, with a separate performance decision pending. A bugfix or a
threshold relaxation would conceal the unresolved scientific choice.

## Next action

The next scientifically justified action is a separately authorized, focal C3
evidence acquisition that records the exact-Riemann return and an independent
momentum balance, or an explicit human decision on the E13 periodicity contract.
Until then, do not alter physics, rerun broad P4 campaigns, grant P4, start P5,
or authorize P9.
