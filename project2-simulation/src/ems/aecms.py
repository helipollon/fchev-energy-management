"""
ems/aecms.py — Adaptive ECMS, Section 3.6.3 of MAT4901E.

At every instant the controller minimizes the Hamiltonian of Eq. (28) over
a discrete P_dc grid:

    H(SoC, Pdc, s, t) = L(SoC, Pdc) + s(t) * (SoC_k - SoC_{k+1}(Pdc))

i.e. the co-state lambda of Pontryagin's principle is replaced by the
equivalence factor s(t) acting on the SoC *decrement* of the step.  A
positive s makes battery depletion look expensive, a negative s makes it
look attractive.

Plug-in twist (report + Xu [4]): the running cost L already prices battery
energy at its grid-equivalent monetary value (Eq. 21), so the ECONOMIC
trade-off is fully contained in L.  The equivalence factor therefore does
not need a heuristic baseline (s0 = 0); its only job is to keep the SoC on
the charge-depleting reference, which is done by the PI law of Eq. (29):

    s(t) = s0 + kp*e(t) + ki*int_0^t e(tau) dtau,  e = SoC_ref - SoC.

  * SoC above the reference -> e < 0 -> s decreases -> battery favoured;
  * SoC below the reference -> e > 0 -> s increases -> fuel cell favoured.
Without this feedback a constant factor drives the strategy to the
physical SoC limits (shown in [4]) because grid electricity is uniformly
cheaper than hydrogen under the default price scenario.

The anti-windup clamp on the integrator prevents the well-known burst at
the end of the trip when the terminal constraint saturates the actuator.
"""
import numpy as np
import config as cfg
import battery as bat
from cost_model import soc_reference


class AECMSController:

    def __init__(self, cost_model):
        self.cm = cost_model
        c = cfg.AECMS_CFG
        self.s0, self.kp, self.ki = c['s0'], c['kp'], c['ki']
        n_u = int(np.floor(self.cm.P_dc_max / c['dPdc'])) + 1
        self.u_grid = np.arange(n_u) * c['dPdc']
        self.e_int = 0.0
        self.I_MAX = 2.0 / max(self.ki, 1e-9)   # anti-windup: |ki*e_int| <= 2 EUR/SoC

    def step(self, k, soc, P_load_k):
        # --- Eq. (29): PI adaptation of the equivalence factor -------------
        e = float(soc_reference(k * cfg.DT) - soc)
        self.e_int = float(np.clip(self.e_int + e * cfg.DT,
                                   -self.I_MAX, self.I_MAX))
        s = self.s0 + self.kp * e + self.ki * self.e_int

        # --- Eq. (28): pointwise Hamiltonian minimization -------------------
        u = self.u_grid
        L, P_bat_eff = self.cm.stage_cost(u, P_load_k, soc)
        d_soc = bat.RintModel.delta_soc(P_bat_eff, soc)
        H = L + s * (-d_soc)          # (SoC_k - SoC_{k+1}) = -d_soc
        # hard SoC window protection (upper bound handled by curtailment
        # inside stage_cost, so only the lower bound is guarded here)
        soc_next = soc + d_soc
        H[soc_next < cfg.BAT['SoC_min']] = np.inf
        return float(u[int(np.argmin(H))])
