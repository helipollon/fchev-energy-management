"""
fuel_cell.py — Mann–Amphlett generalized steady-state electrochemical model
(GSSEM) of the PEMFC stack, Section 3.3.2 of the MAT4901E report.

Single-cell voltage, Eq. (5):
    V_FC = E_Nernst - V_act - V_ohm - V_con

  Eq. (6)  E_Nernst = 1.229 - 8.5e-4 (T-298.15)
                      + 4.308e-5 T [ ln p*H2 + 0.5 ln p*O2 ]
  Eq. (7)  V_act = -[ xi1 + xi2 T + xi3 T ln(C*O2) + xi4 T ln(i) ]
  Eq. (8)  V_ohm = i (R_M + R_C),   R_M = rho_M l / A
  Eq. (9)  V_con = -beta ln(1 - J/J_max)

The membrane resistivity rho_M uses the empirical correlation of
Mann et al. [6] with effective water content lambda.

The dissolved O2 concentration at the catalyst interface follows Henry's
law (Amphlett et al.):  C*O2 = p*O2 / (5.08e6 exp(-498/T))  [mol/cm^3].

Hydrogen consumption (Faraday's law, exact — no empirical fit needed):
    mdot_H2 = N_cell * I * M_H2 / (2 F)                       [kg/s]
so the LHV stack efficiency is proportional to cell voltage:
    eta_fc = P_gross / (mdot_H2 * LHV) = 2 F * V_cell / (M_H2 * LHV)
           = V_cell / 1.254 V
This is why the efficiency map of Eq. (11) can be generated purely from
the polarization curve (identified in param_id.py).
"""
import numpy as np
import config as cfg


class GSSEM:
    """Zero-dimensional static PEMFC stack model.

    Parameters can be overridden with the PSO-identified set
    (data/identified_stack_params.json) via the `params` argument.
    """

    #: names of the coefficients that PSO identifies, in order
    ID_KEYS = ['xi1', 'xi2', 'xi3', 'xi4', 'lam_w', 'R_C', 'beta_con', 'J_max']

    def __init__(self, params=None):
        p = dict(cfg.FC)
        if params:
            p.update(params)
        self.p = p
        self.T = p['T_stack']

    # ---- electrochemistry --------------------------------------------------
    def cell_voltage(self, J):
        """Single-cell voltage [V] at current density J [A/cm^2] (vectorized)."""
        p, T = self.p, self.T
        J = np.asarray(J, dtype=float)
        J = np.clip(J, 1e-4, p['J_max'] * 0.9999)   # avoid log singularities
        i = J * p['A_cell']                          # stack current [A]

        # Eq. (6) Nernst potential
        E = (1.229 - 8.5e-4 * (T - 298.15)
             + 4.308e-5 * T * (np.log(p['p_H2']) + 0.5 * np.log(p['p_O2'])))

        # Henry's law: dissolved O2 concentration [mol/cm^3]
        C_O2 = p['p_O2'] / (5.08e6 * np.exp(-498.0 / T))

        # Eq. (7) activation overvoltage (Tafel-type, semi-empirical)
        V_act = -(p['xi1'] + p['xi2'] * T + p['xi3'] * T * np.log(C_O2)
                  + p['xi4'] * T * np.log(i))

        # Eq. (8) ohmic loss with Mann's membrane resistivity correlation
        lam = p['lam_w']
        rho_M = (181.6 * (1 + 0.03 * J + 0.062 * (T / 303.0) ** 2 * J ** 2.5)
                 / ((lam - 0.634 - 3.0 * J) * np.exp(4.18 * (T - 303.0) / T)))
        R_M = rho_M * p['l_mem'] / p['A_cell']
        V_ohm = i * (R_M + p['R_C'])

        # Eq. (9) concentration loss
        V_con = -p['beta_con'] * np.log(1.0 - J / p['J_max'])

        return E - V_act - V_ohm - V_con

    # ---- stack-level quantities ---------------------------------------------
    def stack_power_gross(self, J):
        """Gross electrical stack power [W], Eq. (10)."""
        V = self.cell_voltage(J)
        I = np.asarray(J) * self.p['A_cell']
        return self.p['N_cell'] * V * I

    def h2_flow(self, J):
        """Hydrogen mass flow [kg/s] from Faraday's law (exact)."""
        I = np.asarray(J) * self.p['A_cell']
        return self.p['N_cell'] * I * cfg.M_H2 / (2.0 * cfg.FARADAY)

    def efficiency(self, J):
        """LHV stack efficiency = V_cell / 1.254 V."""
        return self.cell_voltage(J) * 2.0 * cfg.FARADAY / (cfg.M_H2 * cfg.LHV_H2)

    # ---- controller-facing look-up tables (Eq. 11) ---------------------------
    def build_lut(self, n=400):
        """Generate the 1-D efficiency/consumption LUT over gross power.

        Returns dict with sorted arrays:
          P_gross [W], eta_fc [-], mdot [kg/s]
        Only the monotonically increasing branch of P(J) is kept (beyond the
        power peak the same power is reachable at lower J with less H2, so
        the controller never operates there).
        """
        J = np.linspace(1e-3, self.p['J_max'] * 0.995, n)
        P = self.stack_power_gross(J)
        k_peak = int(np.argmax(P))
        J, P = J[:k_peak + 1], P[:k_peak + 1]
        return dict(P_gross=P, eta=self.efficiency(J), mdot=self.h2_flow(J),
                    J=J, P_peak=float(P[-1]))


def mdot_of_Pgross(lut, P_gross):
    """Interpolate hydrogen flow [kg/s] for a gross power demand [W]."""
    return np.interp(P_gross, lut['P_gross'], lut['mdot'])


if __name__ == '__main__':
    fc = GSSEM()
    lut = fc.build_lut()
    print(f"P_gross peak = {lut['P_peak']/1e3:.1f} kW at J = {lut['J'][-1]:.2f} A/cm^2")
    for Pk in [12e3, 30e3, 60e3, 100e3, lut['P_peak']]:
        eta = np.interp(Pk, lut['P_gross'], lut['eta'])
        print(f"  P = {Pk/1e3:6.1f} kW -> eta_LHV = {eta:.3f}")
