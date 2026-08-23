"""
battery.py — Lithium-ion battery pack models, Section 3.3.3 of MAT4901E.

Two models, used at two different layers (two-level approach of Onori [14]):

1. PlantBattery  — high-fidelity 1-RC + hysteresis model (Eqs. 12-15).
   Used ONLY by the physical simulation layer.  States:
     SoC   — state of charge (Coulomb counting, Eq. 13)
     V_RC1 — relaxation (diffusion) voltage of the RC branch (Eq. 12)
     V_OC  — hysteretic open-circuit voltage (Huria law, Eq. 15)

2. RintModel     — simplified internal-resistance model.
   Used by ALL controllers (DP / A-ECMS / MPC): only the SoC state is
   tracked, V_OC is the static average of the charge/discharge branches
   and the RC branch is neglected.  This is deliberately *less accurate*
   than the plant: the controller never has perfect model knowledge in a
   real vehicle, and the two-level split quantifies exactly this effect.

LFP OCV curves: the charge and discharge branches of the A123 ANR26650M1B
cell are represented by 8th-order polynomials in SoC as in Nejad [11].
The knot values below reproduce the published curves of [11],[12]:
a flat plateau of ~3.3 V between 20% and 80% SoC and a charge/discharge
separation (hysteresis) of ~25-40 mV that widens at low SoC.

Sign convention (report Eq. 2): current i > 0 <=> discharge.
"""
import numpy as np
import config as cfg

B = cfg.BAT

# ---------------------------------------------------------------------------
# OCV branch data (cell level, V vs SoC) — representative of ANR26650M1B
# ---------------------------------------------------------------------------
_SOC_KNOTS = np.array([0.00, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50,
                       0.60, 0.70, 0.80, 0.90, 0.95, 1.00])
_V_DIS = np.array([2.90, 3.12, 3.19, 3.22, 3.24, 3.26, 3.28,
                   3.29, 3.30, 3.31, 3.33, 3.36, 3.44])   # discharge branch
_V_CHG = np.array([3.00, 3.18, 3.24, 3.26, 3.28, 3.30, 3.31,
                   3.32, 3.33, 3.34, 3.37, 3.41, 3.49])   # charge branch

# 8th-order polynomial fits (as in [11]); dense resampling avoids Runge
# oscillation dominating the fit at the plateau
_s_dense = np.linspace(0, 1, 200)
POLY_DIS = np.polyfit(_s_dense, np.interp(_s_dense, _SOC_KNOTS, _V_DIS), 8)
POLY_CHG = np.polyfit(_s_dense, np.interp(_s_dense, _SOC_KNOTS, _V_CHG), 8)


def ocv_cell(soc, branch):
    """Cell OCV [V] on the given branch ('dis' | 'chg' | 'avg')."""
    soc = np.clip(soc, 0.0, 1.0)
    if branch == 'dis':
        return np.polyval(POLY_DIS, soc)
    if branch == 'chg':
        return np.polyval(POLY_CHG, soc)
    return 0.5 * (np.polyval(POLY_DIS, soc) + np.polyval(POLY_CHG, soc))


def ocv_pack(soc, branch='avg'):
    """Pack OCV [V] = Ns * cell OCV."""
    return B['Ns'] * ocv_cell(soc, branch)


# ---------------------------------------------------------------------------
# Shared electrical helper — Eq. (17)
# ---------------------------------------------------------------------------
def current_from_power(P_bat, V_oc_eff, Rs):
    """Solve V_term * I = P_bat with V_term = V_oc_eff - I*Rs  (Eq. 17).

    Returns the physically valid root
        I = [V - sqrt(V^2 - 4 Rs P)] / (2 Rs).
    The discriminant is clipped at 0: an infeasible demand saturates at the
    pack power capability P_cap = V^2/(4 Rs) (this is exactly the natural
    encoding of the power limit mentioned under Eq. 17 of the report).
    Vectorized in both arguments.
    """
    disc = V_oc_eff ** 2 - 4.0 * Rs * P_bat
    disc = np.maximum(disc, 0.0)
    return (V_oc_eff - np.sqrt(disc)) / (2.0 * Rs)


def pack_charge_power_limit(soc):
    """Most negative admissible P_bat [W] at the 4C charge-current limit.

    P_bat = V_term*I with I = -I_chg_max, V_term = V_oc + I_chg_max*Rs.
    Regenerative power beyond this limit is dissipated in friction brakes.
    """
    v = ocv_pack(soc, 'avg')
    return -B['I_chg_max'] * (v + B['I_chg_max'] * B['Rs_pack'])


def pack_discharge_power_limit(soc):
    """Largest admissible P_bat [W]: min(quadratic capability, 20C limit)."""
    v = ocv_pack(soc, 'avg')
    p_cap = v ** 2 / (4.0 * B['Rs_pack'])
    p_20c = B['I_dis_max'] * (v - B['I_dis_max'] * B['Rs_pack'])
    return np.minimum(p_cap, p_20c)


# ---------------------------------------------------------------------------
# 1. High-fidelity plant model
# ---------------------------------------------------------------------------
class PlantBattery:
    """1-RC + hysteresis pack model — the 'truth' of the simulation."""

    def __init__(self, soc0=None):
        self.soc  = B['SoC_0'] if soc0 is None else soc0
        self.v_rc = 0.0                                   # relaxed start
        self.v_oc = ocv_pack(self.soc, 'dis')             # start on discharge branch
        # Eq. (12) discrete RC coefficients
        tau = B['R1_pack'] * B['C1_pack']
        self.a = np.exp(-cfg.DT / tau)
        self.b = B['R1_pack'] * (1.0 - self.a)

    def step(self, P_bat):
        """Apply terminal power P_bat [W] for one interval of DT seconds.

        Returns dict(I, V_term, P_actual, P_friction, soc).
        P_friction is regenerative power rejected because of the 4C charge
        limit (goes to the mechanical brakes; costs nothing, earns nothing).
        """
        # effective source voltage seen by the quadratic: OCV minus the
        # relaxation state (Eq. 14 substituted into P = V*I)
        v_eff = self.v_oc - self.v_rc

        I = current_from_power(P_bat, v_eff, B['Rs_pack'])
        # enforce current limits (datasheet 4C charge / 20C discharge) and
        # the BMS charge taper that keeps SoC <= SoC_max
        room = max(B['SoC_max'] - self.soc, 0.0)
        I_soc_min = -room * B['Q_pack'] * 3600.0 / (B['eta_coul'] * cfg.DT)
        I_lim = np.clip(I, max(-B['I_chg_max'], I_soc_min), B['I_dis_max'])
        P_act = (v_eff - I_lim * B['Rs_pack']) * I_lim
        P_fric = min(P_bat - P_act, 0.0)   # only regen can be rejected

        # ---- state updates -------------------------------------------------
        # Eq. (12): RC relaxation voltage
        self.v_rc = self.a * self.v_rc + self.b * I_lim
        # Eq. (13): Coulomb counting
        d_soc = -B['eta_coul'] * I_lim * cfg.DT / (B['Q_pack'] * 3600.0)
        soc_new = float(np.clip(self.soc + d_soc, 0.0, 1.0))
        # Eq. (15): hysteretic OCV — relaxes toward the active branch with
        # charge throughput |dSoC| as the integration variable
        branch = 'chg' if d_soc > 0 else 'dis'
        v_ref  = ocv_pack(soc_new, branch)
        dv_ref = v_ref - ocv_pack(self.soc, branch)
        self.v_oc = (self.v_oc + dv_ref
                     + B['m_hyst'] * (v_ref - self.v_oc) * abs(d_soc))
        self.soc = soc_new

        v_term = v_eff - I_lim * B['Rs_pack']
        return dict(I=float(I_lim), V_term=float(v_term),
                    P_actual=float(P_act), P_friction=float(P_fric),
                    soc=self.soc)


# ---------------------------------------------------------------------------
# 2. Controller-layer Rint model (vectorized, stateless)
# ---------------------------------------------------------------------------
class RintModel:
    """Static OCV-Rs model used inside every optimization routine."""

    Rs = B['Rs_pack']

    @staticmethod
    def delta_soc(P_bat, soc):
        """SoC increment for one DT interval (vectorized, Eqs. 17-18)."""
        v = ocv_pack(soc, 'avg')
        I = current_from_power(P_bat, v, RintModel.Rs)
        I = np.clip(I, -B['I_chg_max'], B['I_dis_max'])
        return -B['eta_coul'] * I * cfg.DT / (B['Q_pack'] * 3600.0)

    @staticmethod
    def eta_dis(P_bat, soc):
        """Discharge efficiency V_term/V_oc (P_bat > 0)."""
        v = ocv_pack(soc, 'avg')
        I = current_from_power(P_bat, v, RintModel.Rs)
        return np.clip((v - I * RintModel.Rs) / v, 1e-3, 1.0)

    @staticmethod
    def eta_chg(P_bat, soc):
        """Charge efficiency V_oc/V_term (P_bat < 0)."""
        v = ocv_pack(soc, 'avg')
        I = current_from_power(P_bat, v, RintModel.Rs)
        return np.clip(v / (v - I * RintModel.Rs), 1e-3, 1.0)


if __name__ == '__main__':
    # quick physical sanity checks
    print(f"pack: {B['Q_pack']} Ah, Rs={B['Rs_pack']*1e3:.1f} mOhm, "
          f"E_nom={B['E_nom_Wh']/1e3:.2f} kWh")
    print(f"OCV(0.5) dis/chg = {ocv_pack(0.5,'dis'):.1f}/{ocv_pack(0.5,'chg'):.1f} V")
    print(f"charge power limit @SoC .9 = {pack_charge_power_limit(0.9)/1e3:.1f} kW")
    print(f"discharge power limit @SoC .25 = {pack_discharge_power_limit(0.25)/1e3:.1f} kW")
    # constant 10 kW discharge for 10 min
    pb = PlantBattery()
    for _ in range(600):
        r = pb.step(10e3)
    print(f"after 10 min @10 kW: SoC={pb.soc:.4f}, Vterm={r['V_term']:.1f} V, "
          f"Vrc={pb.v_rc*1e3:.1f} mV")
