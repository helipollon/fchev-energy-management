"""
simulate.py — Two-layer closed-loop simulation, Section 3.7 of MAT4901E.

Layer separation (Onori et al. [14]):
  CONTROLLER layer: whatever strategy object is passed in; it sees only the
    measured SoC and the instantaneous load, and internally reasons with
    the simplified Rint model + FC efficiency LUT.
  PLANT layer: the high-fidelity truth — 1-RC + hysteresis battery
    (battery.PlantBattery) and the identified GSSEM hydrogen-consumption
    chain.  The plant, not the controller model, produces every number
    reported in the results.

Per step k:
  1. u_k = controller.step(k, SoC_meas, P_load_k)      [wall-clock timed]
  2. P_bat = P_load_k - u_k                            Eq. (2)
  3. plant battery absorbs P_bat (clipping + friction braking handled inside)
  4. hydrogen flow from the identified LUT chain       Eq. (11)/(16)
  5. monetary accounting with the plant trajectory     Eqs. (19)-(22)

Reported metrics (report Section 3.7): total operating cost incl. terminal
penalty [EUR and EUR/100 km], H2 mass [kg], battery electricity [kWh],
terminal SoC error, FC quasi-stability (mean |dP_fc/dt| and # of on/off
events), mean per-step controller CPU time.
"""
import time
import numpy as np
import config as cfg
import battery as bat


def run(controller, cost_model, P_load, label=''):
    N = len(P_load)
    plant = bat.PlantBattery()

    soc_tr   = np.empty(N + 1); soc_tr[0] = plant.soc
    u_tr     = np.empty(N)
    pbat_tr  = np.empty(N)
    fric_tr  = np.empty(N)
    cost_fc  = 0.0
    cost_bat = 0.0
    m_h2     = 0.0
    cpu      = 0.0

    for k in range(N):
        t0 = time.perf_counter()
        u = controller.step(k, plant.soc, P_load[k])
        cpu += time.perf_counter() - t0

        # ---- plant execution ------------------------------------------------
        res = plant.step(P_load[k] - u)                     # Eq. (2)
        m_dot = float(cost_model.mdot(u))                   # Eq. (11)/(16)
        m_h2 += m_dot * cfg.DT

        # ---- monetary accounting on plant quantities (Eqs. 19-22) -----------
        cost_fc  += cost_model.M_H2 * m_dot * cfg.DT
        cost_bat += float(cost_model.cost_bat(res['P_actual'], soc_tr[k]))

        u_tr[k], pbat_tr[k], fric_tr[k] = u, res['P_actual'], res['P_friction']
        soc_tr[k + 1] = plant.soc

    # ---- metrics -------------------------------------------------------------
    dist_km = None   # filled by caller (depends on cycle)
    term_pen = float(cost_model.terminal_cost(soc_tr[-1]))
    du = np.diff(u_tr, prepend=u_tr[0])
    onoff = int(np.sum(np.diff((u_tr > 0.5e3).astype(int)) != 0))

    return dict(
        label=label,
        soc=soc_tr, u=u_tr, p_bat=pbat_tr, p_fric=fric_tr,
        m_h2_kg=m_h2,
        e_bat_kWh=(soc_tr[0] - soc_tr[-1]) * cfg.BAT['E_nom_Wh'] / 1e3,
        cost_fc=cost_fc, cost_bat=cost_bat,
        cost_run=cost_fc + cost_bat,
        term_penalty=term_pen,
        cost_total=cost_fc + cost_bat + term_pen,
        soc_final=float(soc_tr[-1]),
        soc_err=float(soc_tr[-1] - cfg.BAT['SoC_target']),
        fc_ramp_mean=float(np.mean(np.abs(du))),      # W/step, quasi-stability
        fc_onoff=onoff,
        cpu_ms=cpu / N * 1e3,
    )
