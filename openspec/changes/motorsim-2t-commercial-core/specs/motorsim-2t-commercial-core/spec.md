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

### Requirement: Configurable multi-petal reed intake

The engine MUST expose separate `STATIC_REED_V1` and `DYNAMIC_REED_V1` modes.
Every petal MUST identify its mass, effective pressure area, effective flow
width, spring stiffness, damping, lift stop, discharge coefficient, restitution,
and parameter provenance. Static mode MUST compute bounded equilibrium lift
from signed pressure differential and MUST block reverse flow. Dynamic mode MUST
advance petal position and velocity using the damped lumped-mass/spring equation
under the supplied pressure differential, enforce closed/open lift stops with
the configured restitution, and expose bidirectional transient flow through
the current open area; reverse pressure MUST drive closure but MUST NOT erase
area before the petal physically closes. Multiple petals MUST have independent
state and contribute summed area. Flow MUST reuse the existing gas-flow function
and MUST NOT alter global ledgers itself.

#### Scenario: Static reed opening and reverse protection

- **WHEN** forward differential is positive
- **THEN** static lift is the spring equilibrium clipped to `[0,lift_stop]` and
  effective area is coefficient × width × lift; reverse differential returns
  zero area/flow.

#### Scenario: Dynamic petal response

- **WHEN** the differential changes while a petal has nonzero velocity
- **THEN** the petal state advances deterministically from its previous
  position/velocity, respects the stops, and permits transient reverse flow only
  while its area remains open.

#### Scenario: Multi-petal and invalid configuration

- **WHEN** a reed bank contains multiple valid petals or any mass/stiffness/
  damping/area/provenance value is invalid
- **THEN** valid petal areas/states remain individually inspectable and malformed
  or nonfinite inputs are rejected without silently clipping parameters.

### Requirement: Expansion chamber reuses the quasi-1D solver

The engine MUST represent an expansion system as connected, provenance-bearing
conical sections for header, diffuser, belly, baffle cone, stinger, silencer,
tailpipe, or generic cones. Geometry MUST reuse the existing quasi-1D mesh and
MUST NOT add a parallel gas solver. The result adapter MUST derive pressure,
temperature, Mach, mass flow and characteristic speeds from actual solver
primitive states. A travelling-wave decomposition MUST identify its linear
small-perturbation base state and MUST NOT be represented as a nonlinear wave
solution. Reflection timing MUST be reported as a characteristic travel-time
estimate; amplitudes remain outputs of the gasdynamic solver.

#### Scenario: Build a continuous expansion assembly

- **WHEN** adjacent sections have matching endpoint diameters
- **THEN** they form a mesh using the existing frustum geometry; disconnected,
  nonfinite, or nonpositive sections are rejected.

#### Scenario: Map an actual 1D solution

- **WHEN** admissible primitive cells from the quasi-1D solver are provided
- **THEN** the adapter reports pressure, temperature, signed Mach, mass flow,
  and left/right characteristic speeds for every cell.

#### Scenario: Report travel-time limits

- **WHEN** a characteristic cannot travel toward a requested station because
  the base flow is supersonic in that direction
- **THEN** its travel-time estimate is explicitly unavailable and no reflected
  wave amplitude is fabricated.

### Requirement: Configurable prescribed-wall thermal ledger

Thermal configuration MUST represent cylinder wall, head, piston crown,
crankcase, transfer walls and exhaust walls as separately addressable surfaces.
Each configured surface MUST carry explicit area, heat-transfer coefficient,
provenance and either a fixed positive wall temperature or a bounded RPM/load
temperature map. `CONSTANT_H_V1` MUST calculate signed gas-to-wall heat as
`h*A*(Tgas-Twall)`. The cycle ledger MUST integrate complete, strictly ordered
crank-angle samples with the declared RPM and return signed energy per surface
and total. Map extrapolation, incomplete cycles, missing surfaces, and malformed
or nonfinite values MUST be rejected. The model MUST not silently select/fill
coefficients or alter the gas solver.

#### Scenario: Analytical fixed-wall cycle

- **WHEN** a fixed gas-wall temperature difference and explicit area, `h`, RPM,
  and complete cycle samples are supplied
- **THEN** the per-surface ledger equals the trapezoidal integral of
  `h*A*(Tgas-Twall)` over crank-angle time.

#### Scenario: Mapped prescribed wall temperature

- **WHEN** an RPM/load point lies inside an explicit map
- **THEN** bilinear interpolation supplies its temperature, while an out-of-map
  point is rejected rather than extrapolated.

### Requirement: Prescribed combustion progress V2

`COMBUSTION_MODEL_V2` MUST support one or two weighted Wiebe components with
explicit ignition timing, duration, shape parameters, component delay and
provenance. The model MUST expose normalized progress, derivative per crank
degree, configured combustion efficiency and CA10/CA50/CA90. Efficiency MUST
be an explicit scalar or bounded RPM/load map. The progress capability MUST
remain separate from P7 historical code. It MUST NOT infer fuel chemistry,
species conversion, stoichiometry, LHV or heat release.

#### Scenario: Single or double prescribed burn

- **WHEN** one or two valid Wiebe components and a supported operating point
  are evaluated
- **THEN** weighted progress is monotonic and bounded by configured efficiency,
  the three CA points are ordered, and the final progress equals efficiency.

#### Scenario: Zero efficiency and invalid operating point

- **WHEN** efficiency is zero or RPM/load lies outside its configured map
- **THEN** the burned fraction remains zero with undefined CA points, or the
  out-of-map request is rejected; no heat or chemistry output is fabricated.

### Requirement: Explicit two-stroke mechanical losses and brake metrics

Mechanical losses MUST be explicit nonnegative MEP terms with source class and
provenance; each term MUST use either a fixed value or bounded RPM/load map.
For the declared 2T 360-degree cycle, the model MUST derive indicated/brake
MEP, work, power and torque from the stated displacement, RPM and indicated
work. It MUST preserve negative brake output without clipping and MUST NOT fit
loss terms to desired performance.

#### Scenario: Convert indicated cycle work to brake output

- **WHEN** indicated work, total 2T displacement, RPM and explicit mechanical
  loss terms are supplied
- **THEN** loss work is `FMEP*Vd`, brake work is indicated work minus loss work,
  and power/torque follow the declared 360-degree cycle convention.

#### Scenario: Loss exceeds indicated work

- **WHEN** configured losses exceed indicated cycle work
- **THEN** negative brake work/power/torque remain visible and are flagged, not
  clipped to zero.

### Requirement: Explicit fuel, AFR and 2T SFC accounting

Fuel accounting MUST use explicit stoichiometric AFR, LHV and provenance. The
cycle input MUST distinguish delivered and trapped fresh-air/fuel masses,
explicit P6 species-ledger short circuit, and a bounded prescribed burned
fraction. Outputs MUST include delivered
and trapped AFR, equivalence ratio, fuel trapped/burned/unburned/short-circuited,
fuel flow, released-energy potential, indicated SFC and brake SFC when brake
power is positive. Fuel flow MUST use the declared 2T 360-degree cycle rate.
Zero denominators and nonpositive brake power MUST have explicit undefined
statuses. The energy potential MUST NOT be passed to the gas solver without a
separately verified energy coupling.

#### Scenario: Complete fuel ledger

- **WHEN** explicit fuel properties, P6 delivered/trapped and short-circuited
  species masses, burned fraction, RPM and indicated/brake work are supplied
- **THEN** AFR, equivalence, species-derived fuel masses, flow, energy potential
  and SFC are returned with the 2T cycle convention.

#### Scenario: Missing fuel or nonpositive brake power

- **WHEN** no fuel is present or brake power is zero/negative
- **THEN** AFR or brake SFC is explicitly undefined; masses and energy remain
  zero or signed according to the supplied ledger, without invented values.

### Requirement: RPM-mapped exhaust powervalve geometry

Powervalve V1 MUST map RPM continuously to an explicit `[0,1]` exhaust roof
position with provenance. Position zero MUST mean raised/open and position one
MUST lower the roof by the configured travel distance. The model MUST target
only its declared movable main exhaust window and MUST reuse generic port area
and event calculations. RPM outside the configured map MUST be rejected. No
actuator dynamics or unprovided RPM calibration may be inferred.

#### Scenario: Interpolate roof position

- **WHEN** an RPM lies between configured map points
- **THEN** linear interpolation changes the main exhaust port's area profile and
  event angles through the existing port geometry.

#### Scenario: Invalid target or map range

- **WHEN** the target port is not the configured movable main exhaust or RPM
  lies outside the map
- **THEN** the request is rejected without changing other ports.

### Requirement: Slider-crank crankcase V2 geometry and donor-aware links

Crankcase V2 MUST accept explicit bore, stroke, rod length, BDC volume and
provenance. It MUST use the established slider-crank position to calculate
volume throughout 360 degrees, analytic volume rate at RPM, and the ratio of
maximum to minimum crankcase volume. A standalone 0D intake/leak link MUST reuse
the existing bidirectional restriction relation and its actual donor state;
it MUST NOT clamp reverse flow. The helper MUST NOT claim production P5-C/P6
integration or modify their stage ledger.

#### Scenario: Crankcase volume and compression

- **WHEN** valid slider-crank dimensions and BDC volume are supplied
- **THEN** TDC/BDC volumes, crankcase compression ratio and volume-rate sign
  follow the existing kinematics and preserve its endpoint behavior.

#### Scenario: Reversible intake/leak flow

- **WHEN** pressure ordering changes across a configured link
- **THEN** the existing restriction resolves the direction, enthalpy and fresh
  fraction from the actual upstream donor; closed area gives exact zero flux.
