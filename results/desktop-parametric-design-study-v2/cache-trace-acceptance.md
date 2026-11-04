# Parametric cache traceability — acceptance

Each comparison design row now exposes its source run ID, source project ID, result-directory path, engine identity SHA-256, result artifact SHA-256, canonical result SHA-256, and whether the exact run was reused after verification. The technical HTML study section carries the same fields as columns and retains the full original manifest JSON appendix. Missing metadata is shown as unavailable; Dino does not infer paths or digests.

Verification: the expanded regression set passed **58 tests** in 141.82 s. UI tests assert the cached row tooltip shows the source run, external path, original hashes and verified-reuse status. Report tests assert those source fields and hashes appear in the generated HTML while the exact source manifest remains attached. `compileall` passed.

Cached entries are presentation links to immutable original result artifacts. This feature does not edit source records, relabel scientific classifications or make a validation claim.
