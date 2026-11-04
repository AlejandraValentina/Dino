# Parametric design studies in Dino Desktop

## First vertical capability

Use **SIMULAR → Más opciones → Estudio paramétrico geométrico**. Each study
varies one parameter at a time. The baseline value is inserted automatically;
the engineer enters up to four alternative values. Supported axes are existing
partitioned escape-section lengths, transfer-port top/height/width/discharge
coefficient, intake-port discharge coefficient, and explicit crankcase volume
at BDC. Units are shown with the selected parameter.
All points use the same selected project/variant, RPM, cycle horizon and the
existing `DINO_ENGINEERING_RUN_V1` Desktop execution/import path
(`ENGINEERING_EXPLORATORY`). The topology, existing cells, and physical
equations are unchanged. Transfer-port changes are rebuilt by the existing
`TwoStrokePortSet`; its transfer-opening and effective-width summaries are
regenerated from that same port set. The intake adapter changes only its
declared discharge coefficient and refreshes its effective-area summary.
Crankcase-volume changes use `CrankcaseGeometry` and `SliderCrankChambers2T`,
refresh the BDC-volume/compression-ratio metadata, and rescale the initial
species inventory to preserve the existing density and species fractions.
The study fails closed when the engineering output adapter's explicit
`geometry_identity.displacement_cc` input is absent; it does not infer that
value from bore and stroke.

The preflight validates every generated engine configuration with Dino's
existing configuration/geometry validators and executes zero solver steps. The
dialog shows the exact design values, RPM, cycle horizon, aggregate budget and
artifact root before explicit confirmation. Each point receives a distinct
configuration identity, run ID, artifacts and checkpoint. The existing Desktop
importer verifies result and diagnostic artifact hashes and exposes internal
conservation; it does not perform an independent audit.

Studies are stored under `design-studies-v1/<project>/<study-id>/`. The
`prepared.json` file retains the exact baseline and each generated engine
configuration; `study.json` records point status, identities, run references,
periodicity classifications, elapsed budgets, and interruption reason. The
project's base engine is not mutated. Completed points can be reused on resume
only after the existing Desktop importer verifies their result artifacts.
Interrupted points resume through the existing run/checkpoint binding.

After a study finishes or is interrupted, Dino opens its available runs in
RESULTADOS. The **Comparar** view lists the varied value, run status, periodicity,
completed cycles, and only those power/torque/BMEP metrics whose source marks
them `DEFINED`. It reports a delta only when both a baseline and a candidate
have defined power. Transient estimates remain absent from that definitive
delta; nonconverged and incomplete points remain visible with their own state.

## Scientific and computational boundaries

- Every point is EXPLORATORY and `scientific_validation=NOT_CLAIMED`.
- Periodicity remains the existing per-run detector result; a completed point
  is not synonymous with a periodic point or a validated prediction.
- No interpolation or derived power is introduced by the study layer.
- The current UI caps an initial invocation at five designs, 600 seconds
  aggregate, 600 seconds per design, and 4096 MiB RSS per process. An explicit
  resume can add at most 600 seconds per invocation, up to a cumulative 1200
  seconds. Cancellation leaves the study manifest and run checkpoints for
  explicit resumption.
- Exhaust port-window fields are not exposed because the saved exhaust summary
  binds multiple power-valve positions. Cylinder bore/stroke/rod length,
  cylinder compression ratio, intake-port dimensions, and multi-factor designs
  remain unavailable until their metadata and solver bindings can be regenerated
  without stale summaries.
- Existing global result history is not searched as a design cache. Reuse is
  limited to fully verified points already bound to the same study.

The study manifest is an analysis/execution record. It is not an experimental
validation record and does not alter the project's scientific validation state.
