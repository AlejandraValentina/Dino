# Roadmap executor checkpoint

Starting commit: `854e59e`.

P5-A is verified conditionally. P5-B remains the active phase and is blocked at its conservative integration gate: duct-cell evolution, `-p dV/dt`, and auditable mass/energy/species ledgers are incomplete. The executor therefore stops at P5-B and does not enter P5-C, P6, P7, P8 or P9.

P4 remains `BLOCKED` / `NOT_GRANTED`; all integrated evidence remains conditional on P4. The state machine is persisted in `results/roadmap-executor/state.json` and can resume after the missing P5-B work is implemented.

Focal tests: 13 passed (P5-A and P5-B). OpenSpec P5 and P4 strict validation passed. No simulations beyond the short fixtures, no push, and no experimental validation were performed.

Roadmap executor attempt 2 fixed a localized fixture timestep/volume defect (negative pressure from an undersized synthetic cell). The focused P5-B tests now pass. The phase remains blocked because `-p dV/dt`, full gas1d interior evolution and auditable global ledgers are still absent; no automatic advance occurred.
# P5-B implementation checkpoint

La implementación contractual continúa en estado `PENDING_IMPLEMENTATION`, no BLOCKED. Se añadieron estados conservativos de celdas 1D, aplicación de flux único a cámaras y ductos, y ledger básico de frontera/trabajo. Aún faltan cerrar la integración con el RHS interior gas1d, la cuadratura SSPRK2 y los balances auditables antes de evaluar el gate.
