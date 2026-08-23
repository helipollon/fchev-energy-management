# References — Graduation Project II (MAT 4902E)

Two parts:

* **Part A:** the reference list of the MAT 4901E report, [1]–[24] — the numbering is
  shared with the report, and both the report and the code cite these numbers. The PDFs
  live in `../../project1-formulation/references/` (not redistributed in this repository).
* **Part B:** ADDITIONAL sources used in the Graduation Project II implementation,
  [25]–[38] — PSO theory, offset-free MPC, reference design and the standard textbooks.
  These are to be appended to the report's list.

A topic → source reading guide follows at the end.

---

## Part A — sources shared with MAT 4901E, [1]–[24]

**EMS reviews and foundational strategy papers**

[1] Khalatbarisoltani, A., Kandidayeni, M., Boulon, L., & Hu, X. (2024).
Energy management strategies for fuel cell vehicles: A comprehensive review.
*IEEE Transactions on Intelligent Transportation Systems, 25*(1), 14–32.
https://ieeexplore.ieee.org/abstract/document/10247150
→ EMS taxonomy, topologies T1–T5 (Figure 2).

[2] Sciarretta, A., & Guzzella, L. (2007). Control of hybrid electric
vehicles. *IEEE Control Systems Magazine, 27*(2), 60–70.
https://ieeexplore.ieee.org/abstract/document/4140747
→ The classical exposition of the ECMS ↔ PMP connection.

[3] Paganelli, G., Delprat, S., Guerra, T. M., Rimaux, J., & Santin, J. J.
(2002). Equivalent consumption minimization strategy for parallel hybrid
powertrains. *IEEE Vehicular Technology Conference*, 2076–2081.
→ The paper in which ECMS was born.

[4] Xu, L., Ouyang, M., Li, J., Yang, F., Lu, L., & Hua, J. (2013).
Application of Pontryagin's Minimal Principle to the energy management
strategy of plugin fuel cell electric vehicles. *International Journal of
Hydrogen Energy, 38*(24), 10104–10115.
https://www.sciencedirect.com/science/article/abs/pii/S0360319913013578
→ Plug-in monetary valuation + the constant-factor pathology; the main template of this project.

[5] Gao, J., Li, Y., Liu, Y., & Li, X. (2021). Adaptive real-time optimal
energy management strategy based on equivalent factors optimization for
hybrid fuel cell system. *International Journal of Hydrogen Energy, 46*,
4329–4338.
https://www.sciencedirect.com/science/article/abs/pii/S0360319920340830
→ The A-ECMS PI adaptation law (the source of Eq. 29).

**PEMFC modelling**

[6] Mann, R. F., Amphlett, J. C., Hooper, M. A. I., Jensen, H. M.,
Peppley, B. A., & Roberge, P. R. (2000). Development and application of a
generalised steady-state electrochemical model for a PEM fuel cell.
*Journal of Power Sources, 86*(1–2), 173–180.
https://www.sciencedirect.com/science/article/abs/pii/S037877539900484X
→ GSSEM: the source of Eq. 5–10; the membrane resistivity correlation.

[7] Fang, Y., Yang, F., Xing, Y., Zhang, X., Wang, W., & Lin, S. (2026).
A comparative review of modeling and metaheuristic parameter identification
strategies for zero-dimensional PEMFC polarization models. *Energies, 19*,
1438. https://www.mdpi.com/1996-1073/19/6/1438
→ Identification methodology and parameter bounds (the BOUNDS in `param_id.py`).

[8] Springer, T. E., Zawodzinski, T. A., & Gottesfeld, S. (1991). Polymer
electrolyte fuel cell model. *Journal of the Electrochemical Society, 138*,
2334–2342. https://iopscience.iop.org/article/10.1149/1.2085971/meta
→ The origin of the membrane water content concept λ.

[9] Kim, J., Lee, S., Srinivasan, S., & Chamberlin, C. E. (1995). Modeling
of proton-exchange membrane fuel-cell performance with an empirical
equation. *Journal of the Electrochemical Society, 142*, 2670–2674.
https://iopscience.iop.org/article/10.1149/1.2050072/meta
→ The empirical polarization equation (exponential form of the concentration loss).

[10] Ziogou, C., Voutetakis, S., Papadopoulou, S., & Georgiadis, M. C.
(2011). Modeling, simulation and experimental validation of a PEM fuel
cell system. *Computers & Chemical Engineering, 35*, 1886–1900.
→ A dynamic 0-D model — the comparison baseline for choosing a static one.

**Battery modelling**

[11] Nejad, S., Gladwin, D. T., & Stone, D. A. (2016). A systematic review
of lumped-parameter equivalent circuit models for real-time estimation of
lithium-ion battery states. *Journal of Power Sources, 316*, 183–196.
https://www.sciencedirect.com/science/article/abs/pii/S0378775316302427
→ Justification of the 1-RC+hysteresis choice; cell parameters (Rs, R1, C1);
8th-order OCV polynomials.

[12] Huria, T., Ludovici, G., & Lutzemberger, G. (2014). State of charge
estimation of high power lithium iron phosphate cells. *Journal of Power
Sources, 249*, 92–102.
→ The differential hysteresis law (Eq. 15).

[13] Plett, G. L. (2004). Extended Kalman filtering for battery management
systems of LiPB-based HEV battery packs — Part 3: State and parameter
estimation. *Journal of Power Sources, 134*, 277–292.
→ The state/parameter estimation framework.

**Optimal control and DP**

[14] Onori, S., Serrao, L., & Rizzoni, G. (2016). *Hybrid electric
vehicles: Energy management strategies.* Springer.
https://link.springer.com/book/10.1007/978-1-4471-6781-5
→ The two-level model approach and reference design; the single best book in the field.

[15] Sundström, O., & Guzzella, L. (2009). A generic dynamic programming
Matlab function. *IEEE Control Applications & Intelligent Control*,
1625–1630. https://ieeexplore.ieee.org/abstract/document/5281131
→ The DP grid + interpolation implementation structure (`ems/dp.py`).

[16] Bertsekas, D. P. (2005). *Dynamic programming and optimal control*
(3rd ed.). Athena Scientific.
→ The theoretical foundation of the Bellman recursion.

**Reference vehicle, drive cycle, prices**

[17] (2025). Energy balance and hydrogen exhaust emissions of the
second-generation Toyota Mirai. *International Journal of Hydrogen Energy.*
https://www.sciencedirect.com/science/article/pii/S0360319925034093
→ Stack/efficiency anchors, auxiliary consumption ratio, polarization target points.

[18] Hu, X., Murgovski, N., Johannesson, L. M., & Egardt, B. (2013). Energy
efficiency analysis of a series plug-in hybrid electric bus with different
energy management strategies and battery sizes. *Applied Energy, 111*,
1001–1009.

[19] Tribioli, L., Cozzolino, R., Chiappini, D., & Iora, P. (2016). Energy
management of a plug-in fuel cell/battery hybrid vehicle with on-board fuel
processing. *Applied Energy, 184*, 140–154.

[20] Kandidayeni, M., Macias, A., Boulon, L., & Kelouwani, S. (2020).
Investigating the impact of ageing and thermal management of a fuel cell
system on energy management strategies. *Applied Energy, 274*, 115293.
→ The effects left out of scope by the isothermal assumption.

[21] United Nations Economic Commission for Europe. (2022). *UN Global
Technical Regulation No. 15: Worldwide harmonized Light vehicles Test
Procedure (WLTP)* (ECE/TRANS/WP.29/2022/42/Rev.1).
https://unece.org/sites/default/files/2022-04/ECE_TRANS_WP.29_2022_42_Rev.1E.pdf
→ The official definition of the WLTC Class 3b trace (`data/wltp_class3b_kmh.csv`).

[22] Toyota Motor Corporation. (2022). *Toyota Mirai technical
specifications.* Toyota (GB) Media Site.
https://media.toyota.co.uk/wp-content/uploads/sites/5/pdf/220203M-Mirai-Tech-Spec.pdf

[23] H2 MOBILITY Deutschland GmbH. (2026). *H2.LIVE: Hydrogen stations in
Germany and Europe — fuel pricing.* https://h2.live/en/

[24] BDEW Bundesverband der Energie- und Wasserwirtschaft. (2026).
*BDEW-Strompreisanalyse Januar 2026.*
https://www.bdew.de/media/documents/BDEW_Strompreisanalyse_012026_1.pdf

---

## Part B — sources added in Graduation Project II, [25]–[38]

*Note: entries [25]–[38] are classical, widely known publications; those without a DOI/URL
are found as the single top hit on Google Scholar by title. A final check of the entries is
recommended before they are appended to the report.*

**PSO theory (rationale for `param_id.py`)**

[25] Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization.
*Proceedings of ICNN'95 — International Conference on Neural Networks*,
Vol. 4, 1942–1948. IEEE.
→ The paper in which PSO was born; the velocity/position update structure.

[26] Clerc, M., & Kennedy, J. (2002). The particle swarm — explosion,
stability, and convergence in a multidimensional complex space. *IEEE
Transactions on Evolutionary Computation, 6*(1), 58–73.
→ Analytical derivation of the constriction coefficients w = 0.7298,
c₁ = c₂ = 1.4962 (the values used in the code).

[27] Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer.
*IEEE International Conference on Evolutionary Computation*, 69–73.
→ The inertia weight concept; the practice of velocity clamping.

**ECMS / PMP in depth (`ems/aecms.py`)**

[28] Musardo, C., Rizzoni, G., Guezennec, Y., & Staccia, B. (2005).
A-ECMS: An adaptive algorithm for hybrid electric vehicle energy
management. *European Journal of Control, 11*(4–5), 509–524.
→ The paper that named "adaptive ECMS"; online updating of s.

[29] Serrao, L., Onori, S., & Rizzoni, G. (2011). A comparative analysis of
energy management strategies for hybrid electric vehicles. *Journal of
Dynamic Systems, Measurement, and Control, 133*(3), 031012.
→ A systematic comparison of the DP–PMP–ECMS equivalence; the literature context
for our result table (DP < MPC < A-ECMS, the 1–3 % band).

[30] Kim, N., Cha, S., & Peng, H. (2011). Optimal control of hybrid
electric vehicles based on Pontryagin's minimum principle. *IEEE
Transactions on Control Systems Technology, 19*(5), 1279–1287.
→ The rigorous version of the argument that λ is approximately constant.

**MPC theory (rationale for `ems/mpc.py`)**

[31] Rawlings, J. B., Mayne, D. Q., & Diehl, M. (2017). *Model predictive
control: Theory, computation, and design* (2nd ed.). Nob Hill Publishing.
→ Receding horizon, terminal cost, stability; a free PDF is on the publisher's site.

[32] Pannocchia, G., & Rawlings, J. B. (2003). Disturbance models for
offset-free model-predictive control. *AIChE Journal, 49*(2), 426–437.
→ Offset-free MPC: removing persistent model bias through integral/disturbance
estimation — the theoretical basis of the `beta_int` correction.

[33] Borhan, H., Vahidi, A., Phillips, A. M., Kuang, M. L., Kolmanovsky,
I. V., & Di Cairano, S. (2012). MPC-based energy management of a
power-split hybrid electric vehicle. *IEEE Transactions on Control Systems
Technology, 20*(3), 593–603.
→ A representative application of MPC in HEVs; the effect of the prediction model choice.

**Textbooks (general background)**

[34] Guzzella, L., & Sciarretta, A. (2013). *Vehicle propulsion systems:
Introduction to modeling and optimization* (3rd ed.). Springer.
→ Longitudinal dynamics (Eq. 3–4), the quasi-static modelling philosophy, an
introduction to EMS.

[35] Larminie, J., & Dicks, A. (2003). *Fuel cell systems explained*
(2nd ed.). Wiley.
→ The most readable introduction to PEMFC loss mechanisms and the Nernst/Tafel derivations.

[36] Barbir, F. (2013). *PEM fuel cells: Theory and practice* (2nd ed.).
Academic Press.
→ The polarization curve, water management, auxiliary systems (the compressor-floor argument).

[37] Plett, G. L. (2015). *Battery management systems, Volume I: Battery
modeling.* Artech House.
→ ECM families, OCV-hysteresis models, Coulomb counting.

[38] Kirk, D. E. (2004). *Optimal control theory: An introduction.* Dover.
→ A concise classic on PMP and the variational foundations.

---

## Topic → source reading guide

| Topic to study | Start with | Then go deeper |
|---|---|---|
| FCHEV overview + topologies | [1] | [14] Ch. 1–2 |
| Vehicle dynamics, drive cycle, quasi-static model | [34] Ch. 2 | [21] |
| PEMFC electrochemistry | [35] Ch. 3 | [6], [8], [9], [36] |
| PEMFC parameter identification | [7] | [25], [26], [27] |
| Battery ECM + LFP hysteresis | [37] Ch. 2–3 | [11], [12], [13] |
| Optimal control fundamentals | [38] | [16] |
| DP implementation | [15] | [16], [14] Ch. 4 |
| PMP → ECMS → A-ECMS | [2] | [3], [30], [28], [5], [29] |
| Plug-in monetary formulation | [4] | [18], [19] |
| MPC | [31] Ch. 1–2 | [32], [33] |
| Reference (SoC) design | [14] Ch. 6 | [4] |
| Comparing the results with the literature | [29] | [1] |

### Notes on citation use

* In-code citations ([6], [11], [15]…) use the report numbering; the Part B sources should
  be appended to the bibliography from [25] onwards when the MAT 4902E report is written.
* Suggested citations for the three main decisions in the "deviations from the report"
  section of the README: energy-based reference → [14]; offset-free MPC correction → [32];
  grid-DP subsolver → [15] plus the convexity discussion in [31].
* For the PSO settings (constriction coefficients) see [26]; for the bound ranges see [7].
