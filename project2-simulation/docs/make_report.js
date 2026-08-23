/*
 * make_report.js — Generates MAT4902_GraduationProject2_Report.docx
 * in the same format as the MAT 4901E report (title page, ToC, headers,
 * numbered sections, figure/table captions, references).
 *
 * Regenerate with:  node docs/make_report.js   (run from bitirme2/ root)
 * Figures are read from results/figures/, so run src/run_all.py first.
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ImageRun,
  TableOfContents, PageBreak, Header, PageNumber, TabStopType, ShadingType,
} = require('docx');

const ROOT = path.resolve(__dirname, '..');
const FIG = (n) => path.join(ROOT, 'results', 'figures', n);
const OUT = path.join(ROOT, 'MAT4902_GraduationProject2_Report.docx');

// ---------- helpers ---------------------------------------------------------
const CONTENT_W = 9026; // A4 content width in DXA (11906 - 2*1440)

function para(text, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: [new TextRun({ text, size: 22, ...opts.run })],
    ...opts.para,
  });
}
function paraRuns(runs, opts = {}) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: runs.map(r => new TextRun({ size: 22, ...r })),
    ...opts,
  });
}
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    spacing: { before: 280, after: 160 },
    children: [new TextRun({ text, bold: true, size: 28, color: '000000' })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    spacing: { before: 220, after: 130 },
    children: [new TextRun({ text, bold: true, size: 24, color: '000000' })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3,
    spacing: { before: 180, after: 110 },
    children: [new TextRun({ text, bold: true, size: 22, color: '000000' })] });
}
function eq(text, tag) {
  // centred equation line with right-aligned tag, GP1 style
  return new Paragraph({
    tabStops: [
      { type: TabStopType.CENTER, position: Math.round(CONTENT_W / 2) },
      { type: TabStopType.RIGHT, position: CONTENT_W },
    ],
    spacing: { before: 60, after: 120 },
    children: [
      new TextRun({ text: '\t' }),
      new TextRun({ text, italics: true, size: 22 }),
      new TextRun({ text: tag ? '\t' + tag : '', size: 22 }),
    ],
  });
}
function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 60, after: 200 },
    children: [new TextRun({ text, size: 18, italics: true })],
  });
}
function figure(file, widthPx, ratio, capText) {
  const h = Math.round(widthPx * ratio);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(FIG(file)),
        transformation: { width: widthPx, height: h } })],
    }),
    caption(capText),
  ];
}
function cell(text, { bold = false, w, fill } = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA },
    shading: fill ? { type: ShadingType.CLEAR, fill } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({
      spacing: { after: 0 },
      children: [new TextRun({ text, bold, size: 18 })] })],
  });
}
function table(headers, rows, widths) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true,
        children: headers.map((t, i) => cell(t, { bold: true, w: widths[i], fill: 'E8E8E8' })) }),
      ...rows.map(r => new TableRow({
        children: r.map((t, i) => cell(String(t), { w: widths[i] })) })),
    ],
  });
}

// ---------- title page -------------------------------------------------------
const titleChildren = [
  new Paragraph({ spacing: { before: 2400 } }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({
      text: 'NUMERICAL SOLUTION & COMPARISON OF ENERGY MANAGEMENT STRATEGIES FOR HYBRID HYDROGEN SYSTEMS',
      bold: true, size: 40 })],
  }),
  new Paragraph({ spacing: { before: 1600 } }),
  ...[
    ['Prepared by', 'AHMET YEŞİL'],
    ['Student No', '090220359'],
    ['Submission Date', 'January 15, 2027'],
    ['Course', 'MAT 4902E'],
    ['Supervisor', 'PROF. DR. SEMRA AHMETOLAN'],
  ].map(([k, v]) => new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 80 },
    children: [
      new TextRun({ text: k + ' : ', size: 24 }),
      new TextRun({ text: v, bold: true, size: 24 }),
    ],
  })),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- front matter -----------------------------------------------------
const frontMatter = [
  new Paragraph({ children: [new TextRun({ text: 'Table of Contents', bold: true, size: 28 })],
    spacing: { after: 200 } }),
  new TableOfContents('Table of Contents', { hyperlink: true, headingStyleRange: '1-3' }),
  new Paragraph({ children: [new PageBreak()] }),
  new Paragraph({ children: [new TextRun({ text: 'Table of Figures', bold: true, size: 28 })],
    spacing: { after: 160 } }),
  ...[
    'Figure 1  Speed profile and bus load trajectory of the reference trip (2×WLTC Class 3b).',
    'Figure 2  Polarization-curve fit of the identified GSSEM and PSO convergence history.',
    'Figure 3  Stack LHV efficiency and tank-to-bus system efficiency maps (Eq. 11 of GP1).',
    'Figure 4  LFP open-circuit-voltage branches with hysteresis band and operating window.',
    'Figure 5  Charge-depleting SoC trajectories of the five controllers (plant model).',
    'Figure 6  Fuel-cell bus power commands P_dc(t) of the five controllers.',
    'Figure 7  Total trip cost decomposition under the default price scenario.',
    'Figure 8  Price-scenario sensitivity of the total trip cost.',
    'Figure 9  DP sensitivity to the terminal penalty weight γ.',
  ].map(t => para(t, { para: { alignment: AlignmentType.LEFT } })),
  new Paragraph({ children: [new TextRun({ text: 'Table of Tables', bold: true, size: 28 })],
    spacing: { before: 240, after: 160 } }),
  ...[
    'Table 1  Mapping of the simulation modules to the GP1 formulation.',
    'Table 2  PSO search bounds and identified GSSEM coefficients for the Mirai II stack.',
    'Table 3  Strategy comparison under the default price scenario.',
    'Table 4  Price-scenario sensitivity (total trip cost, EUR).',
    'Table 5  Terminal-penalty weight sweep on the DP benchmark.',
    'Table 6  Documented deviations from the GP1 formulation.',
  ].map(t => para(t, { para: { alignment: AlignmentType.LEFT } })),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- body -------------------------------------------------------------
const body = [];

// 1 ---------------------------------------------------------------------------
body.push(h1('1. Definition and Purpose of Design'));
body.push(para(
  'This study is the second and final stage of the graduation project whose first stage (MAT 4901E) formulated the optimal energy management problem of a plug-in hydrogen fuel cell hybrid electric vehicle (FCHEV). In the first stage, the reference vehicle (second-generation Toyota Mirai with the battery rescaled to 7.92 kWh for plug-in operation), the T4 powertrain topology, the component models (Mann–Amphlett GSSEM stack model, 1-RC + hysteresis battery model), the monetary cost functional based on Germany 2026 hydrogen and electricity prices, and four solution strategies (DP, A-ECMS, MPC, BLFS) were selected and formulated. The purpose of the present stage is the numerical realization of that formulation: a two-layer simulation environment is implemented in Python, the semi-empirical stack coefficients are identified for the Mirai II by particle swarm optimization, the four strategies are implemented and executed in closed loop over the reference trip, and the strategies are compared in terms of total operating cost, hydrogen and electricity consumption, terminal state-of-charge accuracy, fuel-cell quasi-stability and per-step computation time, together with sensitivity analyses over the price scenarios and the terminal penalty weight.'));
body.push(para(
  'All equation numbers of the form Eq. (n) in this report refer to the MAT 4901E report; new material introduced in this stage is numbered by section. The complete source code, data and result files are organized so that a single command regenerates every number and every figure appearing in this report, and both stochastic components of the pipeline (measurement noise of the identification data set and the PSO initial swarm) are seeded, making the study bit-exact reproducible.'));

// 2 ---------------------------------------------------------------------------
body.push(h1('2. Scope of Design and Areas of Usage'));
body.push(para(
  'The scope of this stage comprises: (i) the construction of the reference trip from the official WLTC Class 3b trace of UN GTR 15 [21] and the derivation of the bus load trajectory through the longitudinal dynamics of Eqs. (3)–(4); (ii) the identification of the eight GSSEM coefficients from the published polarization behaviour of the Mirai II stack [17] using particle swarm optimization following the methodology surveyed by Fang et al. [7]; (iii) the implementation of the two-layer simulation environment — a high-fidelity plant layer combining the identified stack model with the full 1-RC + hysteresis battery model, and a controller layer restricted to the efficiency look-up table and the Rint model, as planned in Section 3.7 of GP1 following the two-level approach of Onori et al. [14]; (iv) the implementation of the four strategies and their closed-loop execution against the plant; and (v) the comparison and sensitivity studies. Component degradation costs and thermal dynamics remain outside the scope, as fixed in GP1.'));
body.push(para(
  'The outputs can be used as a directly transferable basis for supervisory control software of plug-in fuel cell passenger cars and, with modified parameter sets, of fuel cell city buses and light commercial vehicles. Because every architectural claim of GP1 is now backed by a measured number (optimality gaps, computation times, protection-layer overhead), the results also serve as a quantitative feasibility reference for the European market scenarios considered.'));

// 3 ---------------------------------------------------------------------------
body.push(h1('3. Conducted Studies'));

body.push(h2('3.1. Simulation Environment'));
body.push(para(
  'The simulation environment is implemented in Python 3 using only NumPy and Matplotlib. The deliberate restriction to two dependencies eliminates installation friction and version decay; it is made possible by the scalar-state structure of the problem, which allows both the dynamic programming recursion and the identification to be expressed as vectorized array operations. The environment is organized in strictly separated modules, each implementing one block of the GP1 formulation; the mapping is given in Table 1.'));
body.push(table(
  ['Module', 'Implements', 'GP1 reference'],
  [
    ['config.py', 'all physical constants, vehicle/component parameters, price scenarios, solver settings', 'Tables 1–3'],
    ['drive_cycle.py', 'longitudinal dynamics and load trajectory', 'Eqs. (3)–(4)'],
    ['fuel_cell.py', 'Mann–Amphlett GSSEM, Faraday hydrogen flow, efficiency LUT', 'Eqs. (5)–(11)'],
    ['param_id.py', 'PSO identification of the stack coefficients', 'Sec. 3.3.2 / 3.7'],
    ['battery.py', 'plant model (1-RC + hysteresis) and controller model (Rint)', 'Eqs. (12)–(15), (17)–(18)'],
    ['cost_model.py', 'power-flow chain, monetary running cost, SoC reference', 'Eqs. (16), (19)–(23)'],
    ['ems/dp.py, aecms.py, mpc.py, blfs.py', 'the four strategies', 'Eqs. (27)–(31)'],
    ['simulate.py', 'two-layer closed-loop execution and metric accounting', 'Sec. 3.7'],
  ],
  [2200, 4826, 2000]));
body.push(caption('Table 1 Mapping of the simulation modules to the GP1 formulation.'));
body.push(para(
  'The two-layer separation is methodologically essential: the controller layer never has access to the plant states (relaxation voltage, hysteretic OCV) and reasons exclusively with the simplified Rint model and the stack efficiency look-up table, exactly as an embedded controller would in a real vehicle. Every number reported in Section 3.7 of this report is produced by the plant layer, so the reported performance honestly includes the cost of controller model mismatch. For the DP benchmark this mismatch is directly measurable: the backward-pass prediction of the optimal cost is 2.733 EUR, whereas the closed-loop realization against the plant is 2.718 EUR, a 0.5% agreement that simultaneously validates both models.'));

body.push(h2('3.2. Drive Cycle and Load Trajectory'));
body.push(para(
  'The speed profile is the official 1 Hz WLTC Class 3b trace of UN GTR 15 [21] (1801 samples, 23.27 km, v_max = 131.3 km/h), checksum-verified against the regulation. Two consecutive cycles are concatenated, dropping the duplicated standstill sample at the seam, giving the reference trip of N = 3600 decision points and 46.53 km. Evaluating Eqs. (3)–(4) with the Table 2 (GP1) vehicle parameters over the trip yields a peak traction demand of 54.4 kW, a peak regeneration of −36.3 kW, a total traction energy of 8.56 kWh and a recoverable braking energy of 2.13 kWh (Figure 1). The acceleration is evaluated by the forward difference consistent with the zero-order hold on the decision variable, and the rolling-resistance force is masked at standstill.'));
body.push(para(
  'The net electrical demand of approximately 6.4 kWh exceeds the usable battery budget of (0.90−0.25)·7.92 = 5.15 kWh; a battery-only replay of the trip terminates at SoC = 0.053, far below the SoC window. The problem is therefore not degenerate: fuel-cell operation is strictly necessary, and the optimization question is when and at which power the fuel cell should supply its share.'));
body.push(...figure('fig01_cycle_load.png', 600, 650 / 1170,
  'Figure 1 Speed profile and bus load trajectory of the reference trip (2×WLTC Class 3b, official UN GTR 15 trace).'));

body.push(h2('3.3. Stack Parameter Identification by PSO'));
body.push(para(
  'The GSSEM with the nominal coefficient set of Mann et al. [6] does not represent the Mirai II stack: it predicts a peak gross power of 50.9 kW against the actual 128 kW and an LHV efficiency of 0.51 at 12 kW against the measured ≈0.70 [17]. This confirms quantitatively the necessity of the re-identification announced in GP1 Section 3.3.2. The identification target is a 35-point polarization data set reconstructed from the published Mirai II operating anchors of [17] (open-circuit ≈0.95–0.98 V; η ≈ 0.70 near 12 kW gross, i.e. V_cell = 0.878 V; η ≈ 0.54 at 128 kW, i.e. V_cell = 0.677 V at J ≈ 1.91 A/cm²), completed between the anchors with the canonical shape of a high-power-density automotive stack and perturbed with seeded Gaussian measurement noise of σ = 3 mV so that the identification problem is realistic. The pipeline is data-agnostic: if the digitized experimental curve becomes available, replacing one CSV file reruns the entire study unchanged.'));
body.push(para(
  'The decision vector θ = [ξ₁, ξ₂, ξ₃, ξ₄, λ, R_C, β, J_max] is identified by minimizing the root-mean-square polarization error. The objective is non-convex — ξ₁ acts as a pure offset while ξ₃ multiplies ln(C*O₂), producing long correlated valleys, and λ and R_C are nearly redundant at low current density — which motivates a population-based method; PSO is the reference method of the fuel-cell identification literature [7], [25]. The canonical global-best PSO with the Clerc constriction coefficients w = 0.7298, c₁ = c₂ = 1.4962 [26] is used with 40 particles and 150 iterations, velocity clamped to 20% of the box width [27], reflecting boundary handling, and a physicality penalty on non-positive cell voltages. Search bounds follow the ranges surveyed in [7] and are listed with the identified values in Table 2.'));
body.push(table(
  ['Parameter', 'Lower bound', 'Upper bound', 'Identified'],
  [
    ['ξ₁ [V]', '−1.20', '−0.80', '−1.0764'],
    ['ξ₂ [V/K]', '1.0·10⁻³', '5.0·10⁻³', '3.557·10⁻³'],
    ['ξ₃ [V/K]', '3.6·10⁻⁵', '9.8·10⁻⁵', '6.122·10⁻⁵'],
    ['ξ₄ [V/K]', '−2.6·10⁻⁴', '−0.9·10⁻⁴', '−1.061·10⁻⁴'],
    ['λ (water content) [-]', '10', '24', '23.92'],
    ['R_C [Ω]', '1.0·10⁻⁵', '8.0·10⁻⁴', '5.00·10⁻⁵'],
    ['β (concentration) [V]', '0.01', '0.20', '0.010'],
    ['J_max [A/cm²]', '2.35', '3.00', '2.981'],
  ],
  [3200, 1800, 1800, 2226]));
body.push(caption('Table 2 PSO search bounds [7] and identified GSSEM coefficients for the Mirai II stack (RMSE = 6.4 mV over 35 points).'));
body.push(para(
  'The identified model fits the data with an RMSE of 6.4 mV — approximately twice the injected noise floor, indicating a good fit without over-fitting — and reproduces the Mirai II system anchors: peak gross power 138 kW, η(12 kW) = 0.703, η(128 kW) = 0.52 (Figure 2). The identified water content λ = 23.9 and limiting current density J_max = 2.98 A/cm² are physically consistent with a well-humidified, high-power-density automotive stack. Because the hydrogen mass flow follows exactly from Faraday’s law, the LHV stack efficiency is proportional to the cell voltage (η = V_cell/1.254 V), so the identified polarization curve directly generates the one-dimensional consumption look-up table of Eq. (11); only the monotonically increasing branch of P(J) is retained, which keeps the table invertible (Figure 3).'));
body.push(...figure('fig02_polarization_pso.png', 600, 468 / 1170,
  'Figure 2 Polarization-curve fit of the identified GSSEM (red), nominal Mann coefficient set (blue, for contrast) and PSO convergence history.'));
body.push(...figure('fig03_efficiency_map.png', 460, 468 / 780,
  'Figure 3 Stack LHV efficiency and tank-to-bus system efficiency (including DC/DC and auxiliary losses); the interior system peak defines the BLFS recharge operating point.'));

body.push(h2('3.4. Component Model Implementation'));
body.push(para(
  'Battery. The plant battery implements the full model of Eqs. (12)–(15): Coulomb counting with η_i = 0.995, the RC relaxation state with τ₁ = 180 s, and the hysteretic open-circuit voltage relaxing towards the direction-dependent branch with rate m_hyst = 150 per unit of charge throughput, following Huria et al. [12]. The charge and discharge OCV branches of the A123 ANR26650M1B cell are represented by 8th-order polynomials in SoC as in Nejad et al. [11] and scaled to the 96s10p pack (Figure 4). Terminal power is converted to current through the quadratic relation of Eq. (17), whose discriminant naturally encodes the pack power capability; in addition the data-sheet current limits (4C continuous charge, 20C continuous discharge) are enforced, and regenerative power beyond the admissible charging power is diverted to the friction brakes without monetary credit.'));
body.push(para(
  'A modelling refinement proved necessary at the SoC ceiling: without it, any regeneration event occurring near SoC_max renders the upper boundary of the DP state grid spuriously infeasible, and the resulting infinite costs contaminate the interior of the value function through the linear interpolation. Physically, the battery management system tapers the charging current so that the window is never violated, with the excess again dissipated in the friction brakes; this charge curtailment is therefore modelled inside the stage cost, which restores feasibility of the entire grid without artificial penalties.'));
body.push(para(
  'Auxiliaries. GP1 quotes the auxiliary consumption of the Mirai II as a fixed fraction P_aux/P_gross ≈ 0.10–0.13 [17]. A strictly proportional auxiliary load, however, makes the tank-to-bus efficiency monotone in power, which would eliminate the interior optimum operating point of the fuel cell, contradicting the measured system efficiency peak of the Mirai near 12 kW [17]. The implementation therefore uses the affine model P_aux = 1.0 kW + 0.09·P_gross (fuel cell on), which stays inside the quoted ratio band above ≈30 kW and reproduces the interior peak visible in Figure 3.'));
body.push(...figure('fig04_ocv_hysteresis.png', 460, 468 / 780,
  'Figure 4 LFP open-circuit-voltage charge/discharge branches (8th-order polynomials [11]), hysteresis band and SoC operating window.'));

body.push(h2('3.5. Implementation of the EMS Strategies'));
body.push(h3('3.5.1. Dynamic Programming benchmark'));
body.push(para(
  'The Bellman recursion of Eq. (27) is evaluated on the grids specified in GP1 (ΔSoC = 0.005, i.e. 151 state nodes; ΔP_dc = 1 kW, i.e. 105 decisions) following the implementation structure of Sundström and Guzzella [15]: the cost-to-go at the successor state is obtained by linear interpolation between grid nodes, which suppresses the quantization chattering of nearest-node assignment, and infeasible transitions below SoC_min receive infinite cost (the upper bound being handled by the charge curtailment of Section 3.4). The full transition and cost tensor of each time step is evaluated in a single vectorized pass, so the complete backward recursion over 3600 steps executes in 2.5 s — the concrete payoff of the static stack model selected in GP1 Section 3.1.2. The backward pass produces a policy table u*(k, SoC); the forward pass replays this policy in closed loop against the plant, with the control interpolated between the two neighbouring SoC nodes.'));
body.push(h3('3.5.2. Adaptive ECMS'));
body.push(para(
  'At every step the Hamiltonian of Eq. (28) is minimized pointwise over the 1 kW decision grid, with the equivalence factor adapted by the PI law of Eq. (29). Two implementation decisions follow the plug-in character of the problem: first, since the running cost already prices battery energy at its grid-equivalent monetary value (Eq. 21), the economic trade-off is fully contained in the stage cost and the baseline s₀ is set to zero — the adaptive term performs pure reference tracking, which also removes the constant-factor pathology demonstrated by Xu et al. [4]; second, the integrator is clamped (anti-windup) to prevent the end-of-trip burst that occurs when the terminal constraint saturates the actuator. The gains were tuned over the default scenario: (k_p, k_i) = (60, 0.1) tracked too loosely (total 3.198 EUR), (300, 0.5) chattered (3.144 EUR), and (150, 0.3) was selected (2.783 EUR).'));
body.push(h3('3.5.3. Model Predictive Control'));
body.push(para(
  'MPC solves at every instant the finite-horizon restriction of Eq. (30) with N_p = 15 s under the constant-load assumption, applies the first move and repeats. GP1 sketched a quadratic-programming transcription; during implementation this was replaced by an exact local dynamic program over the horizon, for two reasons documented in the code: the stage cost is non-convex in P_dc (the hydrogen map inherits the curvature of the identified polarization curve, and the direction-dependent battery efficiency of Eq. (20) introduces a kink at P_bat = 0), so a QP could only solve a convex surrogate; and the scalar state makes exhaustive local search cheap — the SoC can move at most ≈0.002 per second, hence a ±0.03 window (31 local nodes) covers every trajectory the horizon can reach, and the subproblem is solved exactly on a 2 kW decision grid in 0.6 ms per step.'));
body.push(para(
  'The constant-load assumption is systematically biased: during traction peaks the controller believes the peak will persist over the whole horizon and over-protects the battery, firing the fuel cell precisely when the depletion opportunity is largest. The resulting persistent SoC offset cannot be removed by any finite terminal weight — sweeping γ_MPC from 200 to 5000 left the terminal SoC unchanged at ≈0.277 — which identifies it as the classical offset problem of model predictive control. The standard remedy, integral action on the tracking error in the sense of offset-free MPC [32], shifts the tracked reference by the low-pass accumulated bias; the gain β = 0.005 was selected by a sweep (β = 0 → 3.013 EUR; 0.005 → 2.746 EUR; 0.01 → 3.011 EUR; 0.02 → 3.220 EUR).'));
body.push(h3('3.5.4. Boundary Layer Surface Following'));
body.push(para(
  'BLFS is implemented as a wrapper around either real-time strategy, exactly as specified in GP1 Section 3.6.5: above the ±0.05 hysteresis band around the SoC reference the fuel cell is held at minimum power, below the band it is held at the peak system-efficiency point (the maximizer of the tank-to-bus efficiency, computed once from the identified look-up table), and inside the band the upper-level command passes through. The fuel-cell load ramp is limited to 5 kW/s (Eq. 31), enforced on the bus-side command; since the map between P_dc and P_fc,gross is smooth and monotone, this implies an (even slightly stricter) gross-side bound.'));

body.push(h2('3.6. Documented Deviations from the GP1 Formulation'));
body.push(para(
  'Faithfulness to the GP1 formulation was the guiding principle of the implementation; the four points where the implementation deviates are summarized in Table 6 together with their justification. The most consequential one concerns the SoC reference of Eq. (29): a reference linear in time proved untrackable in closed loop, because during idle phases and the final deceleration there is no traction load and the battery physically cannot be depleted while the reference keeps falling. All real-time strategies then end the trip stranded 0.02–0.03 above the target and collect a terminal penalty of 0.5–0.8 EUR that reflects the reference design rather than the strategy quality (development measurements: A-ECMS terminal SoC 0.227 with penalty 0.51 EUR; MPC 0.275). Following the standard practice of the plug-in literature (cf. Onori et al. [14], Ch. 6), the reference was made linear in cumulative positive traction energy — the exact measure of the depletion opportunity available up to time k — computed offline from the known cycle, i.e. under the same standing assumption the DP benchmark already makes.'));
body.push(table(
  ['GP1 formulation', 'Implemented as', 'Reason'],
  [
    ['digitized polarization data of [17]', 'representative 35-point set reconstructed from the published anchors of [17]', 'raw digitized data unavailable; pipeline is data-agnostic (one CSV swap)'],
    ['P_aux as fixed fraction of P_gross', 'affine model 1 kW + 0.09·P_gross', 'fixed ratio destroys the interior system-efficiency peak measured in [17]'],
    ['SoC reference linear in time (Eq. 29)', 'linear in cumulative positive traction energy', 'time-linear reference untrackable during idle/final deceleration'],
    ['MPC transcribed to a QP', 'exact local grid DP over the horizon + offset-free integral correction [32]', 'stage cost non-convex; scalar state makes exact search cheap (0.6 ms/step)'],
  ],
  [2800, 3226, 3000]));
body.push(caption('Table 6 Documented deviations from the GP1 formulation and their justification.'));

body.push(h2('3.7. Results and Comparison'));
body.push(para(
  'Table 3 compares the five controllers under the default scenario (11 EUR/kg H₂, 0.35 EUR/kWh) over the 46.53 km reference trip, all metrics produced by the plant layer. The expected hierarchy is confirmed: the DP benchmark is cheapest at 2.718 EUR per trip, the real-time strategies follow within a 1–3% optimality gap — MPC at +1.0% and A-ECMS at +2.4% — consistent with the gaps reported in the comparative literature [29]. All strategies deplete the battery budget almost completely (5.08–5.15 kWh) and burn 78–81 g of hydrogen; as anticipated in GP1 Section 3.5.2, grid electricity is uniformly cheaper than hydrogen in this scenario, so the fuel cell supplies only the energy deficit that the battery budget cannot cover, and the entire difference between the strategies lies in the timing and power level of that supply (Figures 5 and 6).'));
body.push(table(
  ['Strategy', 'Total [EUR]', 'Gap to DP', 'Running [EUR/100 km]', 'H₂ [g]', 'Electricity [kWh]', 'Terminal SoC', 'FC on/off', 'CPU [ms/step]'],
  [
    ['DP (benchmark)', '2.718', '—', '5.84', '77.6', '5.15', '0.249', '85', '0.016'],
    ['MPC', '2.746', '+1.0%', '5.85', '79.5', '5.11', '0.255', '64', '0.59'],
    ['MPC+BLFS', '2.752', '+1.2%', '5.86', '80.0', '5.11', '0.255', '50', '0.60'],
    ['A-ECMS', '2.783', '+2.4%', '5.85', '80.3', '5.09', '0.258', '154', '0.21'],
    ['A-ECMS+BLFS', '2.795', '+2.8%', '5.86', '80.8', '5.08', '0.258', '54', '0.25'],
  ],
  [1600, 900, 800, 1400, 700, 1100, 900, 800, 826]));
body.push(caption('Table 3 Strategy comparison under the default price scenario (Germany 2026: 11 EUR/kg H₂, 0.35 EUR/kWh); all quantities measured on the plant model.'));
body.push(para(
  'Three observations deserve emphasis. First, the BLFS protection layer costs only 0.2–0.4% in total cost while reducing the number of fuel-cell on/off events from 154 to 54 (under A-ECMS) and from 64 to 50 (under MPC) and halving the mean load ramp — the durability protection announced in GP1 is obtained at a nearly negligible monetary premium. Second, all per-step computation times are far below the 1 s real-time budget (A-ECMS 0.21 ms, MPC 0.60 ms), quantitatively confirming the real-time capability classification of GP1 Table 4, while the DP policy lookup (0.016 ms) remains an offline benchmark only because its backward pass requires the full future load. Third, the running cost of ≈5.9 EUR/100 km compares favourably with a hydrogen-only operation of the same vehicle (≈8 EUR/100 km at the same prices), which is the economic justification of the plug-in architecture itself.'));
body.push(...figure('fig05_soc_trajectories.png', 600, 546 / 1170,
  'Figure 5 Charge-depleting SoC trajectories of the five controllers against the energy-based reference (plant model).'));
body.push(...figure('fig06_pdc_profiles.png', 560, 1170 / 1170,
  'Figure 6 Fuel-cell bus power commands P_dc(t); the load trajectory is shaded in grey. Note the concentration of fuel-cell operation near the reference-approach segments and the visibly smoother commands under BLFS.'));
body.push(...figure('fig07_cost_breakdown.png', 520, 494 / 910,
  'Figure 7 Total trip cost decomposition under the default scenario: hydrogen (Eq. 19), grid electricity (Eq. 21) and terminal penalty (Eq. 23).'));

body.push(h2('3.8. Sensitivity Analyses'));
body.push(para(
  'Price scenarios. Table 4 and Figure 8 report the total trip cost of the five controllers under the three Germany 2026 scenarios of GP1 Table 3. In all three scenarios grid electricity remains cheaper than hydrogen on a per-kWh basis, so the optimal policy structure is unchanged — maximum battery utilization with the fuel cell covering the deficit — and the costs scale with the prices while the strategy ranking is preserved. Hydrogen consumption varies by only ±2% across the scenarios: the policy is insensitive to the price ratio in this regime because the binding constraint is the battery energy budget, not the relative prices. A structural change of the optimal policy would only occur when hydrogen becomes competitive with grid electricity per delivered kWh (approximately M_H2 ≈ 8 EUR/kg against M_ele ≈ 0.26 EUR/kWh at the realized path efficiencies), which lies outside the scenario band.'));
body.push(table(
  ['Scenario', 'M_H2 [EUR/kg]', 'M_ele [EUR/kWh]', 'DP', 'MPC', 'MPC+BLFS', 'A-ECMS', 'A-ECMS+BLFS'],
  [
    ['High', '13.85', '0.40', '3.203', '3.228', '3.230', '3.242', '3.251'],
    ['Default', '11.00', '0.35', '2.718', '2.746', '2.752', '2.783', '2.795'],
    ['Low', '8.00', '0.32', '2.325', '2.361', '2.360', '2.431', '2.445'],
  ],
  [1300, 1300, 1400, 1000, 1000, 1100, 1000, 926]));
body.push(caption('Table 4 Price-scenario sensitivity: total trip cost [EUR] of the five controllers (Germany 2026 scenarios of GP1 Table 3).'));
body.push(...figure('fig08_sensitivity.png', 560, 494 / 1040,
  'Figure 8 Price-scenario sensitivity of the total trip cost; the strategy ranking is preserved in all scenarios.'));
body.push(para(
  'Terminal penalty weight. Table 5 and Figure 9 sweep the weight γ of Eq. (23) on the DP benchmark. Below γ ≈ 300 the controller literally buys out the penalty and misses the target (terminal SoC 0.2395 at γ = 100); above γ ≈ 3000 the terminal error no longer improves while the running cost stiffens. The value γ = 1000 selected in GP1 by dimensional reasoning sits exactly at the knee — terminal error below 0.001 at essentially unchanged running cost — so the GP1 choice is confirmed experimentally.'));
body.push(table(
  ['γ [EUR]', '100', '300', '1000', '3000', '10000'],
  [
    ['Terminal SoC', '0.2395', '0.2449', '0.2494', '0.2495', '0.2495'],
    ['Running cost [EUR]', '2.694', '2.706', '2.717', '2.721', '2.726'],
  ],
  [2400, 1320, 1320, 1320, 1320, 1346]));
body.push(caption('Table 5 Terminal-penalty weight sweep on the DP benchmark; γ = 1000 EUR (GP1 choice) sits at the knee of the trade-off.'));
body.push(...figure('fig09_gamma_sweep.png', 460, 468 / 780,
  'Figure 9 DP sensitivity to the terminal penalty weight γ (log scale).'));

body.push(h2('3.9. Verification and Reproducibility'));
body.push(para(
  'Six independent checks support the validity of the results. (i) The reconstructed trip length (46.53 km) and traction energy (8.56 kWh, i.e. 184 Wh/km) match the official cycle definition and typical D-segment electric consumption. (ii) The battery energy balance closes: a 10 kW, 10-minute discharge changes the SoC by exactly the delivered charge within 0.3%, and the full-trip battery-only replay reconciles the SoC decrement with the integrated terminal power. (iii) The DP backward-pass prediction agrees with the closed-loop plant realization within 0.5%. (iv) No real-time strategy outperforms the DP benchmark in any scenario — a necessary condition that would expose an implementation error if violated. (v) The PSO improves by less than 0.1 mV over its final 60 iterations and its residual sits at twice the injected noise floor, indicating convergence without over-fitting. (vi) The complete pipeline is bit-exact reproducible: rerunning the identification and the DP benchmark from scratch reproduces the cached parameters to machine precision and the total cost of 2.71767 EUR exactly.'));

// 4 ---------------------------------------------------------------------------
body.push(h1('4. Conclusions and Future Work'));
body.push(para(
  'The optimal control problem formulated in MAT 4901E has been solved numerically in full. The two-layer Python environment reproduces the physics selected in GP1; the PSO identification transfers the generic Mann–Amphlett model to the Mirai II stack with a 6.4 mV polarization residual; and the four strategies behave exactly as the GP1 qualitative comparison (Table 4 of GP1) predicted, now with measured numbers attached: DP provides the 2.718 EUR benchmark, MPC and A-ECMS operate within 1.0% and 2.4% of it at 0.6 ms and 0.2 ms per step respectively, and BLFS buys a threefold reduction of fuel-cell cycling for a 0.2–0.4% cost premium. The plug-in economics anticipated in GP1 Section 3.5 are confirmed: under all three price scenarios the optimal policy depletes the battery budget completely and uses the fuel cell only to cover the energy deficit, at a running cost near 5.9 EUR/100 km.'));
body.push(para(
  'Beyond the planned scope, the implementation surfaced three findings of independent interest, each traced to its theoretical root and resolved with a documented, literature-backed remedy: the untrackability of a time-linear charge-depleting reference (resolved by an energy-based reference), the spurious infeasibility of the DP state-grid ceiling under regeneration (resolved by modelling the BMS charge curtailment inside the stage cost), and the persistent SoC offset of constant-load MPC (resolved by offset-free integral action [32]).'));
body.push(para(
  'Future work follows three directions. First, replacing the constant-load MPC prediction by a navigation-based speed preview would close most of the remaining 1.0% gap to DP. Second, augmenting the cost functional with fuel-cell and battery degradation terms [20] would allow the BLFS protection heuristics to be replaced by an explicit durability–cost trade-off. Third, identifying the stack from the actual digitized polarization data of [17] and validating the battery polynomials against cell measurements would complete the experimental grounding of the parameter set; the pipeline requires no structural change for either step.'));

// 5 ---------------------------------------------------------------------------
body.push(h1('5. References'));
const refs = [
  '[1] Khalatbarisoltani, A., Kandidayeni, M., Boulon, L., & Hu, X. (2024). Energy management strategies for fuel cell vehicles: A comprehensive review. IEEE Transactions on Intelligent Transportation Systems, 25(1), 14–32.',
  '[2] Sciarretta, A., & Guzzella, L. (2007). Control of hybrid electric vehicles. IEEE Control Systems Magazine, 27(2), 60–70.',
  '[3] Paganelli, G., Delprat, S., Guerra, T. M., Rimaux, J., & Santin, J. J. (2002). Equivalent consumption minimization strategy for parallel hybrid powertrains. IEEE Vehicular Technology Conference, 2076–2081.',
  '[4] Xu, L., Ouyang, M., Li, J., Yang, F., Lu, L., & Hua, J. (2013). Application of Pontryagin’s Minimal Principle to the energy management strategy of plugin fuel cell electric vehicles. International Journal of Hydrogen Energy, 38(24), 10104–10115.',
  '[5] Gao, J., Li, Y., Liu, Y., & Li, X. (2021). Adaptive real-time optimal energy management strategy based on equivalent factors optimization for hybrid fuel cell system. International Journal of Hydrogen Energy, 46, 4329–4338.',
  '[6] Mann, R. F., Amphlett, J. C., Hooper, M. A. I., Jensen, H. M., Peppley, B. A., & Roberge, P. R. (2000). Development and application of a generalised steady-state electrochemical model for a PEM fuel cell. Journal of Power Sources, 86(1–2), 173–180.',
  '[7] Fang, Y., Yang, F., Xing, Y., Zhang, X., Wang, W., & Lin, S. (2026). A comparative review of modeling and metaheuristic parameter identification strategies for zero-dimensional PEMFC polarization models. Energies, 19, 1438.',
  '[8] Springer, T. E., Zawodzinski, T. A., & Gottesfeld, S. (1991). Polymer electrolyte fuel cell model. Journal of the Electrochemical Society, 138, 2334–2342.',
  '[9] Kim, J., Lee, S., Srinivasan, S., & Chamberlin, C. E. (1995). Modeling of proton-exchange membrane fuel-cell performance with an empirical equation. Journal of the Electrochemical Society, 142, 2670–2674.',
  '[10] Ziogou, C., Voutetakis, S., Papadopoulou, S., & Georgiadis, M. C. (2011). Modeling, simulation and experimental validation of a PEM fuel cell system. Computers & Chemical Engineering, 35, 1886–1900.',
  '[11] Nejad, S., Gladwin, D. T., & Stone, D. A. (2016). A systematic review of lumped-parameter equivalent circuit models for real-time estimation of lithium-ion battery states. Journal of Power Sources, 316, 183–196.',
  '[12] Huria, T., Ludovici, G., & Lutzemberger, G. (2014). State of charge estimation of high power lithium iron phosphate cells. Journal of Power Sources, 249, 92–102.',
  '[13] Plett, G. L. (2004). Extended Kalman filtering for battery management systems of LiPB-based HEV battery packs — Part 3: State and parameter estimation. Journal of Power Sources, 134, 277–292.',
  '[14] Onori, S., Serrao, L., & Rizzoni, G. (2016). Hybrid electric vehicles: Energy management strategies. Springer.',
  '[15] Sundström, O., & Guzzella, L. (2009). A generic dynamic programming Matlab function. IEEE Control Applications & Intelligent Control, 1625–1630.',
  '[16] Bertsekas, D. P. (2005). Dynamic programming and optimal control (3rd ed.). Athena Scientific.',
  '[17] Energy balance and hydrogen exhaust emissions of the second-generation Toyota Mirai. (2025). International Journal of Hydrogen Energy.',
  '[18] Hu, X., Murgovski, N., Johannesson, L. M., & Egardt, B. (2013). Energy efficiency analysis of a series plug-in hybrid electric bus with different energy management strategies and battery sizes. Applied Energy, 111, 1001–1009.',
  '[19] Tribioli, L., Cozzolino, R., Chiappini, D., & Iora, P. (2016). Energy management of a plug-in fuel cell/battery hybrid vehicle with on-board fuel processing. Applied Energy, 184, 140–154.',
  '[20] Kandidayeni, M., Macias, A., Boulon, L., & Kelouwani, S. (2020). Investigating the impact of ageing and thermal management of a fuel cell system on energy management strategies. Applied Energy, 274, 115293.',
  '[21] United Nations Economic Commission for Europe. (2022). UN Global Technical Regulation No. 15: Worldwide harmonized Light vehicles Test Procedure (WLTP) (ECE/TRANS/WP.29/2022/42/Rev.1).',
  '[22] Toyota Motor Corporation. (2022). Toyota Mirai technical specifications. Toyota (GB) Media Site.',
  '[23] H2 MOBILITY Deutschland GmbH. (2026). H2.LIVE: Hydrogen stations in Germany and Europe — fuel pricing. https://h2.live/en/',
  '[24] BDEW Bundesverband der Energie- und Wasserwirtschaft. (2026). BDEW-Strompreisanalyse Januar 2026.',
  '[25] Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. Proceedings of ICNN’95, Vol. 4, 1942–1948. IEEE.',
  '[26] Clerc, M., & Kennedy, J. (2002). The particle swarm — explosion, stability, and convergence in a multidimensional complex space. IEEE Transactions on Evolutionary Computation, 6(1), 58–73.',
  '[27] Shi, Y., & Eberhart, R. (1998). A modified particle swarm optimizer. IEEE International Conference on Evolutionary Computation, 69–73.',
  '[28] Musardo, C., Rizzoni, G., Guezennec, Y., & Staccia, B. (2005). A-ECMS: An adaptive algorithm for hybrid electric vehicle energy management. European Journal of Control, 11(4–5), 509–524.',
  '[29] Serrao, L., Onori, S., & Rizzoni, G. (2011). A comparative analysis of energy management strategies for hybrid electric vehicles. Journal of Dynamic Systems, Measurement, and Control, 133(3), 031012.',
  '[30] Kim, N., Cha, S., & Peng, H. (2011). Optimal control of hybrid electric vehicles based on Pontryagin’s minimum principle. IEEE Transactions on Control Systems Technology, 19(5), 1279–1287.',
  '[31] Rawlings, J. B., Mayne, D. Q., & Diehl, M. (2017). Model predictive control: Theory, computation, and design (2nd ed.). Nob Hill Publishing.',
  '[32] Pannocchia, G., & Rawlings, J. B. (2003). Disturbance models for offset-free model-predictive control. AIChE Journal, 49(2), 426–437.',
  '[33] Borhan, H., Vahidi, A., Phillips, A. M., Kuang, M. L., Kolmanovsky, I. V., & Di Cairano, S. (2012). MPC-based energy management of a power-split hybrid electric vehicle. IEEE Transactions on Control Systems Technology, 20(3), 593–603.',
  '[34] Guzzella, L., & Sciarretta, A. (2013). Vehicle propulsion systems: Introduction to modeling and optimization (3rd ed.). Springer.',
];
refs.forEach(r => body.push(para(r, { para: { alignment: AlignmentType.LEFT,
  spacing: { after: 140 } } })));

// ---------- document ---------------------------------------------------------
const header = new Header({
  children: [new Paragraph({
    tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '999999' } },
    children: [
      new TextRun({ text: 'Mathematical Engineering Design', size: 18, color: '555555' }),
      new TextRun({ text: '\t', size: 18 }),
      new TextRun({ children: [PageNumber.CURRENT], size: 18, color: '555555' }),
    ],
  })],
});

const doc = new Document({
  features: { updateFields: true },
  styles: { default: { document: { run: { font: 'Calibri', size: 22 } } } },
  sections: [
    { properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: titleChildren },
    { properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      headers: { default: header },
      children: [...frontMatter, ...body] },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log('written:', OUT, buf.length, 'bytes');
});
