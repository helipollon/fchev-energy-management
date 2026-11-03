# MAT 4902E — Graduation Project II: Plug-in FCHEV Energy Management Simulation

**Mathematical Modeling & Control Strategies for Hybrid Hydrogen Systems**
Ahmet Yeşil · Supervisor: Prof. Dr. Semra Ahmetolan · Istanbul Technical University, 2026

This folder holds the **results** of Graduation Project II: the tables and figures of the frozen
model **v9** (14 October 2026) and a guide to them. The simulation code is not published.
The report is in preparation.

---

## 1. What was simulated

A plug-in hydrogen fuel cell hybrid electric vehicle based on the second-generation Toyota Mirai.
Every second the energy management system chooses the power the fuel cell delivers to the DC bus,
`u = P_dc`; the battery supplies the rest, `P_bat = P_load − P_dc`. The trip cost is

```
J = Σ_k ( C_fc,k + C_bat,k )  +  c_sw · n_sw  +  γ (SoC_N − 0.25)²
```

* `C_fc`: hydrogen at 13 €/kg (Germany 2026; scenarios 8 and 20 €/kg);
* `C_bat`: grid-equivalent electricity at 0.37 €/kWh (the energy taken from the battery has to be
  recharged from the grid after the trip);
* `c_sw` = 0.13 € per fuel-cell start or stop (0.01 kg H2, Kofler, Jakubek, Hametner 2025);
* `γ` = 1000 €: terminal penalty; the battery starts at SoC 0.90 and should end at 0.25.

**Models.**

* *Vehicle:* Mirai II road-load (coast-down) coefficients and test mass, level road, a
  bus-to-wheel efficiency of 0.92 · 0.90 · 0.95 = 0.787; the 1 Hz speed trace is turned into the
  bus power `P_load` second by second.
* *Fuel cell:* Mann–Amphlett GSSEM of the FCB130 stack; eight semi-empirical coefficients
  identified by particle swarm optimisation against the measured stack efficiency of Alves et al.
  (2025) (cell-voltage RMSE 14.1 mV).
* *Battery:* two layers. The controllers plan on an Rint model; the results are measured on a
  1-RC + hysteresis LFP model (the *plant*). Every number in this folder comes from the plant.

**Strategies.**

| Strategy | Knows the future? | What it does |
|---|---|---|
| DP | yes, the whole trip | Dynamic programming over SoC and the on/off state; the benchmark |
| A-ECMS | no | Minimises a Hamiltonian every second; a PI law on the SoC error sets the equivalence factor |
| MPC | no | Optimises over a short horizon, assuming the present load persists |
| BLFS | no | Rule-based on/off supervisor wrapped around A-ECMS or MPC: decides when the fuel cell starts and stops |

---

## 2. Evaluation protocol

Nine trips, each long enough that the battery alone cannot finish it inside the SoC window.

| Role | Trips | Use |
|---|---|---|
| Training | `train_2xWLTC3b`, `train_3xWLTC3b` | The only trips the gains were tuned on |
| Development | `test_3xWLTC2`, `test_3xUS06`, `test_4xFTP75`, `test_mixed` (FTP-75 + 2×US06 + WLTC 2) | Guided the design of the SoC control, so they are not unseen |
| Held-out test | `hold_HWFET` (3×), `hold_WLTC1` (7×), `hold_mixed` (2×HWFET + 2×WLTC 1 + US06) | No design or tuning decision was taken on them |

The held-out trips were run a few times while the design was still changing (for example in a
hold-time experiment on 6 October 2026), but no setting was chosen on their results. They should
therefore be read as "not used for decisions" rather than "never seen".

Gain selection rule: on the tuning grid, the setting whose own result and the results of its
grid neighbours are best in the worst case; if the choice falls on the edge of the grid, the
grid is widened.

---

## 3. Main results

Total cost in € on the plant, difference to DP, and fuel-cell starts.

| Trip | DP (€) | A-ECMS + BLFS | MPC + BLFS | Starts without BLFS (A-ECMS / MPC) |
|---|---|---|---|---|
| `train_2xWLTC3b` | 4.025 | 4.076 (+1.3 %), 1 | 4.079 (+1.3 %), 1 | 37 / 85 |
| `train_3xWLTC3b` | 6.409 | 6.519 (+1.7 %), 1 | 6.525 (+1.8 %), 1 | 78 / 168 |
| `test_3xWLTC2` | 5.658 | 5.703 (+0.8 %), 1 | 5.711 (+0.9 %), 1 | 83 / 126 |
| `test_3xUS06` | 4.552 | 4.644 (+2.0 %), 1 | 4.650 (+2.1 %), 1 | 84 / 247 |
| `test_4xFTP75` | 4.972 | 5.249 (+5.6 %), 2 | 5.228 (+5.1 %), 2 | 310 / 392 |
| `test_mixed` | 6.365 | 6.516 (+2.4 %), 1 | 6.565 (+3.1 %), 1 | 136 / 263 |
| `hold_HWFET` | 3.885 | 3.906 (+0.5 %), 1 | 3.963 (+2.0 %), 1 | 77 / 160 |
| `hold_WLTC1` | 4.002 | 3.991 (−0.3 %), 1 | 3.991 (−0.3 %), 1 | 465 / 242 |
| `hold_mixed` | 5.503 | 5.872 (+6.7 %), 2 | 5.902 (+7.2 %), 2 | 107 / 204 |

* Without the supervisor A-ECMS and MPC are close to DP in energy cost but start the fuel cell
  37–465 times; the start/stop charges then dominate the total. With BLFS: 1–2 starts.
* With BLFS both strategies are between −0.3 % and +7.2 % of DP; with a single start at most +3.1 %.
  The two-start trips (`test_4xFTP75`, `hold_mixed`) are the weak cases.
* DP is optimal on the controller model; on the plant it can be beaten slightly (`hold_WLTC1`).
* Mean computation time per decision step: at most 0.17 ms (A-ECMS + BLFS) and 0.54 ms
  (MPC + BLFS) over the nine trips; the sampling interval is 1 s.

Frozen gains (tuned on the training trips): A-ECMS `k_p = 200`, `k_i = 0.001`;
BLFS start threshold `α = 1.1`, hold time 60 s; MPC terminal weight `γ_mpc = 300`, `β = 0`.

---

## 4. Result files

Costs are in €, powers in kW unless the column name says otherwise, SoC is a fraction (0–1).

### `results/evaluation/` — training / test evaluation

| File | Contents |
|---|---|
| `evaluation_summary_v9.csv` | **Main table:** 9 trips × 5 strategies (DP, A-ECMS, A-ECMS+BLFS, MPC, MPC+BLFS) |
| `eval2_distance_<trip>.csv` | The same rows, one file per trip (the main table is these nine files stacked) |

Columns: `cost_run` energy cost (hydrogen + electricity), `cost_sw` start/stop charges,
`term_penalty` terminal penalty, `cost_total` their sum; `gap_run_pct`, `gap_total_pct` difference to
DP in %; `m_h2_g` hydrogen used [g]; `soc_final`, `soc_min`; `fc_starts`; `cpu_ms` mean computation
time of one decision step; `dist_km`, `duration_s`; `u_below_me` seconds with the fuel cell on but
below its lowest operating point; `unmet_s` seconds in which the battery current limit left
part of the traction demand unmet.

### `results/tuning/` — tuning (training trips only)

| File | Contents |
|---|---|
| `tuning4_aecms.csv` | A-ECMS + BLFS grid: `k_p` (7) × `k_i` (10) × `α` (7) = 490 settings, both training trips |
| `tuning5_mpc.csv` | MPC + BLFS grid: `γ_mpc` (7) × `β` (4) = 28 settings |
| `tuned_settings4_distance.json`, `tuned_settings5_distance.json` | Selected settings with their mean and worst-neighbour gap |
| `dp_baseline4.json` | DP results of the training trips used as the reference during tuning |

### `results/default_scenario/` — default trip (2 × WLTC Class 3b)

| File | Contents |
|---|---|
| `results_default.csv` | Five strategies with the cost broken down (`cost_fc`, `cost_bat`, `eur_per_100km`, `m_h2_kg`, `e_bat_kWh`, …) |
| `results_low.csv`, `results_high.csv`, `results_all_scenarios.csv` | Hydrogen price scenarios 8 / 13 / 20 €/kg |
| `results_default_other_map.csv` | The same with the measured hydrogen map instead of the GSSEM map |
| `gamma_sweep.json` | DP for different terminal-penalty weights `γ` |
| `figures/fig01…fig09.png` | Load trajectory, polarization fit (PSO), efficiency map, OCV hysteresis, SoC trajectories, `P_dc` profiles, cost breakdown, price sensitivity, `γ` sweep |

### `results/sensitivity/` — sensitivity to the start/stop charge

| File | Contents |
|---|---|
| `switching_cost_sensitivity.csv` | Charge × 0.2 … 25 (`factor`, `p_kg` kg H2 per action): DP and A-ECMS + BLFS |
| `tradeoff_dp.csv`, `fig_tradeoff.png` | DP trade-off between energy cost and number of starts (charge × 0 … 1) |

### `results/robustness/` — robustness of the supervisor

| File | Contents |
|---|---|
| `robustness_scenarios.csv` | Scenarios R0 nominal, R1/R2 trip 30 % longer/shorter than planned, R3/R4 gains ÷ 10 / ÷ 100, R5 no upper-level command; with and without BLFS (`*_blfs` columns); `band_s`, `mp_s`, `ramp_s` seconds BLFS spent in each mode |
| `blfs_nominal.csv` | When and how often BLFS intervenes on the nominal trips |

### `results/demo/` — second-by-second traces

`traces_train_2xWLTC3b.csv`, `traces_test_3xUS06.csv`: time, speed, `P_load`, and `P_dc` and
SoC of DP, A-ECMS+BLFS, MPC+BLFS and A-ECMS for every second of the trip.

### `results/note_figures/` — figures of the study notes (axis labels and titles in Turkish)

`n1_trip` load of the training trip, `n2_dp_policy` DP decision map, `n3_hamiltonian` A-ECMS
Hamiltonian, `n4_soc` SoC trajectories, `n5_pdc` fuel-cell power, `n6_s` equivalence factor,
`n7_supervisor_effect` effect of the supervisor, `n8_blfs_r5` BLFS without an upper-level command,
`n9_final_approach` last 150 s of a trip, braking to standstill and the approach to the target SoC; `numbers.json` the numbers quoted in the notes.

---

## 5. Limitations

* Level road, constant vehicle mass (test mass).
* Five of the eight identified stack coefficients lie close to the bounds of the PSO search box.
* The held-out trips are "not used for decisions" rather than strictly unseen (Section 2).
* Results depend on the prices; the scenarios vary only the hydrogen price.

Bibliography: [`docs/REFERENCES.md`](docs/REFERENCES.md) (July 2026 list; the final list will be in
the report).
