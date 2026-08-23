"""
param_id.py — PSO identification of the GSSEM stack coefficients for the
Mirai II, following the methodology of Fang et al. [7] as announced in
Section 3.3.2 / 3.7 of the MAT4901E report.

Decision vector (8 parameters, bounds from the ranges surveyed in [7]):
    theta = [xi1, xi2, xi3, xi4, lam_w, R_C, beta_con, J_max]

Objective: root-mean-square error between the GSSEM cell voltage and the
measured polarization data over all data points,
    F(theta) = sqrt( mean_j ( V_model(J_j; theta) - V_data_j )^2 )

Why PSO (and not gradient methods)?
  * The objective is non-convex: xi3 multiplies ln(C_O2) which interacts
    with xi1 (pure offset), producing long correlated valleys; lam_w and
    R_C are nearly redundant at low J.  Gradient descent stalls in these
    valleys; a population method explores them cheaply.
  * The model is cheap (algebraic) -> thousands of evaluations are free.
  * PSO is the reference method in the FC identification literature [7]
    and needs no derivative bookkeeping.

Implementation: canonical global-best PSO (Clerc constriction values
w = 0.7298, c1 = c2 = 1.4962), 40 particles, 150 iterations, velocity
clamped to 20% of the box width, positions reflected at the bounds.
Seeded RNG => fully reproducible.

Result is cached to data/identified_stack_params.json.
"""
import os
import json
import numpy as np
import config as cfg
from fuel_cell import GSSEM

# parameter bounds (rows: [low, high]) — ranges from Fang et al. [7]
BOUNDS = {
    'xi1'      : (-1.20,   -0.80),
    'xi2'      : ( 1.0e-3,  5.0e-3),
    'xi3'      : ( 3.6e-5,  9.8e-5),
    'xi4'      : (-2.6e-4, -0.9e-4),
    'lam_w'    : (10.0,     24.0),
    'R_C'      : ( 1.0e-5,  8.0e-4),
    'beta_con' : ( 0.01,    0.20),
    'J_max'    : ( 2.35,    3.00),
}
KEYS = GSSEM.ID_KEYS
LO = np.array([BOUNDS[k][0] for k in KEYS])
HI = np.array([BOUNDS[k][1] for k in KEYS])


def load_data():
    fn = os.path.join(cfg.DATA_DIR, 'mirai_polarization.csv')
    if not os.path.exists(fn):
        import make_polarization_data
        make_polarization_data.main()
    d = np.loadtxt(fn, delimiter=',')
    return d[:, 0], d[:, 1]


def rmse(theta, J, V_meas):
    """Objective: polarization-curve RMSE [V] for one particle."""
    fc = GSSEM(dict(zip(KEYS, theta)))
    # guard: model must remain physical (positive voltage everywhere)
    V = fc.cell_voltage(J)
    if np.any(~np.isfinite(V)) or np.any(V <= 0.0):
        return 1e3
    return float(np.sqrt(np.mean((V - V_meas) ** 2)))


def pso(J, V_meas, n_particles=40, n_iter=150, seed=7):
    rng = np.random.default_rng(seed)
    dim = len(KEYS)
    w, c1, c2 = 0.7298, 1.4962, 1.4962
    v_max = 0.20 * (HI - LO)

    x = LO + rng.random((n_particles, dim)) * (HI - LO)
    v = rng.uniform(-1, 1, (n_particles, dim)) * v_max * 0.1
    f = np.array([rmse(xi, J, V_meas) for xi in x])
    pbest_x, pbest_f = x.copy(), f.copy()
    g = int(np.argmin(f))
    gbest_x, gbest_f = x[g].copy(), f[g]
    hist = [gbest_f]

    for it in range(n_iter):
        r1 = rng.random((n_particles, dim))
        r2 = rng.random((n_particles, dim))
        v = (w * v + c1 * r1 * (pbest_x - x) + c2 * r2 * (gbest_x - x))
        v = np.clip(v, -v_max, v_max)
        x = x + v
        # reflect at bounds (keeps particles inside the physical box)
        over, under = x > HI, x < LO
        x = np.where(over, 2 * HI - x, x)
        x = np.where(under, 2 * LO - x, x)
        x = np.clip(x, LO, HI)

        f = np.array([rmse(xi, J, V_meas) for xi in x])
        better = f < pbest_f
        pbest_x[better], pbest_f[better] = x[better], f[better]
        g = int(np.argmin(pbest_f))
        if pbest_f[g] < gbest_f:
            gbest_x, gbest_f = pbest_x[g].copy(), pbest_f[g]
        hist.append(gbest_f)
    return gbest_x, gbest_f, np.array(hist)


def identify(force=False):
    """Run (or load cached) identification. Returns the parameter dict."""
    fn = os.path.join(cfg.DATA_DIR, 'identified_stack_params.json')
    if os.path.exists(fn) and not force:
        with open(fn) as fh:
            return json.load(fh)
    J, V = load_data()
    theta, f_best, hist = pso(J, V)
    params = dict(zip(KEYS, [float(t) for t in theta]))
    params['rmse_V'] = f_best
    params['pso_history'] = hist.tolist()
    with open(fn, 'w') as fh:
        json.dump(params, fh, indent=2)
    print(f"PSO done: RMSE = {f_best*1e3:.2f} mV")
    for k in KEYS:
        print(f"  {k:9s} = {params[k]:.5g}")
    return params


if __name__ == '__main__':
    p = identify(force=True)
    fc = GSSEM({k: p[k] for k in KEYS})
    lut = fc.build_lut()
    print(f"identified stack: P_peak = {lut['P_peak']/1e3:.1f} kW")
    for Pk in [12e3, 60e3, 128e3]:
        eta = np.interp(Pk, lut['P_gross'], lut['eta'])
        print(f"  P = {Pk/1e3:6.1f} kW -> eta_LHV = {eta:.3f}")
