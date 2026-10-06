# Closure task queue

- [x] C1 network endpoint pressure traction and reaction/equilibrium tests.
- [x] C2 integrate OPEN_END_PLENUM_V2 into IntegratedEngine2T config and restore;
      run only a short diagnostic before campaign preparation. (Integrated
      equilibrium/short-step checks pass; no campaign evidence claimed.)
- [x] C3 support any positive number of transfer routes in the integrated core.
- [x] C4 implement a distinct, fuel/oxygen-limited chemical combustion capability;
      leave P7 unchanged. `FUEL_COUPLED_COMBUSTION_V1` uses the frozen synthetic
      surrogate, ignition-snapshot oxygen/fuel availability, stage-local SSPRK2
      limitation, four-species conversion, and LHV/efficiency heat identity.
      Integrated P7 and the historical P7 event remain mutually exclusive and
      unchanged; focused legacy P7 regressions pass.
- [x] C5 derive trapped/delivered/burned fuel metrics from accepted snapshots.
      The cycle primary keeps intake delivery and exhaust short-circuit totals,
      exact port-close species states, ignition-time trapped fuel, chemically
      burned fuel, and terminal unburned inventory as distinct quantities.
- [x] C6 enforce physical domains and explicit perfect-mixing scavenging semantics.
      Additive metrics V2 preserves historical V1 and marks bounded gross-ledger
      ratios outside [0,1] UNDEFINED without clipping; it declares and propagates
      SINGLE_ZONE_PERFECT_MIXING_SCAVENGING_ASSUMPTION.
- [x] C7 use cylinder, crankcase and net piston gas work consistently.
      Primary/output report W_cyl, W_crankcase and W_net = W_cyl + W_crankcase;
      the new mechanical-loss API consumes W_net exactly once. IMEP/loss
      displacement is bound to configured slider-crank swept volume.
- [x] C8 version and validate status/provenance/periodicity-aware outputs.
      New fuel-coupled output schema V5 requires provenance, metric definition
      version and periodicity dependency; it rejects unknown-provenance defined
      values, physical-domain violations and performance without bound periodic
      detector/config/terminal evidence. Historical output schemas remain intact.
- [x] C9 cover equilibrium and pressure reactions for port, endpoint, junction,
      and atmospheric interfaces. Static port opening fractions, both finite
      network endpoints/orientations and OPEN_END_PLENUM_V2 open ends preserve
      uniform rest; pressure reaction identities are checked at each boundary.
- [x] C10 primary-evidence V3 audit rebuilds configuration-bound RHS/fluxes,
       independently replays every accepted SSPRK2 step, enforces float64
       gamma-n ledger residual bounds, and binds cycle retry records, accepted
       trajectory, terminal/checkpoint state, solver dependencies, campaign
       runner, and detector sources. The auditor reexecutes each rejection,
       verifies its failure reason and half-step chain, and the evaluator
       cross-checks the complete retry stream against the manifest. A final
       completeness check also verifies each accepted step against the shared
       nominal event/CFL scheduler, so a rejected attempt cannot be removed
       while preserving internally consistent hashes and counters. The
       independent adversarial follow-up confirmed the identified gaps are
       closed. The affected integrated/evidence suite passes 75 tests and
       strict OpenSpec validation passes. This closes the C10 foundation, not
       an A'/B' campaign.
- [ ] C11 exact continuous/checkpoint/restart/replay comparisons for both primes.
- [ ] C12 preregister and complete transfer/exhaust integrated mesh study.
- [ ] C13 commit immutable A'/B' campaign preregistration before any campaign.
- [ ] C14 run frozen A' 20-cycle campaign and offline audit.
- [ ] C15 run frozen B' 20-cycle campaign and offline audit.
- [ ] C16 exercise at least two distinct RPMs across the primes or preregistered
       sanity fixture.
- [ ] C17 run focused integration tests, full relevant P4–P8 regressions,
       OpenSpec strict, git diff check, git lfs fsck, and verify P9 hash.
- [ ] C18 keep this v1 definition of done versioned in OpenSpec; classify every
       newly discovered item BLOCKS_2T_V1 or POST_2T_V1_BACKLOG.

## Additive capability authorized after the original C1-C18 registration

- [ ] Implement FUEL_COUPLED_COMBUSTION_V2 as an additive Fuel Library snapshot
      consumer. ANCAP profiles remain incomplete and combustion-ineligible;
      the pure C8H18 profile is explicitly MODELED_SURROGATE, not ANCAP fuel.
      The SSPRK stages conserve accepted species and calculate heat only from
      bounded burned fuel, frozen LHV, and explicitly synthetic efficiency.
      Full primary reconstruction, AFR/equivalence-ratio output, and
      configuration/restart roundtrip tests pass. V1 and P7 remain unchanged.
      Record its commit in the durable queue before marking this task complete.

The original C1-C18 v1 acceptance campaigns and mesh gates remain open. Other
features outside this additive capability remain deferred: detailed
carburetion/injection, advanced scavenging, advanced thermal/friction,
multi-cylinder, rotary, turbo/supercharger, GUI, KT100 calibration/recovery and
full RPM sweeps.
