# MAT 4901E — Graduation Project I: Modelling and Formulation

**Mathematical Modeling & Control Strategies for Hybrid Hydrogen Systems**
Submitted 14 June 2026 · Ahmet Yeşil (090220359) · Supervisor: Prof. Dr. Semra Ahmetolan

This stage **sets up the problem mathematically**: longitudinal vehicle dynamics, the
Mann–Amphlett GSSEM model of the PEMFC stack, battery equivalent-circuit models
(1-RC with hysteresis), the power flow model and the monetary cost functional are
derived; the problem is then stated as a finite-horizon optimal control problem and the
solution strategies (DP, A-ECMS, MPC, BLFS) are justified. The numerical solution lives
in [`../project2-simulation/`](../project2-simulation/).

## Contents

| File | Description |
|---|---|
| **`report/MAT4901E_Report.pdf`** | **Submitted final report** (22 pages) |
| `report/drafts/` | Earlier versions (`_v1`, `_v2`; PDF and editable .docx sources) |
| `presentation/presentation.tex` | Defence presentation — Beamer source (TikZ/pgfplots, no external figures needed) |
| `presentation/FCHEV_Presentation.pptx` | PowerPoint version of the talk |
| `figures/` | WLTP speed profile and OCV–SoC flat-zone figures |
| `references/` | List of the 22 sources used (PDFs not redistributed — see the folder README) |

## Report outline

1. Definition and purpose of the design
2. Scope of the design and areas of usage
3. Conducted studies — literature review (EMS strategies, PEMFC and Li-ion modelling),
   system architecture with the reference vehicle and drive cycle, mathematical modelling
   of the powertrain components, power flow model, derivation of the cost function,
   EMS methods (DP, A-ECMS, MPC, BLFS), and the work plan for Graduation Project II
4. References (24 entries)

## Building the presentation

```bash
cd presentation
pdflatex -shell-escape presentation.tex   # run twice
```
