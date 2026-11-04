# Project-linked parametric study manifests

Project schema V3 adds a small `study_references` list containing manifest path, study ID, manifest SHA-256, schema, and original source project ID. Manifests and run artifacts remain external. Projects V1 and V2 migrate forward without changing engine identity; project duplication retains original provenance.

When a study finishes in Desktop, its manifest is registered only after the bytes, schema, study ID, and active project binding are verified. Results offers a project study selector. Opening a registered study fails closed when the file hash or identity differs, with the manifest bytes verified again at load time. Re-completing a resumed study replaces its old reference instead of leaving a stale hash. Duplicate projects retain source-project provenance.

Verification: `tests/test_desktop_design_study.py` plus `tests/test_engine_configuration_v1.py`: **19 passed**. V1/V2 migrations in `tests/test_dino_desktop.py`: **2 passed**. The first broad run had one test setup assertion failure: it assumed the optional UI manifest attribute existed before opening a study; the application had correctly rejected the modified manifest. The assertion was corrected, and the final focused suite passed. `compileall` passed for all modified modules.

No solver execution or result artifacts were changed by this task. Existing study manifests and run evidence remain external and unchanged.
