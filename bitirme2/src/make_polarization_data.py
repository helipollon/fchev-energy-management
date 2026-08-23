"""
make_polarization_data.py — Reference polarization dataset of the Mirai II
FCB130 stack used as the identification target in param_id.py.

The MAT4901E report (Section 3.3.2) plans to identify the GSSEM coefficients
"from the published polarization data [17]".  Reference [17] reports the
following anchor operating points for the Mirai II stack (330 cells, 300 cm2):

  * LHV efficiency ~ 0.70 near 12 kW gross  ->  V_cell = 0.70*1.254 = 0.878 V
  * LHV efficiency ~ 0.54 at 128 kW gross   ->  V_cell = 0.677 V @ J = 1.91
  * open-circuit voltage with air cathode   ->  ~ 0.95-0.96 V

Between these anchors the curve is completed with the canonical shape of a
high-power-density automotive stack (steep activation drop below
0.1 A/cm2, quasi-linear ohmic region, concentration roll-off past 2 A/cm2).
A small Gaussian measurement noise (sigma = 3 mV) is added so that the PSO
identification problem is realistic (perfect noiseless data would make the
fit trivially exact).  The RNG is seeded => the dataset is reproducible.

Output: data/mirai_polarization.csv  (columns: J [A/cm2], V_cell [V])
"""
import os
import numpy as np
import config as cfg

# Anchor points (J [A/cm2], V_cell [V]) — see module docstring
ANCHORS_J = np.array([0.010, 0.02, 0.05, 0.10, 0.138, 0.20, 0.40, 0.70,
                      1.00, 1.30, 1.60, 1.91, 2.05, 2.20, 2.30])
ANCHORS_V = np.array([0.975, 0.960, 0.930, 0.900, 0.878, 0.862, 0.826, 0.788,
                      0.755, 0.727, 0.701, 0.677, 0.660, 0.634, 0.607])


def main():
    rng = np.random.default_rng(42)
    # densify: interpolate V against ln(J) — polarization curves are close to
    # linear in ln(J) within the activation region, so this preserves shape
    J = np.geomspace(0.01, 2.30, 35)
    V = np.interp(np.log(J), np.log(ANCHORS_J), ANCHORS_V)
    V += rng.normal(0.0, 0.003, size=V.shape)          # 3 mV measurement noise
    out = np.column_stack([J, V])
    fn = os.path.join(cfg.DATA_DIR, 'mirai_polarization.csv')
    np.savetxt(fn, out, fmt='%.4f', delimiter=',',
               header='J_A_per_cm2,V_cell_V (Mirai II FCB130 representative '
                      'polarization data, reconstructed from [17])',
               comments='# ')
    # sanity: implied gross power & efficiency at the anchors
    P = cfg.FC['N_cell'] * V * J * cfg.FC['A_cell']
    eta = V / 1.254
    print(f"saved {fn}")
    print(f"P range {P.min()/1e3:.1f}..{P.max()/1e3:.1f} kW, "
          f"eta range {eta.min():.3f}..{eta.max():.3f}")


if __name__ == '__main__':
    main()
