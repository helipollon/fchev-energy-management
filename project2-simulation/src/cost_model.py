"""
cost_model.py — Power-flow chain and monetary running cost,
Sections 3.4 and 3.5 of the MAT4901E report.

Causal chain (report Section 3.4):
    u = P_dc  --Eq.(2)-->  P_bat = P_load - P_dc
    P_dc      --Eq.(16)->  P_fc,net = P_dc/eta_dc,
                           P_fc,gross = (P_fc,net + P_aux0) / (1 - aux_frac)
    P_fc,gross --Eq.(11)-> mdot_H2  (efficiency LUT from the identified GSSEM)
    P_bat     --Eq.(17)->  I_bat --Eq.(18)-> SoC_{k+1}

Auxiliary model note: the report quotes P_aux/P_gross ~ 0.10-0.13 [17].
A purely proportional auxiliary load would make the tank-to-bus efficiency
monotone in power, i.e. the fuel cell would have no interior optimum point.
Real stacks have a fixed auxiliary floor (compressor idle, pumps, control
electronics) which is why the measured SYSTEM efficiency of the Mirai
peaks near 12 kW [17].  We therefore use the affine model
    P_aux = P_aux0 + c_aux * P_gross,   P_aux0 = 1.0 kW, c_aux = 0.09,
which stays inside the 0.10-0.13 ratio band above ~30 kW and reproduces
the interior efficiency peak.  P_aux0 applies only while the FC is ON
(P_dc > 0); at P_dc = 0 the stack is assumed idled at zero flow.

Running cost (Eqs. 19-22):
    C_fc  = M_H2 * mdot_H2 * dt                       [EUR]  >= 0
    C_bat = M_ele' * P_bat / eta_eff * dt             [EUR]  sign follows P_bat
with the direction-dependent efficiency of Eq. (20) evaluated through the
Rint-model LUT-style functions in battery.py.
"""
import numpy as np
import config as cfg
import battery as bat

P_AUX0 = 1.0e3    # W  fixed auxiliary floor while FC is on
C_AUX  = 0.09     # -  proportional auxiliary coefficient


class CostModel:
    """Bundles the identified FC LUT and a price scenario.

    All methods are vectorized: P_dc, P_load, soc can be numpy arrays of a
    common broadcast shape — this is what makes the DP recursion fast.
    """

    def __init__(self, fc_lut, scenario='default'):
        self.lut = fc_lut
        pr = cfg.PRICES[scenario]
        self.M_H2  = pr['M_H2']                 # EUR/kg
        self.M_ele = pr['M_ele'] / 3.6e6        # EUR/J   (from EUR/kWh)
        # feasible P_dc ceiling: converter rating AND identified stack peak
        gross_ceiling = (1.0 - C_AUX) * self.lut['P_peak'] - P_AUX0
        self.P_dc_max = min(cfg.P_DC_MAX, gross_ceiling * cfg.ETA_DC)

    # ---- fuel-cell chain ----------------------------------------------------
    def p_gross(self, P_dc):
        """Gross stack power [W] for bus power P_dc (Eq. 16 + affine aux)."""
        P_dc = np.asarray(P_dc, dtype=float)
        P_net = P_dc / cfg.ETA_DC
        Pg = (P_net + P_AUX0) / (1.0 - C_AUX)
        return np.where(P_dc > 0.0, Pg, 0.0)

    def mdot(self, P_dc):
        """Hydrogen flow [kg/s] for bus power P_dc (Eq. 11 via LUT)."""
        Pg = self.p_gross(P_dc)
        m = np.interp(Pg, self.lut['P_gross'], self.lut['mdot'])
        return np.where(Pg > 0.0, m, 0.0)

    def cost_fc(self, P_dc):
        """Eq. (19): hydrogen cost of one interval [EUR]."""
        return self.M_H2 * self.mdot(P_dc) * cfg.DT

    # ---- battery chain --------------------------------------------------------
    def cost_bat(self, P_bat, soc):
        """Eq. (20)-(21): grid-equivalent electricity cost [EUR].

        Discharge (P_bat>0): grid energy invested per bus joule exceeds 1
          -> divide by the round-trip product (eta_dis*eta_chg).
        Charge (P_bat<0): only the recoverable fraction is credited
          -> multiply by the round-trip product.
        """
        P_bat = np.asarray(P_bat, dtype=float)
        eta_d = bat.RintModel.eta_dis(np.maximum(P_bat, 0.0), soc)
        eta_c = bat.RintModel.eta_chg(np.minimum(P_bat, 0.0), soc)
        cost_dis = self.M_ele * P_bat / (eta_d * 0.98)          # P>0 branch
        cost_chg = self.M_ele * P_bat * (eta_c * 0.98)          # P<0 branch
        # 0.98: coulombic/charger round-trip share attributed symmetrically
        return np.where(P_bat >= 0.0, cost_dis, cost_chg) * cfg.DT

    # ---- total running cost ----------------------------------------------------
    def stage_cost(self, P_dc, P_load, soc):
        """Eq. (22): L_k = C_fc + C_bat for decision P_dc at load P_load.

        Charging is curtailed by TWO physical mechanisms, both of which
        divert the excess regenerative power to the friction brakes
        (no credit is earned for the dissipated remainder):
          1. the 4C datasheet charge-current limit of the pack;
          2. the SoC_max ceiling: the BMS tapers charging so the window
             [SoC_min, SoC_max] is never violated.  Without this term the
             upper boundary of the DP state grid would be spuriously
             infeasible whenever a regeneration event occurs near SoC_max.
        """
        P_bat = P_load - P_dc                                    # Eq. (2)
        soc = np.asarray(soc, dtype=float)
        b = cfg.BAT
        # mechanism 2: most negative current that still respects SoC_max
        room = np.maximum(b['SoC_max'] - soc, 0.0)
        I_min = -room * b['Q_pack'] * 3600.0 / (b['eta_coul'] * cfg.DT)
        v = bat.ocv_pack(soc, 'avg')
        P_soc_lim = I_min * (v - I_min * bat.RintModel.Rs)
        # mechanism 1: 4C limit
        P_chg_lim = bat.pack_charge_power_limit(soc)
        P_bat_eff = np.maximum(P_bat, np.maximum(P_chg_lim, P_soc_lim))
        return self.cost_fc(P_dc) + self.cost_bat(P_bat_eff, soc), P_bat_eff

    def terminal_cost(self, soc_N, gamma=None):
        """Eq. (23): soft quadratic terminal penalty [EUR]."""
        g = cfg.GAMMA if gamma is None else gamma
        return g * (np.asarray(soc_N) - cfg.BAT['SoC_target']) ** 2


# ---------------------------------------------------------------------------
# Charge-depleting SoC reference, Eq. (29)
#
# The report specifies a reference "decreasing linearly from 0.90 to 0.25
# over the trip".  A reference linear in TIME turned out to be infeasible
# in closed loop: during the final deceleration-to-standstill (and every
# idle phase) there is no traction load, hence the battery physically
# CANNOT be depleted, while the time-linear reference keeps falling.  All
# real-time strategies then end the trip stranded ~0.025 above the target
# and collect a large terminal penalty that reflects the reference design,
# not the strategy quality.
#
# Remedy (standard in the plug-in EMS literature, cf. Onori [14] Ch. 6):
# make the reference linear in CUMULATIVE POSITIVE TRACTION ENERGY, which
# is exactly the "depletion opportunity" available up to time k:
#     ref(k) = SoC_0 + (SoC_tgt - SoC_0) * E_cum(k) / E_tot .
# For the fixed reference trip E_cum is known offline (the same standing
# assumption DP already makes); in a real vehicle it would come from the
# navigation system.  set_reference() must be called once per trip; if it
# has not been called, the time-linear reference of Eq. (29) is used.
# ---------------------------------------------------------------------------
_REF = None


def set_reference(P_load):
    """Build the energy-based reference array from the trip load profile."""
    global _REF
    e_cum = np.concatenate([[0.0], np.cumsum(np.maximum(P_load, 0.0))])
    frac = e_cum / e_cum[-1]
    _REF = cfg.BAT['SoC_0'] + (cfg.BAT['SoC_target'] - cfg.BAT['SoC_0']) * frac


def soc_reference(t):
    """SoC reference at time t [s] (energy-based if set, else time-linear)."""
    t = np.asarray(t, dtype=float)
    if _REF is not None:
        idx = np.clip(t / cfg.DT, 0, len(_REF) - 1)
        return np.interp(idx, np.arange(len(_REF)), _REF)
    T = cfg.N_CYCLES * 1800.0
    frac = np.clip(t / T, 0.0, 1.0)
    return cfg.BAT['SoC_0'] + (cfg.BAT['SoC_target'] - cfg.BAT['SoC_0']) * frac
