# Requirements

## ADDED Requirements

### Requirement: Preserve historical scientific contracts

The program MUST preserve historical P4–P8 records and the frozen P9 contract
byte-for-byte unless a later explicit scientific authorization creates a new
contract. New capabilities MUST use separate schemas and MUST NOT claim
experimental or predictive validation from synthetic cases.

#### Scenario: New capability uses a separate contract

- **WHEN** a new 2T component or metric is added
- **THEN** its behavior and evidence are versioned independently, with source
  provenance and no retroactive changes to P4–P9 results.

### Requirement: Traceable configurable two-stroke engine

The product MUST progressively support a configurable single-cylinder 2T engine
with gas exchange, four-species transport, scavenging, combustion, heat transfer,
crankcase dynamics, mechanical losses, fuel accounting, performance outputs,
checkpoint/restart/replay, and auditable primary evidence. Each material
parameter MUST identify its provenance. The program MUST NOT declare
`MOTORSIM_2T_COMMERCIAL_CORE_READY` until all required subsystems are integrated
and verified together.

#### Scenario: Incomplete capability cannot pass the product gate

- **WHEN** a subsystem has only unit or isolated fixture coverage
- **THEN** its phase may be recorded complete at its own scope but the overall
  commercial-core readiness remains not ready.

### Requirement: Evidence and conservation for stateful components

New components that exchange mass, energy, or species MUST participate in
appropriate local and global ledgers, preserve admissibility, and provide
auditable evidence. Stateful capabilities MUST test serialization, restart, and
deterministic replay where applicable. Auditors MUST recompute claims from
primary evidence rather than trust stored PASS summaries.

#### Scenario: Invalid evidence is rejected

- **WHEN** evidence has missing fields, invalid numerics, identity mismatch, or
  inconsistent primary-to-summary values
- **THEN** audit returns a failure/invalid state without promoting a stored PASS.

### Requirement: Independent phases continue around local blockers

The program MUST classify blocked phases precisely and continue any later phase
whose inputs and acceptance do not depend on the blocker. A phase MUST stop only
for a real scientific decision or one of the global hard stops in the user
authorization.

#### Scenario: KT100 boundary blocker does not block an independent fixture

- **WHEN** a reference operating point fails at an existing boundary
- **THEN** the receipt remains unchanged while independent analytic fixtures and
  component work may proceed without changing that boundary or its contract.

### Requirement: Generic two-stroke port geometry

The engine configuration MUST represent any positive number of individually
identified transfer windows (including primary, secondary, and boost roles),
multiple exhaust apertures (including auxiliary or bridged segments), a piston
port intake, explicit duct association, and nonnegative finite discharge
coefficients. Rectangular piston-controlled area MUST reuse the existing
kinematics and use `Cd*w*max(0,min(h,x(theta)-top))`; piston-port intake MUST
reuse its documented skirt-window geometry and MUST remain bidirectional at the
flow interface. Powervalve-ready roof travel MUST be geometry metadata and MUST
not create an actuator model in this phase. Arbitrary effective-area profiles
MUST use explicit periodic angle-area knots and deterministic piecewise-linear
interpolation. Configurations MUST persist primary geometry and derived
effective-area profiles bound to the exact primary configuration. Existing
project JSON versions and historical port interpretation MUST remain readable
unchanged.

#### Scenario: Multiple transfer and exhaust apertures

- **WHEN** a configuration has two or more transfer apertures and multiple
  exhaust apertures associated with named ducts
- **THEN** each aperture retains its own role, timing, geometry, coefficient,
  and duct association, and the compiled profile reports each duct's summed
  effective area by crank angle.

#### Scenario: Profile is periodic and bound to geometry

- **WHEN** an explicit area profile is loaded or geometry is edited
- **THEN** profile knots cover 0–360°, endpoint area agrees exactly, derived
  samples are recomputed, and stale or modified derived-profile evidence is
  rejected.

#### Scenario: Reverse flow through piston-port intake

- **WHEN** the connected flow reverses through an open piston-port window
- **THEN** the geometry continues to expose its open area; donor selection stays
  with the existing conservative flow interface and is not suppressed by a
  one-way intake flag.

### Requirement: Auditable two-stroke scavenging metrics

The engine MUST derive cycle scavenging metrics from four-species inventories,
fresh-delivery ledger, and direction-aware fresh short-circuit ledger without
altering P6 transport. Let `F=fresh_air+fuel`, `R=residual`, `M=sum(four
species)`, `Fdel=fresh delivered through transfers`, `Flost=fresh short circuit
through outward exhaust`, and `Mref=rho_ambient*Vdisplacement`. The outputs MUST
include: delivery ratio `Fdel/Mref`; trapping efficiency `Fret/Fdel`; scavenging
efficiency `Fret/Mexhaust_close`; charging efficiency `Fret/Mref`; trapping
ratio `Fdel/Fret`; fresh retained `Fret`; fresh lost `Flost`; residual fraction
`Rexhaust_close/Mexhaust_close`; purity at transfer close `Ftransfer_close/
Mtransfer_close`; purity at exhaust close `Fexhaust_close/Mexhaust_close`; and
short-circuit fraction `Flost/Fdel`. `Fret` is `Fexhaust_close`. Reference
displacement volume is `pi*bore^2*stroke/4` with SI conversion. Each zero
denominator MUST produce an explicit undefined result and reason; invalid or
nonfinite inputs MUST be rejected, never clipped to a plausible efficiency.
These are model diagnostics, not experimental claims.

#### Scenario: Analytical species ledger

- **WHEN** reference mass is 0.01 kg, fresh delivery is 0.012 kg, short circuit
  is 0.002 kg, transfer-close species are `[0.003,0.001,0.006,0]` kg, and
  exhaust-close species are `[0.004,0.001,0.004,0.001]` kg
- **THEN** delivery ratio is 1.2, trapping efficiency is 5/12, scavenging and
  charging efficiency are 0.5, trapping ratio is 2.4, residual fraction 0.4,
  transfer purity 0.4, exhaust purity 0.5, and short-circuit fraction 1/6.

#### Scenario: Zero denominator and reverse exhaust

- **WHEN** a ratio denominator is zero or an exhaust exchange is inward
- **THEN** the ratio is explicitly undefined when appropriate, and inward
  exhaust species do not increment fresh-short-circuit mass.
