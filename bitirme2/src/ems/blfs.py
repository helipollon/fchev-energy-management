"""
ems/blfs.py — Boundary Layer Surface Following, Section 3.6.5 of MAT4901E.

BLFS is NOT an independent EMS: it is a lightweight rule-based protection
layer wrapped AROUND a real-time upper-level strategy (A-ECMS or MPC).
It acts on a hysteresis band of half-width 0.05 around the charge-
depleting SoC reference:

  SoC > ref + band :  fuel cell held at minimum power (P_dc = 0)
                      -> battery is actively depleted back to the band;
  SoC < ref - band :  fuel cell held at its PEAK-EFFICIENCY operating
                      point -> battery is recharged at the cheapest
                      possible hydrogen cost per joule;
  inside the band  :  the upper-level command passes through unchanged.

Additionally the fuel-cell load ramp is limited (Eq. 31):
    |dP_fc/dt| <= 5 kW/s
which suppresses gas starvation and membrane stress from fast transients.
The limit is enforced on the bus-side command P_dc; since P_dc and
P_fc,gross are related by a smooth monotone map, a 5 kW/s bus-side bound
implies an (even slightly stricter) gross-side bound.

The peak-efficiency point is computed once from the identified stack LUT
as the maximizer of the tank-to-bus efficiency  eta_sys = P_dc/(mdot*LHV),
i.e. including converter and auxiliary losses — this is the point where a
joule put into the battery via the FC is cheapest.
"""
import numpy as np
import config as cfg
from cost_model import soc_reference


class BLFSWrapper:
    """Decorates any controller exposing .step(k, soc, P_load_k)."""

    def __init__(self, inner, cost_model):
        self.inner = inner
        self.cm = cost_model
        c = cfg.BLFS_CFG
        self.band = c['band']
        self.ramp = c['ramp_max'] * cfg.DT     # max |Delta P_dc| per step
        self.u_prev = 0.0
        # peak system-efficiency P_dc (computed once, documented above)
        u = np.linspace(1e3, self.cm.P_dc_max, 400)
        eta_sys = u / (self.cm.mdot(u) * cfg.LHV_H2)
        self.u_peak = float(u[int(np.argmax(eta_sys))])
        self.eta_peak = float(eta_sys.max())

    def step(self, k, soc, P_load_k):
        ref = float(soc_reference(k * cfg.DT))
        if soc > ref + self.band:                    # deplete
            u = 0.0
        elif soc < ref - self.band:                  # recharge at peak eff.
            u = self.u_peak
        else:                                        # pass-through
            u = self.inner.step(k, soc, P_load_k)

        # Eq. (31): fuel-cell ramp limitation
        u = float(np.clip(u, self.u_prev - self.ramp, self.u_prev + self.ramp))
        u = float(np.clip(u, 0.0, self.cm.P_dc_max))
        self.u_prev = u
        return u
