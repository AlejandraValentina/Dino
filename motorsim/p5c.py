"""Bounded P5-C intake/transfer/exhaust integration.

This module is deliberately small: it composes the verified P5-B finite
topology with the existing P4 port flux and gas1d Riemann primitives.  It is a
conditional verification fixture, not a periodic engine solver.
"""
from copy import deepcopy
from math import fsum, isfinite

from .p5b import IntegratedIntakeTransfer, Chamber, DuctCell, _FinitePath
from .coupling import ChamberState
from .exhaust_port import port_flux
from .gas1d.eos import IdealGas
from .gas1d.mesh import uniform_mesh
from .gas1d.riemann import hllc_flux
from .gas1d.boundary import Boundary


class IntegratedP5C:
    """Short-horizon coupled fixture with one finite exhaust path.

    ``step`` advances the already assembled P5-B state and then applies the
    same resolved cylinder/exhaust face flux to both connected components.
    The trace and ledgers make the conditional boundary explicit.
    """
    dependency_status = "CONDITIONAL_ON_P4"

    def __init__(self, crankcase, cylinder, duct_states, exhaust_states=None,
                 *, eos=None, meshes=None, exhaust_mesh=None,
                 exhaust_area=1.0e-4, port_area=0.0, volume_rates=(0.0, 0.0)):
        self.eos = eos or IdealGas()
        self.core = IntegratedIntakeTransfer(crankcase, cylinder, duct_states,
                                             eos=self.eos, meshes=meshes,
                                             volume_rates=volume_rates,
                                             external_boundary=False)
        if exhaust_states is None:
            exhaust_states = ((1.0, 0.0, 100000.0, 0.0),) * 3
        self.exhaust_mesh = exhaust_mesh or uniform_mesh(len(exhaust_states),
                                                          length=0.03,
                                                          area=exhaust_area)
        self.exhaust = _FinitePath(exhaust_states, self.exhaust_mesh, self.eos)
        self.exhaust_area = float(exhaust_area)
        self.port_area = float(port_area)
        self.angle = 0.0
        self.ledger = {"external_mass": 0.0, "external_energy": 0.0,
                       "external_species": 0.0, "port_mass": 0.0,
                       "port_energy": 0.0, "port_species": 0.0}
        self.history = []
        self._initial = self.totals()

    def _duct_totals(self, path):
        return {"mass": fsum(q[0] * v for q, v in
                              zip(path.conservative(), path.mesh.volumes)),
                "energy": fsum(q[2] * v for q, v in
                                zip(path.conservative(), path.mesh.volumes)),
                "species": fsum(q[3] * v for q, v in
                                 zip(path.conservative(), path.mesh.volumes))}

    def totals(self):
        total = self.core._totals()
        ex = self._duct_totals(self.exhaust)
        return {k: total[k] + ex[k] for k in total}

    def admissible(self):
        self.core.admissible()
        for q in self.exhaust.conservative():
            self.eos.primitive(q)
        return True

    def _exhaust_step(self, dt):
        cyl_inv = self.core.cylinder.inventory(self.eos)
        chamber = ChamberState(cyl_inv[0], cyl_inv[2], cyl_inv[1],
                               self.core.cylinder.volume)
        first = self.eos.primitive(self.exhaust.cells[0].conservative)
        face = port_flux(chamber, first, self.port_area, self.exhaust_area,
                         eos=self.eos)
        flux = face["flux"]
        # Positive flux leaves the cylinder and enters the duct.
        self.core.cylinder.apply_rhs((-flux[0], -flux[2], -flux[3]), dt,
                                     self.eos)
        self.exhaust.cells[0].apply_flux(flux, dt, self.eos, sign=1.0)
        for i in range(len(self.exhaust.cells) - 1):
            a = self.eos.primitive(self.exhaust.cells[i].conservative)
            b = self.eos.primitive(self.exhaust.cells[i + 1].conservative)
            f, _, _ = hllc_flux(a, b, self.eos)
            extensive = tuple(self.exhaust_mesh.areas[i + 1] * x for x in f)
            self.exhaust.cells[i].apply_flux(extensive, dt, self.eos, sign=-1.0)
            self.exhaust.cells[i + 1].apply_flux(extensive, dt, self.eos, sign=1.0)
        outlet = self.eos.primitive(self.exhaust.cells[-1].conservative)
        out = Boundary("outflow").flux(outlet, 1, self.eos)[0]
        ext = tuple(self.exhaust_mesh.areas[-1] * x for x in out)
        self.exhaust.cells[-1].apply_flux(ext, dt, self.eos, sign=-1.0)
        for key, idx in (("external_mass", 0), ("external_energy", 2),
                         ("external_species", 3)):
            self.ledger[key] += dt * ext[idx]
        for key, idx in (("port_mass", 0), ("port_energy", 2),
                         ("port_species", 3)):
            self.ledger[key] += dt * flux[idx]
        return {"flux": flux, "closed": face["area"] == 0.0,
                "external": ext, "area": face["area"]}

    def step(self, dt, *, angle=None, port_area=None):
        if not isinstance(dt, (int, float)) or not isfinite(dt) or dt <= 0:
            raise ValueError("dt must be positive")
        if port_area is not None:
            self.port_area = float(port_area)
        self.angle = self.angle + float(dt) if angle is None else float(angle)
        self.core.step(dt, angle=self.angle)
        trace = self._exhaust_step(dt)
        self.admissible()
        record = {"angle": self.angle, "exhaust": trace,
                  "totals": self.totals(), "dependency": self.dependency_status}
        self.history.append(record)
        return record

    def snapshot(self):
        return {"core": self.core.snapshot(), "exhaust": deepcopy(self.exhaust),
                "angle": self.angle, "port_area": self.port_area,
                "ledger": dict(self.ledger), "history": deepcopy(self.history)}

    def restore(self, snapshot):
        self.core.restore(snapshot["core"])
        self.exhaust = deepcopy(snapshot["exhaust"])
        self.angle = snapshot["angle"]
        self.port_area = snapshot["port_area"]
        self.ledger = dict(snapshot["ledger"])
        self.history = deepcopy(snapshot["history"])


def make_p5c_fixture(*, eos=None, cells=2, port_area=0.0):
    eos = eos or IdealGas()
    state = (1.0, 0.0, 100000.0, 0.2)
    ducts = tuple((state,) * cells for _ in range(3))
    crankcase = Chamber((1.0, 0.0, 105000.0, 0.3), 1.0e-3)
    cylinder = Chamber((1.0, 0.0, 100000.0, 0.2), 1.0e-2)
    return IntegratedP5C(crankcase, cylinder, ducts, (state,) * cells,
                         eos=eos, port_area=port_area)
