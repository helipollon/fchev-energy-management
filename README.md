# Energy Management for Plug-in Fuel Cell Hybrid Electric Vehicles (FCHEV)

**Mathematical modelling, optimal control formulation and numerical solution**

Istanbul Technical University — Department of Mathematical Engineering
Graduation Project I (MAT 4901E) and Graduation Project II (MAT 4902E), 2026

**Author:** Ahmet Yeşil 

**Status:** Project I (formulation) is complete. Project II is in progress — the
simulation environment and the four strategies are being implemented; results will be
added as they are produced.

---

## Overview

The power split between the fuel cell and the battery of a plug-in hydrogen fuel cell
hybrid electric vehicle (an FCHEV based on the second-generation Toyota Mirai) is posed
as an **optimal control problem** and solved numerically. The single decision variable is
the power the DC/DC converter delivers to the bus, `u(t) = P_dc(t)`; the single state is
the battery state of charge, `SoC`. The objective is to minimise the total monetary cost
of a reference trip — hydrogen, grid-equivalent electricity and a terminal SoC penalty:

```
min  Σ L_k(SoC_k, P_dc,k) + γ (SoC_N − 0.25)²      L_k = C_fuel-cell,k + C_battery,k
```

The repository covers both stages of the project:

| Stage | Contents |
|---|---|
| **[`project1-formulation/`](project1-formulation/)** — MAT 4901E | Literature review, mathematical derivation of the vehicle, fuel cell and battery models, formulation of the optimal control problem, and selection of the solution strategies. Report + defence presentation. |
| **[`project2-simulation/`](project2-simulation/)** — MAT 4902E *(in progress)* | Numerical solution in Python: a two-layer simulation environment, identification of the stack coefficients by particle swarm optimisation, and implementation of four energy management strategies (DP, A-ECMS, MPC, BLFS). Code under active development; see [`project2-simulation/README.md`](project2-simulation/README.md) for current status — results are not yet final. |

---

## Quick start

```bash
git clone https://github.com/<username>/fchev-energy-management.git
cd fchev-energy-management/project2-simulation
pip install -r requirements.txt      # numpy + matplotlib
cd src
python3 run_all.py                   # generates the current results and figures (~2 min)
```

Both stochastic steps (measurement noise in the polarization data and the PSO swarm
initialisation) use fixed seeds (`seed=42`, `seed=7`), so two runs are bit-for-bit identical.

---

## Repository layout

```
.
├── project1-formulation/            MAT 4901E — modelling and formulation
│   ├── report/                      submitted report (+ drafts/)
│   ├── presentation/                defence talk (Beamer .tex + .pptx)
│   ├── figures/                     WLTP profile, OCV–SoC flat-zone figures
│   └── references/                  list of the literature used (PDFs not redistributed)
│
└── project2-simulation/             MAT 4902E — numerical solution
    ├── src/                         simulation and EMS code
    │   └── ems/                     dp.py · aecms.py · mpc.py · blfs.py
    ├── data/                        WLTC speed trace, polarization data, PSO output
    ├── results/                     csv/json results + figures/fig01…fig09.png
    ├── docs/                        bibliography, report generator
    └── README.md                    module-by-module code documentation
```

---

## Methods

* **Fuel cell:** Mann–Amphlett generalised steady-state electrochemical model (GSSEM);
  the coefficients are identified against polarization data by particle swarm optimisation.
* **Battery:** 1-RC equivalent circuit with OCV hysteresis (LFP), plus an Rint model.
* **Drive cycle:** UN GTR No. 15 WLTC Class 3b (official 1 Hz speed trace).
* **Energy management:** Dynamic Programming (offline global benchmark), Adaptive ECMS,
  Model Predictive Control, and Boundary Layer Surface Following (protection layer).

## Licence

The code is released under the [MIT Licence](LICENSE). The text, figures and analysis in
the reports and documentation are the author's academic work and may be used with
attribution. Third-party publications under `project1-formulation/references/` are
copyrighted and are therefore **not** included in this repository.

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
