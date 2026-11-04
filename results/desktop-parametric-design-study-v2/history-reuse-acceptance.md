# Parametric historical reuse — acceptance evidence

## Implementation

Historical cache lookup now searches completed engineering runs under the configured artifact root. A candidate must match the exact resolved engine/RPM identity, RPM, requested cycle limit, memory limit, and current implementation source hashes. The run manifest's SHA-256 is checked against the actual `result.json` bytes, then Dino imports the candidate through its existing engineering result importer, which verifies the associated diagnostic manifest and sample evidence. Unsupported or altered candidates are rejected. There is no interpolation or modification of source records.

Reused study points are marked `CACHED`, retain the source run/project identifiers and original path, and are joined into the study results by the original run ID. Desktop labels cached rows as historical and verified. The result's scientific classification and periodicity are shown unchanged; cached execution does not imply convergence or predictive validity.

The technical HTML report now accepts the associated `DINO_PARAMETRIC_DESIGN_STUDY_V1` manifest, displays parameter values, point status, engine identities and the current manifest file hash, and includes the full attached manifest JSON. Invalid manifest schemas fail closed. It does not recompute solver data or alter exact result rows.

## Verification

- Focused study, Desktop, report, crankcase and port suites: **38 passed** in 71.54 s.
- Technical report suite after the Desktop export assertion: **6 passed** in 1.13 s.
- Historical reuse boundary, live runner integration, same-study resume and cached row presentation: **4 passed** in 15.96 s.
- `compileall` passed for the changed implementation modules.
- A real artifact-root integration opened two existing synthetic, one-cycle runs through Dino's real importer. The verified second study completed as `CACHED` in 0.094 s. Its execution replaced the solver runner with an assertion that would fail if called. Both points remained `MAX_CYCLES_NONCONVERGED` / `INSUFFICIENT_CYCLES`; metrics remain undefined. Manifest and source result SHA-256 values are recorded in `history-reuse-receipt.json`.

## Preserved failed probe

The first real reuse probe failed to match because the engineering contract stores the canonical result digest in `run.json`; it is not a field inside `result.json`. The probe therefore ran two synthetic points for one cycle each before the defect was identified. Both outputs are preserved in the external artifact root, nonconverged, with no performance metrics or validation claim. No cleanup was performed. The corrected test uses the actual result/manifest hash contract and exact historical identity. A later smoke test confirmed reuse without solver entry.

## Limits

Historical search includes the configured artifact root's `exploratory-workflow-v1` store and project-registered result references, including references outside that root. Arbitrary external paths not registered by the project are not searched. Multi-factor studies and a parameter-response visualization remain unavailable. The Desktop integration is source-level; no Windows package was rebuilt. This evidence is functional and synthetic only, not experimental validation.
