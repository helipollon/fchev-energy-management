# MAT 4902E — Graduation Project II: Plug-in FCHEV Energy Management Simulation

**Author:** Ahmet Yeşil · **Supervisor:** Prof. Dr. Semra Ahmetolan
**Previous stage:** the MAT 4901E report (`../project1-formulation/report/MAT4901E_Report.pdf`) — mathematical formulation of the problem

This directory contains the **numerical solution** of the optimal control problem
formulated in Graduation Project I (MAT 4901E): the implementation and comparison of
four energy management strategies (DP, A-ECMS, MPC, BLFS) for a plug-in hydrogen fuel
cell hybrid electric vehicle (FCHEV, based on the second-generation Toyota Mirai) inside
a two-layer Python simulation environment.

**Status: in progress.** The four work packages announced in Section 3.7 of the report
are currently being implemented; none is finalised yet, and no comparative results are
published in this document until they have been produced and checked. The description
below documents the code and design decisions as they currently stand.

1. A two-layer simulation environment (high-fidelity plant + simplified controller model)
2. Metaheuristic identification of the stack coefficients by PSO and generation of the efficiency map
3. Implementation of the four strategies: DP benchmark, A-ECMS, MPC, BLFS protection layer
4. Comparison over the reference trip + price-scenario and γ penalty-weight sensitivity analysis

---

## Contents

1. [Quick start](#1-quick-start)
2. [Directory layout](#2-directory-layout)
3. [Problem summary and architectural decisions](#3-problem-summary-and-architectural-decisions)
4. [Module-by-module code documentation](#4-module-by-module-code-documentation)
5. [Deviations from the report formulation and their justification](#5-deviations-from-the-report-formulation-and-their-justification)
6. [Results](#6-results)
7. [Tuning process](#7-tuning-process)
8. [Verification and sanity checks](#8-verification-and-sanity-checks)
9. [Limitations and future work](#9-limitations-and-future-work)
10. [References](#10-references)

---

## 1. Quick start

```bash
cd project2-simulation
pip install -r requirements.txt     # numpy + matplotlib is all that is needed
cd src
python3 run_all.py                  # generates the current results (~2 min)
```

When `run_all.py` finishes:

* `results/results_default.csv` — comparison of the 5 strategies in the default price scenario
* `results/results_all_scenarios.csv` — 3 price scenarios × 5 strategies
* `results/gamma_sweep.json` — sweep of the γ penalty weight (DP)
* `results/figures/fig01…fig09.png` — all figures

Every module can also be run on its own (each file ends with verification code under
`if __name__ == '__main__':`):

```bash
python3 drive_cycle.py    # trip energy check
python3 fuel_cell.py      # shows that the nominal GSSEM is inadequate
python3 param_id.py       # re-runs the PSO identification from scratch
python3 battery.py        # battery energy balance check
```

**Randomness and reproducibility:** the two stochastic steps in the project (measurement
noise in the polarization data and the initial PSO swarm) use fixed seeds
(`seed=42`, `seed=7`). Two runs of the code produce **bit-for-bit identical** results.

---

## 2. Directory layout

```
project2-simulation/
├── README.md                    ← this file
├── requirements.txt
├── data/
│   ├── wltp_class3b_kmh.csv         official WLTC Class 3b speed trace (1 Hz, 1801 samples)
│   ├── mirai_polarization.csv       polarization data used as identification target (35 points)
│   └── identified_stack_params.json PSO output (cache; deleted → re-identified)
├── src/
│   ├── config.py                CENTRAL parameter file (every constant lives here)
│   ├── drive_cycle.py           WLTP → P_load(t) load trajectory        [Eq. 3-4]
│   ├── fuel_cell.py             Mann–Amphlett GSSEM stack model         [Eq. 5-11]
│   ├── make_polarization_data.py generation of the identification target data
│   ├── param_id.py              coefficient identification by PSO       [Section 3.3.2]
│   ├── battery.py               1-RC + hysteresis and Rint models       [Eq. 12-15, 17-18]
│   ├── cost_model.py            power flow + monetary cost + SoC reference [Eq. 16, 19-23]
│   ├── simulate.py              two-layer closed-loop simulator
│   ├── run_all.py               main script: all results + figures
│   └── ems/
│       ├── dp.py                Dynamic Programming benchmark           [Eq. 27]
│       ├── aecms.py             Adaptive ECMS                           [Eq. 28-29]
│       ├── mpc.py               Model Predictive Control                [Eq. 30]
│       └── blfs.py              Boundary Layer Surface Following        [Eq. 31]
└── results/
    ├── results_default.csv, results_all_scenarios.csv, gamma_sweep.json
    └── figures/fig01…fig09.png
```

---

## 3. Problem summary and architectural decisions

### 3.1 The optimal control problem (Eq. 25-26 of the report)

The single decision variable is the power the DC/DC converter delivers to the bus:
`u(t) ≡ P_dc(t) ≥ 0`. Thanks to the bus power balance `P_bat = P_load − P_dc` (Eq. 2)
this one variable fully determines the power split. The single state variable is the
battery state of charge (`x ≡ SoC`). The objective is to minimise the total monetary cost
of the trip (hydrogen + grid-equivalent electricity + terminal SoC penalty):

```
min Σ L_k(SoC_k, P_dc,k) + γ(SoC_N − 0.25)²,   L_k = C_fc,k + C_bat,k
```

N = 3600 decision points (Δt = 1 s), SoC window [0.20, 0.95],
SoC₀ = 0.90 → target 0.25 (a charge-depleting plug-in scenario).

### 3.2 Why these architectural decisions?

| Decision | Choice | Rationale |
|---|---|---|
| Language | Python 3 + NumPy | Committed to in the report (Section 3.7); with vectorised NumPy the DP backward pass takes 2.5 s — no need for MATLAB; free and reproducible. |
| Dependencies | numpy + matplotlib only | Zero installation friction and no version rot. PSO and grid-DP need no SciPy anyway (the state is scalar!). |
| Two layers | Plant: GSSEM + 1-RC with hysteresis; Controller: efficiency LUT + Rint | Onori's [14] two-level approach (Section 3.3.3 of the report). A real vehicle controller never has perfect model knowledge; EVERY REPORTED NUMBER comes from the plant model, the controller model only produces decisions. The cost of model mismatch is therefore measured honestly. |
| Topology | T4 (FC → unidirectional DC/DC → bus; battery directly on the bus) | Fixed in Section 3.2 of the report; the actual Mirai architecture. |
| Time resolution | Δt = 1 s | The WLTP trace is 1 Hz; the EMS acts on the second scale, minute-scale dynamics such as stack temperature are out of scope (isothermal assumption in the report). |
| Reproducibility | Fixed RNG seeds + cached identification | Scientific reportability: PSO does not re-run unless `identified_stack_params.json` is deleted; if deleted, the same seed reproduces the same result. |

### 3.3 Data sources

* **Speed profile:** the official WLTC Class 3b trace (UN GTR 15 [21]), exported from the
  regulation-checksum-verified database of the `wltp` Python package
  (1801 samples, 23.27 km, v_max = 131.3 km/h). Two cycles are concatenated to obtain a
  46.53 km / 3600 s reference trip. Two cycles are necessary because only over that
  distance can the 7.92 kWh pack be depleted by a meaningful amount (Section 3.2 of the report).
* **Polarization data:** the Mirai II FCB130 operating points published in [17]
  (details in Sections 4.4 and 5.1).
* **Battery parameters:** the cell parameters of Nejad et al. [11] (LFP,
  A123 ANR26650M1B), scaled to a 96s10p pack.

---

## 4. Module-by-module code documentation

### 4.1 `config.py` — central parameter file

**What it does:** collects EVERY constant used in the project (physical constants, the
Mirai parameters of Table 2, the battery pack, the price scenarios of Table 3, solver
settings) in a single file.

**Why:** parameters scattered across the code are the number one source of
"the report says 0.95 but the code uses 0.92" inconsistencies. One file → one truth.
Derived quantities (pack resistance `Rs_pack = Rs_cell·Ns/Np`, pack capacity, current
limits) are computed here as well, so that the scaling rule (series: voltage and
resistance multiplier; parallel: capacity multiplier, resistance divider; the RC time
constant is scale-invariant — Section 3.3.3 of the report) is visible in one place.

Important derived values:
`Q_pack = 25 Ah`, `Rs_pack = 76.8 mΩ`, `R1_pack = 57.6 mΩ`, `τ₁ = R₁C₁ = 180 s`,
`E_nom ≈ 7.92 kWh`, `P_dc_max = 104.5 kW` (110 kW net × 0.95 converter efficiency).

### 4.2 `drive_cycle.py` — load trajectory

**What it does:** computes wheel power from the longitudinal vehicle dynamics balance
(Eq. 3) and the bus load through the direction-dependent driveline efficiency (Eq. 4):

```
P_wheel = [m·a + m·g·Cr + ½·ρ·Cd·Af·v²] · v        (flat road, α = 0)
P_load  = P_wheel/η_dt   (traction)   |   P_wheel·η_dt   (regenerative braking)
```

**In-code choices:**

* Acceleration uses a **forward difference** (`a_k = (v_{k+1} − v_k)/Δt`): this is
  consistent with the zero-order hold on the decision variable — the power demand of
  interval k is the power that moves the vehicle from v_k to v_{k+1}.
* Rolling resistance is multiplied by a `v > 0.1 m/s` mask: no rolling resistance force
  is applied while the vehicle is stationary (otherwise phantom power demand appears at stops).
* The load is saturated at the motor rated power (134 kW) — never active under WLTP
  (max. 54.4 kW) but kept for physical consistency.

**Verification output:** 46.53 km, traction energy 8.56 kWh, recoverable 2.13 kWh.
Because the net demand (~6.4 kWh) exceeds the battery budget (0.65·7.92 ≈ 5.15 kWh),
using the fuel cell is MANDATORY — the problem is not degenerate (a battery-only solution
violates the SoC window; the `battery.py` test confirms this with SoC_f = 0.053 < 0.20).

### 4.3 `fuel_cell.py` — Mann–Amphlett GSSEM

**What it does:** builds the single-cell voltage from four terms (Eq. 5-9):

```
V_FC = E_Nernst − V_act − V_ohm − V_con
```

* `E_Nernst` (Eq. 6): thermodynamic potential, corrected for temperature and partial pressures.
* `V_act` (Eq. 7): semi-empirical Tafel-type activation loss; the dissolved O₂
  concentration follows Henry's law: `C*_O2 = p*_O2 / (5.08·10⁶·e^(−498/T))`.
* `V_ohm` (Eq. 8): membrane resistivity from the Mann correlation — a function of the
  effective water content λ, current density and temperature; `R_M = ρ_M·l/A` + contact resistance.
* `V_con` (Eq. 9): concentration loss `−β·ln(1 − J/J_max)`.

**Critical design point — hydrogen consumption:** the mass flow rate is not empirical but
computed **exactly from Faraday's law**:

```
ṁ_H2 = N_cell · I · M_H2 / (2F)
```

A consequence is that the LHV stack efficiency is proportional to the cell voltage:
`η_fc = V_cell / 1.254 V`. In other words the efficiency map of Eq. (11) is derived
ENTIRELY from the polarization curve — identification quality translates directly into
consumption accuracy. The report's commitment that "the efficiency map will be derived
offline and stored as a 1-D lookup table" is fulfilled by `build_lut()`.

**A subtlety in `build_lut()`:** only the monotonically increasing branch of the P(J)
curve up to peak power is kept. Beyond the peak the same power is available at a lower J
(with less hydrogen), so a rational controller would never operate there; discarding the
branch guarantees that the lookup table is invertible (one-to-one).

**The end-of-file test** shows that the nominal Mann coefficients do NOT represent the
Mirai (peak 50.9 kW ≪ 128 kW, efficiency 0.27-0.51): numerical proof that identification
is necessary.

### 4.4 `make_polarization_data.py` — identification target data

**What it does:** generates the polarization data set used as identification target from
the Mirai II anchor points reported in [17]:

* η ≈ 0.70 @ 12 kW gross → V_cell = 0.70·1.254 = 0.878 V (J ≈ 0.138 A/cm²)
* η ≈ 0.54 @ 128 kW gross → V_cell = 0.677 V (J ≈ 1.91 A/cm²)
* Open circuit with an air cathode ≈ 0.95-0.98 V

Between the anchors the curve is densified to 35 points following the canonical shape of
automotive stacks (linear in ln(J) in the activation region) and σ = 3 mV Gaussian
measurement noise is added.

**Why add noise?** Noise-free synthetic data makes the identification problem artificially
easy (a perfect fit becomes possible); 3 mV is the typical repeatability band of
polarization measurements and lets the PSO converge to a realistic RMSE floor.

**Transparency note:** since the raw digitised data of [17] was not available, this is
RECONSTRUCTED, representative data. Once genuine digitised data is obtained, the only
thing to do is to replace `data/mirai_polarization.csv` and delete
`data/identified_stack_params.json` — the rest of the pipeline works unchanged (see Section 5.1).

### 4.5 `param_id.py` — coefficient identification by PSO

**What it does:** identifies the 8-dimensional decision vector
`θ = [ξ₁, ξ₂, ξ₃, ξ₄, λ, R_C, β, J_max]`
by minimising the polarization RMSE. The bounds are the literature ranges surveyed by
Fang et al. [7].

**Why PSO (and not a gradient-based method)?**

1. The objective is **non-convex**: ξ₁ is a pure shift while ξ₃ multiplies `ln(C*_O2)`,
   which creates long correlation valleys between the two; λ and R_C are nearly
   interchangeable at low current. Gradient methods stall in those valleys.
2. The model is algebraic → thousands of evaluations are free (35 points × 6000
   particle-iterations < 1 s).
3. PSO is the reference method of the PEMFC identification literature [7] and was
   committed to in the report ("PSO/GA").

**Algorithm details (all justified in the code):**

* Canonical global-best PSO with Clerc constriction coefficients
  `w = 0.7298, c₁ = c₂ = 1.4962` (the literature standard, stability guaranteed).
* 40 particles × 150 iterations; velocity clamped to 20 % of the box width (prevents
  explosion); **reflection** on bound violation (particles stay in the physical box and
  stick to the bounds less).
* Physicality guard: a particle producing V ≤ 0 or NaN receives a 10³ penalty.

**Result:** RMSE = **6.4 mV** (over 35 points), identified stack peak power 138 kW,
η(12 kW) = 0.703, η(128 kW) = 0.52. The PSO convergence curve and the fit are in
`results/figures/fig02_polarization_pso.png`.

### 4.6 `battery.py` — two battery models

**`PlantBattery` (plant layer):** a high-fidelity model with 3 states.

* **SoC** — Coulomb counting (Eq. 13), `η_i = 0.995`.
* **V_RC1** — diffusion/relaxation voltage (Eq. 12):
  `V_RC1(k+1) = a·V_RC1(k) + b·i_k`, `a = e^(−Δt/τ)`, `τ = 180 s`.
* **V_OC** — open-circuit voltage with hysteresis (Huria's law, Eq. 15): the OCV relaxes
  towards the charge/discharge reference branch according to the current direction with
  rate `m_hyst = 150`, and **as a function of charge throughput |ΔSoC|** (hysteresis
  advances with processed charge, not with time — the experimental character of LFP
  hysteresis [12]).

Combining the terminal voltage equation (Eq. 14) `V = V_OC − i·Rs − V_RC1` with the power
demand yields a quadratic in the current; the physical root is (Eq. 17):

```
I = [(V_OC − V_RC1) − √((V_OC − V_RC1)² − 4·Rs·P_bat)] / (2·Rs)
```

A negative discriminant naturally encodes the pack power capability limit (report, below
Eq. 17). Datasheet current limits are applied on top: continuous charge 4C (100 A pack),
discharge 20C (500 A pack). Regenerative power exceeding the 4C limit goes to the
**friction brakes** (reported as `P_friction`; it is neither charged nor credited).

**Why is hysteresis indispensable for LFP?** The LFP OCV curve is almost flat between
20-80 % SoC (a ~5 V band at pack level); the 25-40 mV/cell difference between the charge
and discharge branches dominates SoC estimation in the flat region [11],[12]. The OCV
branches are represented by **8th-order polynomials** as in [11]; the polynomial is fitted
to a densely resampled node curve (to keep Runge oscillations from corrupting the plateau).

**`RintModel` (controller layer):** a stateless, vectorised static model — the mean OCV
branch plus Rs only. It is DELIBERATELY less accurate than the plant: a real controller
has incomplete model knowledge, and the gap between the two layers measures the cost
impact of model mismatch (the two-level approach of Section 3.3.3 of the report). The
algebraic nature of this model is also what lets DP evaluate its 151×105 transition
tensor in a single NumPy pass.

### 4.7 `cost_model.py` — power flow, cost and SoC reference

**Power flow chain (Eq. 16):** `P_dc → P_fc,net = P_dc/η_dc → P_fc,gross`
(adding auxiliary consumption) `→ ṁ_H2` (efficiency LUT).

**Auxiliary consumption model (a deliberate deviation from the report — see Section 5.2):**
`P_aux = 1.0 kW + 0.09·P_gross` (while the FC is on). The report assumes a fixed ratio
(~0.10-0.13 [17]); a fixed ratio makes the tank-to-bus efficiency monotone in power and
destroys the INTERIOR optimal operating point of the fuel cell — whereas the measured
system efficiency of the Mirai peaks around 12 kW [17]. A constant floor (compressor
idle, pumps, control electronics) plus a proportional term both stays in the 0.10-0.13
band above 30 kW and reproduces the interior peak (fig03).

**Costs:**

* `C_fc` (Eq. 19): `M_H2 · ṁ_H2 · Δt` — independent of the state given the decision, always ≥ 0.
* `C_bat` (Eq. 20-21): grid-equivalent valuation with direction-dependent efficiency.
  On discharge, the grid energy invested per unit of bus energy exceeds 1 (division by the
  round-trip factor); on charge only the recoverable fraction is credited (multiplication).
  η_dis = V_terminal/V_OC and η_chg = V_OC/V_terminal are computed instantaneously from the
  Rint model; the 0.98 factor distributes the coulombic/charger share symmetrically.
  The braking credit is therefore automatically valued at the grid price (C_bat is negative on charge).
* Terminal penalty (Eq. 23): `γ(SoC_N − 0.25)²`, γ = 1000 €.

**Charge curtailment — a critical implementation detail:** `stage_cost()` clips the charge
power through two physical mechanisms: (1) the 4C datasheet limit, (2) the SoC_max ceiling
(BMS tapering). Without (2), the upper bound of the DP state grid becomes spuriously
"infeasible" at EVERY step with regeneration near SoC_max, and the infinite cost leaks into
the interior nodes through linear interpolation, poisoning the WHOLE value function
(experienced verbatim during development: V₀ = inf). The clipped power goes to the friction
brake and is not credited.

**SoC reference — energy-based (a justified deviation from the report, see Section 5.3):**
The time-linear reference of Eq. (29) turned out to be UNTRACKABLE in closed loop: at
stops and during the final deceleration there is no traction load, so the battery cannot
physically be discharged while the reference keeps falling → every real-time strategy gets
stranded ~0.025 above the target and pays the penalty of the reference design rather than
of the strategy. The remedy (standard in the plug-in EMS literature, e.g. [14] Ch. 6) is
to make the reference linear in **cumulative positive traction energy**:

```
ref(k) = SoC₀ + (SoC_target − SoC₀) · E_cum(k)/E_total
```

E_cum is a cycle statistic; it uses exactly the same "the trip is known in advance"
assumption that DP already makes (in a real vehicle it comes from navigation). If
`set_reference()` is not called, the code falls back to the time-linear reference of Eq. (29).

### 4.8 `ems/dp.py` — Dynamic Programming benchmark

**What it does:** solves the Bellman backward recursion (Eq. 27) on the grids specified in
the report (ΔSoC = 0.005 → 151 nodes; ΔP_dc = 1 kW → 105 decisions), following the
implementation structure of Sundström & Guzzella [15].

**Implementation decisions:**

* **Value interpolation:** the successor state SoC' generally falls between nodes;
  V_{k+1}(SoC') is obtained by linear interpolation. The alternative, nearest-node
  assignment, turns grid quantisation noise into policy (the well-known chattering
  problem [15]).
* **Vectorisation:** at each time step the 151×105 cost+transition tensor is evaluated in
  a single NumPy pass → the 3600-step backward pass takes **2.5 seconds**. This speed is
  the concrete payoff of choosing a static FC model (Section 3.1.2 of the report: a
  two-orders-of-magnitude saving over a dynamic model).
* **Policy table + closed-loop forward pass:** the backward pass produces the table
  u*(k, SoC); the forward pass replays that policy in closed loop against the PLANT model
  (with the control also interpolated between neighbouring SoC nodes). Even DP's reported
  cost therefore contains the model mismatch — there is none of the optimistic bias of
  reporting open-loop cost inside the controller model. (The backward pass predicts
  2.733 €, the plant realises 2.718 € — a 0.5 % agreement, which also shows how small the
  model mismatch is.)
* Since the whole trip load is known in advance, DP serves only as an offline benchmark
  (Table 4 of the report).

### 4.9 `ems/aecms.py` — Adaptive ECMS

**What it does:** at each step it minimises the Hamiltonian (Eq. 28) pointwise over a
1 kW decision grid:

```
H(u) = L(SoC, u) + s(t)·(SoC_k − SoC_{k+1}(u))
```

The equivalence factor s(t), which takes the place of the PMP co-state λ, is adapted by a
PI law on the SoC tracking error (Eq. 29, Gao [5]):

```
s(t) = s₀ + k_p·e + k_i·∫e,    e = SoC_ref − SoC
```

**A plug-in subtlety (Section 3.5.2 of the report + Xu [4]):** in classical ECMS, s alone
establishes the fuel equivalence. Here L already monetises battery energy at the grid
price, so the economic trade-off lives entirely inside L; the only job left for s is to
make the charge-depleting reference be tracked. Hence **s₀ = 0** — no heuristic base value
is needed and the design is cleaner. A constant multiplier was shown in [4] to drive the
strategy into the physical bounds; the PI feedback prevents that.

* **Anti-windup:** the integrator is clamped with `|k_i·∫e| ≤ 2 €/SoC`, preventing
  integral blow-up when the actuator saturates at the end of the trip.
* Decisions that would violate the lower SoC window receive H = ∞ (the upper window is
  already protected by the curtailment in the cost model).

### 4.10 `ems/mpc.py` — Model Predictive Control

**What it does:** at each step it solves the finite-horizon constrained problem of
Eq. (30): N_p = 15 s horizon, constant-load assumption (`P_load(j) = P_load(k)` — no
telematics preview), only the first move is applied.

**Why local grid-DP instead of a QP? (a justified deviation from the report, see Section 5.4):**
The stage cost is **non-convex** in P_dc (the hydrogen map carries the curvature of the
identified polarization curve; the direction-dependent efficiency of Eq. 20 creates a kink
at P_bat = 0). A QP requires a convex surrogate and returns the minimum of the surrogate.
Since the state is scalar, an exhaustive local DP is cheap: SoC moves at most ~0.002/s →
a window of ±0.03 around the current SoC (31 nodes × 0.002) covers every trajectory the
horizon can reach; with a 2 kW decision grid the subproblem is solved EXACTLY at grid
resolution within milliseconds (measured: 0.59 ms/step). The constant-load assumption makes
the transition/cost tensors common along the horizon → the tensors are built once per step.

**Offset-free correction:** the constant-load assumption is biased — during traction peaks
the controller believes the peak will last the whole horizon and over-protects the battery
(burning fuel cell power exactly when there is an opportunity to deplete). No finite γ_mpc
can remove this persistent model bias (the classical MPC offset problem). The standard
remedy is integral action on the tracking error: the tracked reference is shifted by the
low-pass-accumulated bias (`β = 0.005` is the current working value in `config.py`; the
sweep that will settle it is still in progress — see Section 7).

### 4.11 `ems/blfs.py` — protection layer

**What it does:** NOT a standalone strategy; a rule-based protection wrapped underneath
A-ECMS or MPC (Section 3.6.5 of the report). A ±0.05 hysteresis band around the reference:

* ABOVE the band → FC at minimum (P_dc = 0): the battery is discharged back into the band;
* BELOW the band → FC at its **peak system efficiency** point: the battery is charged at
  the cheapest possible hydrogen cost;
* INSIDE the band → the upper layer's decision passes through unchanged.

The peak efficiency point is computed ONCE from the LUT as the maximiser of the
tank-to-bus efficiency `η_sys = P_dc/(ṁ·LHV)` (converter and auxiliary losses included —
the point where a joule put into the battery through the FC is cheapest).

In addition the fuel cell load ramp is limited (Eq. 31): `|dP_fc/dt| ≤ 5 kW/s` — against
gas starvation and membrane degradation; it protects durability without entering the cost
function. The limit is applied to the bus-side command; since the P_dc ↔ P_gross mapping
is smooth and monotone, it implies a (slightly tighter) limit on the gross side as well.

### 4.12 `simulate.py` — two-layer closed loop

The step loop: (1) the controller decision `u_k` (timed with the wall clock → the CPU time
per step metric), (2) `P_bat = P_load − u` applied to the plant (clipping and friction
braking happen in the plant), (3) the hydrogen flow rate from the LUT chain, (4) monetary
accounting over the PLANT trajectory (Eq. 19-22).

Reported metrics (one-to-one with the list in Section 3.7 of the report): total operating
cost [€ and €/100 km], H₂ mass [kg], battery electricity [kWh], terminal SoC error, FC
quasi-steadiness (mean |ΔP_fc| and the number of on/off transitions), and mean CPU time per step.

### 4.13 `run_all.py` — main script

Runs the whole pipeline in order and generates EVERY figure from code (no manual
plotting — the documentation stays in sync with the code). Because controller objects
carry state (integrators, ramp memory), fresh instances are constructed for every
scenario (`make_controllers`).

---

## 5. Deviations from the report formulation and their justification

The implementation aimed to stay faithful to the MAT 4901E formulation; there are
justified deviations at the following four points. Each is documented in the code as well.

### 5.1 The polarization data is representative

Since the raw data of [17] could not be digitised, the identification target was
reconstructed from the published anchor points of [17] (Section 4.4). The pipeline is
data-agnostic: when real data arrives, a single CSV changes.

### 5.2 Auxiliary consumption: an affine model instead of a fixed ratio

`P_aux = 1 kW + 0.09·P_gross`. The fixed ratio destroyed the interior efficiency peak; the
affine model reproduces both the 0.10-0.13 band of [17] (>30 kW) and the measured system
peak around 12 kW. The BLFS notion of a "peak efficiency point" is only meaningful if that
peak exists.

### 5.3 SoC reference: linear in energy, not in time

The time-linear reference (Eq. 29) is physically untrackable during the final deceleration
and loaded every real-time strategy with an unfair terminal penalty of ~0.5-0.8 €
(development log: A-ECMS SoC_f = 0.227, MPC = 0.275). The energy-based reference removes
this structural error at its source; it does not touch DP (which uses no reference).

### 5.4 MPC: local grid-DP instead of a QP, plus offset-free integral correction

A non-convex stage cost condemns a QP to a surrogate; with a scalar state an exhaustive
local search is both exact and real-time compatible (0.59 ms/step). The persistent SoC
offset of the constant-load assumption was removed with the standard offset-free-MPC
integral action (β = 0.005). Both decisions are detailed in Section 4.10.

---

## 6. Results

**Status: in progress.** The strategy comparison (default scenario, price-scenario
sensitivity, and the γ penalty-weight sweep) has not been finalised yet. Numerical
results and figures will be added to this section, together with their generating
commit, once each strategy has been implemented, tuned and checked end to end. Until
then, no cost/SoC/efficiency figures should be treated as final — including any values
that may appear in intermediate files under `results/`.

### Figures produced so far (`results/figures/`)

The figures below are produced by `run_all.py` as work-in-progress diagnostics while each
component is being built; they are not yet final results.

| File | Contents |
|---|---|
| fig01_cycle_load.png | 2×WLTC 3b speed trace + P_load trajectory (Eq. 3-4) |
| fig02_polarization_pso.png | Polarization fit (data/identified/nominal) + PSO convergence |
| fig03_efficiency_map.png | Stack LHV efficiency and tank-to-bus system efficiency; system peak marked |
| fig04_ocv_hysteresis.png | LFP OCV charge/discharge branches, hysteresis band, operating window |
| fig05_soc_trajectories.png | SoC trajectories of the strategies implemented so far + the energy-based reference |
| fig06_pdc_profiles.png | P_dc(t) profiles per strategy (load shaded) |
| fig07_cost_breakdown.png | Cost decomposition: H₂ / electricity / terminal penalty |
| fig08_sensitivity.png | Total cost across price scenarios and strategies |
| fig09_gamma_sweep.png | Terminal SoC and operating cost versus γ (DP) |

---

## 7. Tuning process

**Status: in progress.** Controller parameters (e.g. the A-ECMS PI gains and the MPC
offset-free integral gain β) are still being swept and adjusted as each strategy is
implemented. `config.py` holds the current working values with comments explaining the
reasoning so far; they are not yet final and will keep changing until each strategy's
tuning is closed out. A record of the tuning sweeps and the selected values will be added
here once settled.

---

## 8. Verification and sanity checks

The checks below validate individual model components already implemented; they do not
depend on the full strategy comparison and are kept up to date as development proceeds.
End-to-end checks that require all four strategies (e.g. optimality ordering across
strategies) will be added once the comparison itself is finalised (see Section 6).

1. **Cycle verification:** 46.53 km ≈ 2×23.27 km (the official GTR 15 value);
   traction 8.56 kWh (≈ 184 Wh/km — consistent with D-segment BEV consumption under WLTP).
2. **Battery energy balance:** 10 kW × 10 min discharge → ΔSoC·E_nom = 1.672 kWh versus
   1.667 kWh supplied (0.3 %, internal losses). Battery-only test over the full trip:
   ΔSoC = 0.851 ↔ the net flow of 8.56−2.12 kWh measured in the plant — it closes.
3. **PSO:** improvement < 0.1 mV over the last 60 of 150 iterations (convergence, fig02);
   RMSE 6.4 mV ≈ twice the injected 3 mV noise floor (no overfitting).
4. **Boundary tests:** regeneration clipping near SoC_max (the fix for the V₀ = inf bug,
   Section 4.7); u = 0 over the whole trip → SoC 0.053 (window violation) → the fuel cell
   is mandatory.

---

## 9. Limitations and future work

* **Isothermal stack (T = 343 K):** the interaction of temperature dynamics and ageing
  with the EMS [20] is out of scope (it was excluded in the report as well).
* **Degradation costs** do not appear in the objective (a decision taken in the report);
  the BLFS ramp limit provides indirect protection. Extending the cost with FC/battery
  ageing is a natural continuation.
* **Representative polarization data** (Section 5.1): a single-CSV swap once genuinely
  digitised data is available.
* **Constant-load MPC prediction:** an MPC with navigation/telematics preview (real speed
  prediction) would close the DP-MPC gap further.
* **Zero road grade (α = 0):** as required by the WLTP definition; extending to real route
  profiles is a one-line change in `drive_cycle.py` (the grade term of Eq. 3 is present as
  a comment in the code).

---

## 10. References

The numbering is shared with the MAT 4901E report; the principal sources are:

* [4] Xu et al. 2013 — PMP, plug-in FCEV (the monetary equivalence approach)
* [5] Gao et al. 2021 — A-ECMS PI adaptation
* [6] Mann et al. 2000 — GSSEM
* [7] Fang et al. 2026 — 0-D PEMFC models + metaheuristic identification review
* [11] Nejad et al. 2016 — 1-RC+hysteresis ECM, LFP parameters
* [12] Huria et al. 2014 — hysteresis law
* [14] Onori et al. 2016 — HEV EMS book (two-level approach, reference design)
* [15] Sundström & Guzzella 2009 — generic DP function
* [17] Mirai II energy balance (2025) — stack/auxiliary/efficiency anchors
* [21] UN GTR 15 — WLTP; [22] Toyota Mirai technical specification
* [23] H2.LIVE, [24] BDEW — German 2026 prices

The full list with links is given in [`docs/REFERENCES.md`](docs/REFERENCES.md) and in
Section 4 of the MAT 4901E report
(`../project1-formulation/report/MAT4901E_Report.pdf`).
