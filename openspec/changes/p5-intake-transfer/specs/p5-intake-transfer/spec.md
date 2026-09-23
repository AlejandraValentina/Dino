## ADDED Requirements

### Requirement: isolated duct geometry
The foundation SHALL represent ordered intake and transfer geometries with exact frustum volumes and shared mesh faces.

#### Scenario: build mesh
- **WHEN** a valid segment list and target spacing are supplied
- **THEN** the shared mesh contains positive volumes and shared faces

### Requirement: bidirectional interfaces
The foundation SHALL expose forward flow, zero crossing and backflow through existing Riemann coupling without direction clamps.

#### Scenario: closed port
- **WHEN** interface area is zero
- **THEN** mass, energy and species fluxes are exactly zero

### Requirement: governance
Integrated periodic engine evidence SHALL remain CONDITIONAL_ON_P4.

#### Scenario: isolated verification
- **WHEN** P5-A fixtures run without the integrated engine
- **THEN** their result is independent of P4 and no P4 PASS is inferred

## ADDED Requirements

### Requirement: integrated conditional topology
P5-B SHALL compose atmosphere, intake, crankcase, two transfer ducts and cylinder without connecting exhaust.

#### Scenario: isolated integrated fixture
- **WHEN** the short fixture is executed
- **THEN** interface traces and stage timing are recorded without inferring P4 acceptance
