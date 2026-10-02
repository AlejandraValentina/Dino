# Deferred scientific work: `GENERALIZED_RESERVOIR_BOUNDARY_V2`

Status: deferred capability work; this note does not amend P5 or authorize a
boundary change.

The KT100 hybrid fixture r5 stopped before its first complete cycle at each
fixed RPM with `No consistent reservoir inflow branch`. The existing
`Boundary('reservoir')` rejected the requested incoming characteristic branch
for the accepted state. The five receipts and their configuration/source
bindings remain frozen in
`results/kt100-hybrid-model-fixture-v2-harness-20261002-r5/`.

This is a local capability blocker for that reservoir/operating-state pairing,
not a blocker for independent component development. It does not establish
that the reservoir equations are generally defective, nor does it establish a
physical failure of the KT100.

Potential future designs to evaluate under a separate scientific contract:

- A sign-aware characteristic boundary that prescribes only incoming
  characteristics for subsonic flow and extrapolates outgoing information.
- Explicit static or stagnation thermodynamic state and donor composition for
  inflow, with a separately specified supersonic inflow contract.
- A pressure outlet/inlet characteristic treatment with documented switching
  rules across flow reversal and strict admissibility handling.

Each option changes boundary semantics and may change mass, energy, species,
and reflection behavior. It therefore requires a declared scientific model,
independent analytical fixtures for subsonic/supersonic inflow/outflow and
reversal, conservation and admissibility tests, and explicit authorization
before implementation. No option is selected here. Do not retry KT100 V2,
change its initial state, pressure, geometry, CFL, mesh, or horizon as a way to
avoid this decision. Do not alter historical P5 or reinterpret its receipts.
