# Tasks

- [x] Implement isolated geometry, port laws and network data model.
- [x] Compose existing mesh and coupling primitives.
- [x] Add focused geometry/closed-port/topology/state tests.
- [ ] Add full wave, conservation and backflow fixture campaign in the next P5 increment.
- [ ] Human acceptance remains conditional on P4.
- [x] P5-B coordinator skeleton and stage/port traces implemented.
- [ ] Conservative chamber/duct updates, p·dV ledger and integrated global conservation remain before P5-B verification.
- [x] P5-B-R1: aplicación conservativa de fluxes a inventarios de cámaras y validación por stage.
- [x] P5-B-R1: término contractual de trabajo `-p·dV/dt` validado con expansión, compresión y rechazo de entradas no finitas.
- [x] P5B-06: auditoría de fuente única de flux por interfaz; cada interfaz se resuelve una vez desde su propio ducto y se reutiliza para trazas y actualizaciones.
- [x] P5B-07: ledger global de masa; el residuo `ΔM - M_ext` se comprueba con entradas externas, transferencias internas y puertos cerrados.
- [x] P5B-08: ledger global de especie pasiva; el residuo `ΔS - S_ext` se comprueba con entradas externas, transferencias internas y puertos cerrados.
- [x] P5B-09: ledger global de energía; `ΔE = E_ext + W_cc + W_cyl`, con flujo externo y cada trabajo `-p·dV/dt` auditables por separado y sin doble conteo de interfaces internas.
- [x] P5B-10: fixture de volumen cerrado; puertos cerrados, inventarios constantes, trabajo contractual de compresión/expansión y admisibilidad auditados ([evidencia](../../../results/p5b-10-closed-volume-work-20260924/evidence.json)).
- [x] P5B-11: fixture finito single 0D↔1D con pared rígida Euler contractual, validación dimensional de cámara mediante `ChamberState`, conservación global y admisibilidad verificadas; 27 P5B y 40 pruebas relevantes PASS ([evidencia](../../../results/p5b-11-single-0d1d-fixture-20260924/evidence.json)).
- [ ] Integrar inventarios/celdas de ductos, término -p dV/dt y ledgers globales antes del cierre P5-B.
- [x] P5B-12: one-transfer closed subsystem implemented; two interfaces are solved once per SSPRK2 stage, opposite-sign duct/chamber updates, global mass/species conservation, applied energy/work gate, exact closed-port zero flux, interior evolution and admissibility verified ([evidence](../../../results/p5b-12-one-transfer-fixture-20260924/evidence.json)). Final stored-state energy roundoff is reported and bounded separately from the strict stage-quadrature gate.
- [ ] P5B-13: two-transfer fixture is the next durable active task.
