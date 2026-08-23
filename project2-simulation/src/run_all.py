"""
run_all.py — Master script: reproduces EVERY result of the study.

    python3 run_all.py            # full pipeline, ~2 min

Pipeline:
  1. build / load the WLTP trip and the load trajectory
  2. PSO identification of the stack coefficients (cached in data/)
  3. closed-loop simulation of the 5 controllers under the default
     price scenario  -> results/results_default.csv + figures
  4. price-scenario sensitivity (high / default / low)  -> results/
  5. terminal-penalty-weight (gamma) sweep on the DP benchmark
  6. all figures  -> results/figures/*.png

Every figure is regenerated from scratch; nothing is hand-drawn, so the
documentation can never drift away from the code.
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import config as cfg
import drive_cycle
import param_id
import cost_model as cmod
import battery as bat
from fuel_cell import GSSEM
from cost_model import CostModel, soc_reference
from ems.dp import DPController
from ems.aecms import AECMSController
from ems.mpc import MPCController
from ems.blfs import BLFSWrapper
import simulate

plt.rcParams.update({'figure.dpi': 130, 'font.size': 9,
                     'axes.grid': True, 'grid.alpha': 0.3})


def make_controllers(cm, P):
    """Fresh controller instances (they are stateful!)."""
    return [
        ('DP',          DPController(cm, P).solve()),
        ('A-ECMS',      AECMSController(cm)),
        ('A-ECMS+BLFS', BLFSWrapper(AECMSController(cm), cm)),
        ('MPC',         MPCController(cm)),
        ('MPC+BLFS',    BLFSWrapper(MPCController(cm), cm)),
    ]


def run_scenario(scenario, lut, P, dist_km):
    cm = CostModel(lut, scenario)
    out = []
    for name, ctrl in make_controllers(cm, P):
        r = simulate.run(ctrl, cm, P, name)
        r['eur_per_100km'] = r['cost_run'] / dist_km * 100.0
        r['scenario'] = scenario
        out.append(r)
        print(f"  [{scenario}] {name:12s} total={r['cost_total']:.3f} EUR "
              f"({r['eur_per_100km']:.2f} EUR/100km run) SoC_f={r['soc_final']:.3f}")
    return out


def save_table(results, fn):
    cols = ['label', 'scenario', 'cost_total', 'cost_run', 'cost_fc',
            'cost_bat', 'term_penalty', 'eur_per_100km', 'm_h2_kg',
            'e_bat_kWh', 'soc_final', 'soc_err', 'fc_ramp_mean',
            'fc_onoff', 'cpu_ms']
    with open(fn, 'w') as f:
        f.write(','.join(cols) + '\n')
        for r in results:
            f.write(','.join(f"{r[c]:.6g}" if isinstance(r[c], float)
                             else str(r[c]) for c in cols) + '\n')
    print(f"table -> {fn}")


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------
def fig_cycle(t, v, P):
    fig, ax = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    ax[0].plot(t, v[:-1] * 3.6, lw=0.8, color='tab:blue')
    ax[0].set_ylabel('v [km/h]')
    ax[0].set_title('2 x WLTC Class 3b (official UN GTR 15 trace), 46.5 km / 3600 s')
    ax[1].plot(t, P / 1e3, lw=0.6, color='tab:red')
    ax[1].set_ylabel('P_load [kW]'); ax[1].set_xlabel('t [s]')
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig01_cycle_load.png')); plt.close(fig)


def fig_polarization(params):
    J_d, V_d = param_id.load_data()
    fc_id = GSSEM({k: params[k] for k in GSSEM.ID_KEYS})
    fc_0  = GSSEM()
    J = np.linspace(0.01, params['J_max'] * 0.98, 300)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
    ax[0].plot(J_d, V_d, 'ko', ms=4, label='Mirai II data [17]')
    ax[0].plot(J, fc_id.cell_voltage(J), 'r-', label='GSSEM (PSO-identified)')
    ax[0].plot(J, fc_0.cell_voltage(np.clip(J, 0, cfg.FC['J_max']*.99)), 'b--',
               lw=1, label='GSSEM (Mann nominal)')
    ax[0].set_xlabel('J [A/cm$^2$]'); ax[0].set_ylabel('V_cell [V]')
    ax[0].set_ylim(0.4, 1.05); ax[0].legend(fontsize=7)
    ax[0].set_title(f"Polarization fit, RMSE = {params['rmse_V']*1e3:.1f} mV")
    h = params['pso_history']
    ax[1].semilogy(h, 'g-')
    ax[1].set_xlabel('PSO iteration'); ax[1].set_ylabel('best RMSE [V]')
    ax[1].set_title('PSO convergence')
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig02_polarization_pso.png')); plt.close(fig)


def fig_efficiency(lut, cm):
    Pg = lut['P_gross']
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(Pg / 1e3, lut['eta'], 'r-', label='stack LHV efficiency')
    u = np.linspace(1e3, cm.P_dc_max, 300)
    eta_sys = u / (cm.mdot(u) * cfg.LHV_H2)
    ax.plot(cm.p_gross(u) / 1e3, eta_sys, 'b-', label='tank-to-bus (incl. aux + DC/DC)')
    k = int(np.argmax(eta_sys))
    ax.plot(cm.p_gross(u[k]) / 1e3, eta_sys[k], 'b*', ms=12,
            label=f'system peak: {eta_sys[k]:.2f} @ {u[k]/1e3:.0f} kW bus')
    ax.set_xlabel('P_gross [kW]'); ax.set_ylabel('efficiency [-]')
    ax.legend(fontsize=8); ax.set_title('Efficiency maps of Eq. (11)')
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig03_efficiency_map.png')); plt.close(fig)


def fig_ocv():
    s = np.linspace(0, 1, 300)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(s * 100, bat.ocv_cell(s, 'chg'), 'g-', label='charge branch')
    ax.plot(s * 100, bat.ocv_cell(s, 'dis'), 'r-', label='discharge branch')
    ax.fill_between(s * 100, bat.ocv_cell(s, 'dis'), bat.ocv_cell(s, 'chg'),
                    alpha=0.2, color='orange', label='hysteresis')
    ax.axvspan(20, 95, alpha=0.08, color='blue')
    ax.text(55, 2.95, 'operating window', color='blue', ha='center', fontsize=8)
    ax.set_xlabel('SoC [%]'); ax.set_ylabel('OCV per cell [V]')
    ax.set_title('LFP OCV, 8th-order polynomial branches [11],[12]')
    ax.legend(fontsize=8); ax.set_ylim(2.8, 3.55)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig04_ocv_hysteresis.png')); plt.close(fig)


def fig_soc(results, t):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ref = soc_reference(np.arange(len(t) + 1) * cfg.DT)
    ax.plot(np.arange(len(ref)), 100 * np.asarray(ref), 'k--', lw=1,
            label='reference (energy-based)')
    for r in results:
        ax.plot(100 * r['soc'], lw=1, label=r['label'])
    ax.axhline(100 * cfg.BAT['SoC_target'], color='gray', lw=0.5)
    ax.text(50, 100 * cfg.BAT['SoC_target'] + 0.6, 'target 25%',
            color='gray', fontsize=7)
    ax.set_xlabel('t [s]'); ax.set_ylabel('SoC [%]')
    ax.set_title('Charge-depleting SoC trajectories (plant model)')
    ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig05_soc_trajectories.png')); plt.close(fig)


def fig_pdc(results, P):
    fig, ax = plt.subplots(len(results), 1, figsize=(9, 9), sharex=True)
    for a, r in zip(ax, results):
        a.plot(P / 1e3, lw=0.4, color='0.8', label='P_load')
        a.plot(r['u'] / 1e3, lw=0.7, color='tab:red', label='P_dc (FC)')
        a.set_ylabel('kW'); a.set_title(r['label'], fontsize=8, loc='left')
    ax[0].legend(fontsize=7); ax[-1].set_xlabel('t [s]')
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig06_pdc_profiles.png')); plt.close(fig)


def fig_cost_breakdown(results):
    labels = [r['label'] for r in results]
    h2  = np.array([r['cost_fc'] for r in results])
    ele = np.array([r['cost_bat'] for r in results])
    pen = np.array([r['term_penalty'] for r in results])
    x = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.bar(x, h2, 0.6, label='hydrogen, Eq. (19)', color='tab:red')
    ax.bar(x, ele, 0.6, bottom=h2, label='grid electricity, Eq. (21)', color='tab:blue')
    ax.bar(x, pen, 0.6, bottom=h2 + ele, label='terminal penalty, Eq. (23)', color='tab:orange')
    for i, r in enumerate(results):
        ax.text(i, r['cost_total'] + 0.03, f"{r['cost_total']:.2f}", ha='center', fontsize=8)
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel('EUR / trip (46.5 km)')
    ax.set_title('Total cost decomposition, default scenario (11 EUR/kg, 0.35 EUR/kWh)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig07_cost_breakdown.png')); plt.close(fig)


def fig_sensitivity(all_results):
    scens = list(cfg.PRICES.keys())
    labels = [r['label'] for r in all_results[scens[0]]]
    x = np.arange(len(labels)); w = 0.25
    fig, ax = plt.subplots(figsize=(8, 3.8))
    for i, sc in enumerate(scens):
        tot = [r['cost_total'] for r in all_results[sc]]
        ax.bar(x + (i - 1) * w, tot, w,
               label=f"{sc}: {cfg.PRICES[sc]['M_H2']} EUR/kg, "
                     f"{cfg.PRICES[sc]['M_ele']} EUR/kWh")
    ax.set_xticks(x, labels, fontsize=8)
    ax.set_ylabel('total cost [EUR/trip]')
    ax.set_title('Price-scenario sensitivity (Table 3 of the report)')
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig08_sensitivity.png')); plt.close(fig)


def fig_gamma(gammas, res):
    fig, ax1 = plt.subplots(figsize=(6, 3.6))
    ax2 = ax1.twinx()
    ax1.semilogx(gammas, [r['soc_final'] for r in res], 'bo-', label='terminal SoC')
    ax1.axhline(cfg.BAT['SoC_target'], color='b', ls=':', lw=0.8)
    ax2.semilogx(gammas, [r['cost_run'] for r in res], 'rs--', label='running cost')
    ax1.set_xlabel(r'$\gamma$ [EUR]'); ax1.set_ylabel('terminal SoC', color='b')
    ax2.set_ylabel('running cost [EUR]', color='r'); ax2.grid(False)
    ax1.set_title(r'DP sensitivity to the terminal penalty weight $\gamma$')
    fig.tight_layout()
    fig.savefig(os.path.join(cfg.FIG_DIR, 'fig09_gamma_sweep.png')); plt.close(fig)


# ---------------------------------------------------------------------------
def main():
    print('=== 1. trip & load ===')
    t, v, P, dist_km = drive_cycle.trip()
    cmod.set_reference(P)
    fig_cycle(t, v, P)

    print('=== 2. stack identification (PSO) ===')
    params = param_id.identify()
    fc = GSSEM({k: params[k] for k in GSSEM.ID_KEYS})
    lut = fc.build_lut()
    fig_polarization(params)
    fig_ocv()

    print('=== 3. default scenario ===')
    cm_def = CostModel(lut, 'default')
    fig_efficiency(lut, cm_def)
    res_def = run_scenario('default', lut, P, dist_km)
    save_table(res_def, os.path.join(cfg.RES_DIR, 'results_default.csv'))
    fig_soc(res_def, t)
    fig_pdc(res_def, P)
    fig_cost_breakdown(res_def)

    print('=== 4. price sensitivity ===')
    all_res = {'default': res_def}
    for sc in ('high', 'low'):
        all_res[sc] = run_scenario(sc, lut, P, dist_km)
    save_table([r for sc in all_res for r in all_res[sc]],
               os.path.join(cfg.RES_DIR, 'results_all_scenarios.csv'))
    fig_sensitivity(all_res)

    print('=== 5. gamma sweep (DP) ===')
    gammas = [100.0, 300.0, 1000.0, 3000.0, 10000.0]
    gres = []
    for g in gammas:
        dp = DPController(cm_def, P, gamma=g).solve()
        r = simulate.run(dp, cm_def, P, f'DP g={g:g}')
        gres.append(r)
        print(f"  gamma={g:7g}: SoC_f={r['soc_final']:.4f} run={r['cost_run']:.3f}")
    fig_gamma(gammas, gres)
    with open(os.path.join(cfg.RES_DIR, 'gamma_sweep.json'), 'w') as f:
        json.dump([{k: r[k] for k in ('label', 'soc_final', 'cost_run',
                                      'cost_total')} for r in gres], f, indent=2)

    print('=== done: results/ and results/figures/ populated ===')


if __name__ == '__main__':
    main()
