"""
ems/dp.py — Dynamic Programming benchmark, Section 3.6.2 of MAT4901E.

Solves the complete optimal control problem, Eqs. (25)-(26), by the Bellman
backward recursion of Eq. (27):

    V_k(SoC) = min_{Pdc} { L_k(SoC, Pdc) + V_{k+1}(SoC') },  V_N = Phi(SoC_N)

on the discretized grids of the report (dSoC = 0.005, dPdc = 1 kW),
following the implementation structure of Sundstrom & Guzzella [15]:
  * the state grid is fixed, the successor state SoC' generally falls
    between grid nodes -> V_{k+1}(SoC') is obtained by LINEAR INTERPOLATION
    (this is the standard remedy against grid-quantization chattering);
  * infeasible transitions (SoC' outside [SoC_min, SoC_max]) get +inf;
  * the whole (n_soc x n_u) transition/cost tensor of one time step is
    evaluated in a single vectorized numpy pass, because both the Rint
    dynamics and the cost LUTs are algebraic.

DP knows the entire load profile in advance -> offline benchmark only
(report Table 4).  The result of the backward pass is a POLICY TABLE
u*(k, SoC); the forward pass in simulate.py replays this policy in closed
loop against the high-fidelity plant, so model mismatch (Rint vs 1-RC +
hysteresis) is honestly reflected in the reported cost.
"""
import numpy as np
import config as cfg
import battery as bat


class DPController:
    """Backward-pass solver + closed-loop policy lookup."""

    def __init__(self, cost_model, P_load, gamma=None):
        self.cm = cost_model
        self.P_load = P_load
        self.gamma = cfg.GAMMA if gamma is None else gamma
        # state grid
        b = cfg.BAT
        n_soc = int(round((b['SoC_max'] - b['SoC_min']) / cfg.DP_CFG['dSoC'])) + 1
        self.soc_grid = np.linspace(b['SoC_min'], b['SoC_max'], n_soc)
        # decision grid (1 kW)
        n_u = int(np.floor(self.cm.P_dc_max / cfg.DP_CFG['dPdc'])) + 1
        self.u_grid = np.arange(n_u) * cfg.DP_CFG['dPdc']
        self.policy = None            # int16 [N, n_soc] -> index into u_grid

    # ------------------------------------------------------------------ solve
    def solve(self):
        N = len(self.P_load)
        soc = self.soc_grid[:, None]              # (n_soc, 1)
        u   = self.u_grid[None, :]                # (1, n_u)
        b = cfg.BAT

        V = self.cm.terminal_cost(self.soc_grid, self.gamma)   # V_N
        policy = np.zeros((N, len(self.soc_grid)), dtype=np.int16)

        for k in range(N - 1, -1, -1):
            L, P_bat_eff = self.cm.stage_cost(u, self.P_load[k], soc)
            d_soc = bat.RintModel.delta_soc(P_bat_eff, soc)
            soc_next = soc + d_soc                              # (n_soc, n_u)
            # interpolate cost-to-go; mark out-of-window states infeasible
            V_next = np.interp(soc_next.ravel(), self.soc_grid, V
                               ).reshape(soc_next.shape)
            # only the LOWER bound can be violated: the SoC_max ceiling is
            # already enforced inside stage_cost via charge curtailment
            bad = soc_next < b['SoC_min']
            total = L + V_next
            total[bad] = np.inf
            policy[k] = np.argmin(total, axis=1)
            V = np.take_along_axis(total, policy[k][:, None], axis=1)[:, 0]

        self.policy = policy
        self.V0 = V                                # cost-to-go at k = 0
        return self

    # ------------------------------------------------------------- closed loop
    def step(self, k, soc, P_load_k):
        """Policy lookup with linear interpolation between SoC nodes."""
        i = np.searchsorted(self.soc_grid, soc) - 1
        i = int(np.clip(i, 0, len(self.soc_grid) - 2))
        # interpolate the CONTROL between the two neighbouring nodes —
        # smoother than nearest-node and consistent with the value interp
        w = (soc - self.soc_grid[i]) / (self.soc_grid[i+1] - self.soc_grid[i])
        u = ((1 - w) * self.u_grid[self.policy[k, i]]
             + w      * self.u_grid[self.policy[k, i + 1]])
        return float(np.clip(u, 0.0, self.cm.P_dc_max))
