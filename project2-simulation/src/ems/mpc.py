"""
ems/mpc.py — Model Predictive Control, Section 3.6.4 of MAT4901E.

At every instant k the finite-horizon restriction of the OCP, Eq. (30), is
solved over Np = 15 steps under the CONSTANT-LOAD assumption
P_load(j) = P_load(k) for j = k..k+Np-1 (no telematic preview available),
only the first move is applied, and the optimization repeats at k+1.

Design note — why grid DP instead of a QP transcription:
The report sketches a QP transcription; during implementation this was
replaced by an exact grid-based DP over the horizon, for two documented
reasons:
  1. The stage cost is NON-CONVEX in P_dc (the hydrogen consumption map
     inherits the curvature of the identified polarization curve, and the
     direction-dependent battery efficiency of Eq. (20) introduces a kink
     at P_bat = 0).  A QP would require convex surrogates and could return
     a minimizer of the surrogate, not of the model.
  2. The state is scalar, so an exhaustive local DP is cheap: the SoC can
     move at most ~0.002/s, hence a window of +/-0.035 around the current
     SoC covers every trajectory the horizon can reach.  With 36 local
     nodes and a 2 kW decision grid the subproblem is solved EXACTLY
     (up to grid resolution) in a few milliseconds of vectorized numpy.
The terminal term of Eq. (30) tracks the charge-depleting reference at the
horizon end with weight gamma_mpc.

Offset-free correction: the constant-load assumption is biased — traction
peaks make the controller over-protect the battery (it believes the peak
will last the whole horizon), while idle/regen phases predict no depletion
need; the net effect is a persistent positive SoC offset that no finite
gamma_mpc removes (a pure terminal weight cannot cancel a persistent
prediction-model bias; this is the classical offset problem of MPC).
The standard remedy is integral action on the tracking error (offset-free
MPC): the tracked reference is shifted by the low-pass-accumulated bias,
    ref_corr = ref - b_int,   b_int <- b_int + beta*(SoC - ref(t_k)),
which restores zero steady-state offset while leaving the fast economic
optimization untouched.
"""
import numpy as np
import config as cfg
import battery as bat
from cost_model import soc_reference


class MPCController:

    def __init__(self, cost_model):
        self.cm = cost_model
        c = cfg.MPC_CFG
        self.Np = c['Np']
        self.gamma = c['gamma_mpc']
        n_u = int(np.floor(self.cm.P_dc_max / c['dPdc'])) + 1
        self.u_grid = np.arange(n_u) * c['dPdc']
        # local state window: 2*n_loc+1 nodes, resolution dSoC
        self.offsets = np.arange(-c['n_loc'], c['n_loc'] + 1) * c['dSoC']
        # offset-free integral state (see module docstring)
        self.b_int = 0.0
        self.beta = c.get('beta_int', 0.05)

    def step(self, k, soc, P_load_k):
        b = cfg.BAT
        grid = soc + self.offsets                    # local SoC nodes
        u = self.u_grid[None, :]                     # (1, n_u)
        s_col = grid[:, None]                        # (n_loc*2+1, 1)

        # transitions & stage costs are identical for every j in the horizon
        # (constant-load assumption) -> compute the tensors once
        L, P_bat_eff = self.cm.stage_cost(u, P_load_k, s_col)
        d_soc = bat.RintModel.delta_soc(P_bat_eff, s_col)
        soc_next = s_col + d_soc                     # (n_s, n_u)
        bad = soc_next < b['SoC_min']     # upper bound handled by curtailment

        # terminal cost at the horizon end, Eq. (30), with the offset-free
        # integral correction of the tracked reference
        self.b_int += self.beta * (soc - float(soc_reference(k * cfg.DT)))
        self.b_int = float(np.clip(self.b_int, -0.05, 0.05))
        t_end = (k + self.Np) * cfg.DT
        ref_corr = float(np.clip(soc_reference(t_end) - self.b_int,
                                 b['SoC_min'], b['SoC_max']))
        V = self.gamma * (grid - ref_corr) ** 2

        first_move = None
        for j in range(self.Np - 1, -1, -1):
            V_next = np.interp(soc_next.ravel(), grid, V).reshape(soc_next.shape)
            total = L + V_next
            total[bad] = np.inf
            idx = np.argmin(total, axis=1)
            V = np.take_along_axis(total, idx[:, None], axis=1)[:, 0]
            if j == 0:
                first_move = idx

        # apply the first move of the node closest to the true SoC (= centre)
        centre = len(self.offsets) // 2
        return float(self.u_grid[first_move[centre]])
