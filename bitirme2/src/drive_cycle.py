"""
drive_cycle.py — WLTP Class 3b speed profile and bus load trajectory.

Implements Section 3.3.1 of the MAT4901E report:

  Eq. (3)  P_wheel = [ m a + m g Cr cos(alpha) + 0.5 rho Cd Af v^2
                       + m g sin(alpha) ] * v          (alpha = 0, level road)
  Eq. (4)  P_load  = P_wheel/eta_dt   if P_wheel >= 0  (traction)
           P_load  = P_wheel*eta_dt   if P_wheel <  0  (regenerative braking)

The speed data in data/wltp_class3b_kmh.csv is the OFFICIAL 1 Hz WLTC
class 3b trace (UN GTR 15 [21]) exported from the `wltp` Python package
(checksum-verified against the regulation; 1801 samples, 23.27 km).
Two consecutive cycles are used so that the 7.92 kWh pack can be depleted
by a meaningful amount within the trip (report Section 3.2).
"""
import os
import numpy as np
import config as cfg


def load_speed_profile():
    """Return the trip speed vector v [m/s] with N+1 = 3601 samples.

    The single cycle file has 1801 samples (t = 0..1800 s) and starts/ends
    at standstill.  Two cycles are concatenated by dropping the duplicated
    zero-speed sample at the seam, giving t = 0..3600 s.
    """
    fn = os.path.join(cfg.DATA_DIR, 'wltp_class3b_kmh.csv')
    v_kmh = np.loadtxt(fn)
    v_ms  = v_kmh / 3.6
    v = np.concatenate([v_ms[:-1]] * cfg.N_CYCLES + [v_ms[-1:]])
    return v


def load_power(v):
    """Compute the bus load trajectory P_load[k], k = 0..N-1 [W].

    Acceleration is evaluated by the forward difference
      a_k = (v_{k+1} - v_k) / dt,
    consistent with a zero-order-hold on the decision variable: the power
    demand of interval k is what moves the vehicle from v_k to v_{k+1}.
    """
    veh = cfg.VEH
    dt  = cfg.DT
    a   = np.diff(v) / dt                       # length N
    vk  = v[:-1]                                # speed at interval start
    # Eq. (3), level road (alpha = 0):
    F_inertia = veh['mass'] * a
    F_roll    = veh['mass'] * cfg.G_GRAV * veh['Cr'] * (vk > 0.1)
    F_aero    = 0.5 * veh['rho_air'] * veh['Cd'] * veh['Af'] * vk**2
    P_wheel   = (F_inertia + F_roll + F_aero) * vk
    # Eq. (4): direction-dependent drivetrain efficiency
    P_load = np.where(P_wheel >= 0.0,
                      P_wheel / veh['eta_dt'],
                      P_wheel * veh['eta_dt'])
    # Physical saturation at the motor rating
    P_load = np.clip(P_load, -veh['Pm_max'], veh['Pm_max'])
    return P_load


def trip():
    """Convenience wrapper: return (t, v, P_load, distance_km)."""
    v = load_speed_profile()
    P = load_power(v)
    t = np.arange(len(P)) * cfg.DT
    dist_km = np.sum(v[:-1]) * cfg.DT / 1000.0
    return t, v, P, dist_km


if __name__ == '__main__':
    t, v, P, d = trip()
    print(f"N = {len(P)} steps, distance = {d:.2f} km")
    print(f"P_load: max = {P.max()/1e3:.1f} kW, min = {P.min()/1e3:.1f} kW, "
          f"mean(+) = {P[P>0].mean()/1e3:.1f} kW")
    E_trac = P[P > 0].sum() * cfg.DT / 3.6e6
    E_reg  = -P[P < 0].sum() * cfg.DT / 3.6e6
    print(f"Traction energy = {E_trac:.2f} kWh, recoverable = {E_reg:.2f} kWh")
