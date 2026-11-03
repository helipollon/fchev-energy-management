# Energy Management for Plug-in Fuel Cell Hybrid Electric Vehicles (FCHEV)

**Mathematical modelling, optimal control formulation and numerical solution**

Istanbul Technical University — Department of Mathematical Engineering
Graduation Project I (MAT 4901E) and Graduation Project II (MAT 4902E), 2026

**Author:** Ahmet Yeşil

**Status:** Project I (formulation) is complete. Project II: the simulation environment and
the four strategies are implemented and evaluated; the model is frozen as **v9** (14 October 2026)
and the report is in preparation.

**Contents of this repository:** reports, presentation, results (tables and figures) and the
documentation that explains them. The simulation code is not published here.

---

## Overview

The power split between the fuel cell and the battery of a plug-in hydrogen fuel cell
hybrid electric vehicle (an FCHEV based on the second-generation Toyota Mirai) is posed
as an **optimal control problem** and solved numerically. The decision variable is the
power the DC/DC converter delivers to the bus, `u_k = P_dc,k`; the battery covers the rest,
`P_bat = P_load − P_dc`. The state is the battery state of charge `SoC` and whether the fuel
cell is on or off. The objective is the total monetary cost of a trip — hydrogen,
grid-equivalent electricity, a charge per fuel-cell start or stop, and a terminal SoC penalty:

```
min  Σ_k ( C_fc,k + C_bat,k )  +  c_sw · n_sw  +  γ (SoC_N − 0.25)²
```

`c_sw` = 0.01 kg H2 per start or stop (Kofler, Jakubek, Hametner 2025), i.e. 0.13 € at 13 €/kg;
`γ` = 1000 €. The real-time energy management system is two-layered: a **BLFS on/off supervisor**
decides when the fuel cell runs, and **A-ECMS** (or MPC) decides its power while it is on.
**Dynamic programming** solves the same problem with the whole trip known in advance and serves
as the benchmark.

| Stage | Contents |
|---|---|
| **[`project1-formulation/`](project1-formulation/)** — MAT 4901E | Literature review, mathematical derivation of the vehicle, fuel cell and battery models, formulation of the optimal control problem, and selection of the solution strategies. Report + defence presentation. |
| **[`project2-simulation/`](project2-simulation/)** — MAT 4902E | Results of the numerical solution: two-layer simulation (controllers plan on an Rint battery model, results are measured on a 1-RC + hysteresis plant), stack coefficients identified by particle swarm optimisation, DP benchmark, A-ECMS, MPC and the BLFS supervisor, evaluated on nine trips. The folder README explains every result file. |

---

## Main results (model v9)

Total trip cost in € (energy + start/stop charges + terminal penalty) as measured on the plant,
the difference to the DP benchmark, and the number of fuel-cell starts. Initial SoC 0.90, target
0.25; hydrogen 13 €/kg, electricity 0.37 €/kWh. The gains were tuned on the two training trips
only; the development trips guided the design; no setting was chosen on the held-out trips
(they were seen during the design, so they are not strictly unseen; see the
[Project II README](project2-simulation/README.md#2-evaluation-protocol)).

| Trip | Role | km | DP (€) | A-ECMS + BLFS: € (vs DP), starts | MPC + BLFS: € (vs DP), starts | Starts without BLFS (A-ECMS / MPC) |
|---|---|---|---|---|---|---|
| `train_2xWLTC3b` | training | 46.5 | 4.025 | 4.076 (+1.3 %), 1 | 4.079 (+1.3 %), 1 | 37 / 85 |
| `train_3xWLTC3b` | training | 69.8 | 6.409 | 6.519 (+1.7 %), 1 | 6.525 (+1.8 %), 1 | 78 / 168 |
| `test_3xWLTC2` | development | 67.9 | 5.658 | 5.703 (+0.8 %), 1 | 5.711 (+0.9 %), 1 | 83 / 126 |
| `test_3xUS06` | development | 38.7 | 4.552 | 4.644 (+2.0 %), 1 | 4.650 (+2.1 %), 1 | 84 / 247 |
| `test_4xFTP75` | development | 71.1 | 4.972 | 5.249 (+5.6 %), 2 | 5.228 (+5.1 %), 2 | 310 / 392 |
| `test_mixed` | development | 66.2 | 6.365 | 6.516 (+2.4 %), 1 | 6.565 (+3.1 %), 1 | 136 / 263 |
| `hold_HWFET` | held-out test | 49.5 | 3.885 | 3.906 (+0.5 %), 1 | 3.963 (+2.0 %), 1 | 77 / 160 |
| `hold_WLTC1` | held-out test | 80.0 | 4.002 | 3.991 (−0.3 %), 1 | 3.991 (−0.3 %), 1 | 465 / 242 |
| `hold_mixed` | held-out test | 68.8 | 5.503 | 5.872 (+6.7 %), 2 | 5.902 (+7.2 %), 2 | 107 / 204 |

* The BLFS supervisor reduces the number of fuel-cell starts from 37–465 to 1–2.
* With BLFS both real-time strategies stay between −0.3 % and +7.2 % of the DP benchmark;
  on trips with a single start the difference is at most +3.1 %.
* DP is optimal on the controller model (Rint battery, discrete grid); measured on the more
  detailed plant it can be beaten slightly, as on `hold_WLTC1`.
* The mean computation time of one decision step is at most 0.17 ms (A-ECMS + BLFS) and
  0.54 ms (MPC + BLFS) over the nine trips, at a sampling interval of 1 s.

Source: [`project2-simulation/results/evaluation/evaluation_summary_v9.csv`](project2-simulation/results/evaluation/evaluation_summary_v9.csv).

---

## Repository layout

```
.
├── project1-formulation/            MAT 4901E — modelling and formulation
│   ├── report/                      submitted report
│   ├── presentation/                defence presentation (PDF)
│   ├── figures/                     WLTP profile, OCV–SoC flat-zone figures
│   └── references/                  list of the literature used (PDFs not redistributed)
│
└── project2-simulation/             MAT 4902E — results of the numerical solution
    ├── results/                     tables (csv/json) and figures of model v9
    ├── docs/                        bibliography
    └── README.md                    guide to the result files
```

---

## Methods

* **Fuel cell:** Mann–Amphlett generalised steady-state electrochemical model (GSSEM) of the
  Mirai II stack; its eight semi-empirical coefficients are identified by particle swarm
  optimisation against the measured stack efficiency of Alves et al. (2025).
* **Battery:** 1-RC equivalent circuit with OCV hysteresis (LFP) as the plant; an Rint model
  inside the controllers.
* **Drive cycles:** WLTC Class 3b (training), WLTC Class 2 and 1 (UN Regulation No. 154),
  US06, FTP-75 and HWFET (US EPA), all at 1 Hz.
* **Energy management:** Dynamic Programming (offline benchmark), Adaptive ECMS and Model
  Predictive Control (real-time), and the BLFS rule-based on/off supervisor wrapped around
  either of them.

## Licence

The text, figures and analysis in the reports, results and documentation are the author's
academic work and may be used with attribution (see also [LICENSE](LICENSE)). Third-party
publications under `project1-formulation/references/` are copyrighted and are therefore
**not** included in this repository.

## Citation

```bibtex
@mastersthesis{yesil2026fchev,
  author = {Ye{\c{s}}il, Ahmet},
  title  = {Mathematical Modeling and Control Strategies for Hybrid Hydrogen Systems},
  school = {Istanbul Technical University, Department of Mathematical Engineering},
  year   = {2026},
  note   = {Graduation Project I--II (MAT 4901E / MAT 4902E)}
}
```
