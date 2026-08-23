"""
config.py — Central parameter file for the MAT 4902E FCHEV simulation.

Every physical constant, vehicle parameter, component rating, price scenario
and solver setting used anywhere in the project is defined HERE and only here,
so that a single edit propagates consistently through all modules.

All values are taken from the MAT 4901E report (Tables 1-3) and its primary
sources:
  [6]  Mann et al. 2000   - GSSEM PEMFC model
  [11] Nejad et al. 2016  - 1-RC + hysteresis battery parameters
  [12] Huria et al. 2014  - hysteresis law
  [17] Mirai II energy-balance paper (stack data, auxiliaries)
  [22] Toyota Mirai technical specifications
  [23] H2.LIVE, [24] BDEW - Germany 2026 price scenarios
"""
import numpy as np

# ----------------------------------------------------------------------------
# 1. Physical constants
# ----------------------------------------------------------------------------
FARADAY   = 96485.0        # C/mol       - Faraday constant
R_GAS     = 8.314          # J/(mol K)   - universal gas constant
M_H2      = 2.016e-3       # kg/mol      - molar mass of H2
LHV_H2    = 120.0e6        # J/kg        - lower heating value of hydrogen
G_GRAV    = 9.81           # m/s^2

# ----------------------------------------------------------------------------
# 2. Vehicle (2nd-gen Toyota Mirai, Table 2 of the MAT4901E report [17],[22])
# ----------------------------------------------------------------------------
VEH = dict(
    mass      = 1925.0,    # kg   total incl. driver
    Af        = 2.547,     # m^2  frontal area
    Cd        = 0.29,      # -    aerodynamic drag coefficient
    Cr        = 0.012,     # -    rolling resistance coefficient
    rho_air   = 1.18,      # kg/m^3 at 20 C
    eta_dt    = 0.92,      # -    drivetrain (motor+inverter+gear) efficiency
    Pm_max    = 134.0e3,   # W    maximum motor power
)

# ----------------------------------------------------------------------------
# 3. PEMFC stack (Mirai II FCB130 [17]) - Mann-Amphlett GSSEM structure [6]
#    The xi coefficients below are only INITIAL values (from Mann et al.);
#    the values actually used in the simulation are re-identified by PSO in
#    param_id.py and stored in data/identified_stack_params.json.
# ----------------------------------------------------------------------------
FC = dict(
    N_cell    = 330,       # -    cells in series
    A_cell    = 300.0,     # cm^2 active area
    T_stack   = 343.0,     # K    isothermal operating temperature (70 C)
    p_H2      = 1.5,       # atm  anode H2 partial pressure
    p_O2      = 0.21*2.0,  # atm  cathode O2 partial pressure (2 atm air)
    # Mann et al. [6] nominal coefficient set (starting point for PSO):
    xi1       = -0.948,
    xi2       = 0.00312,   # placeholder: full expression handled in fuel_cell.py
    xi3       = 7.6e-5,
    xi4       = -1.93e-4,
    lam_w     = 18.0,      # -    effective membrane water content (14..23)
    R_C       = 1.0e-4,    # ohm  contact resistance
    l_mem     = 51e-4,     # cm   membrane thickness (Nafion, ~51 um)
    beta_con  = 0.05,      # V    concentration-loss coefficient (identified)
    J_max     = 2.40,      # A/cm^2 limiting current density (Mirai II class)
    P_gross_max = 128.0e3, # W    gross stack peak power
    P_net_max   = 110.0e3, # W    system net peak power [22]
    aux_frac  = 0.115,     # -    Paux/Pgross mid value of 0.10-0.13 [17]
)

# ----------------------------------------------------------------------------
# 4. DC/DC converter (topology T4: FC->unidirectional DC/DC->bus)
# ----------------------------------------------------------------------------
ETA_DC   = 0.95            # -    converter efficiency
P_DC_MAX = FC['P_net_max'] * ETA_DC   # W  max power deliverable to the bus
P_DC_MIN = 0.0             # W    unidirectional converter: Pdc >= 0

# ----------------------------------------------------------------------------
# 5. Battery pack: A123 ANR26650M1B (LFP), 96s10p  [11],[12]
#    Cell-level parameters from Nejad et al. [11]; pack scaling:
#    series multiplies voltage & resistance, parallel multiplies capacity
#    and divides resistance. RC time constant invariant under scaling.
# ----------------------------------------------------------------------------
BAT = dict(
    Ns        = 96,        # -    cells in series
    Np        = 10,        # -    strings in parallel
    Q_cell    = 2.5,       # Ah   cell capacity
    Rs_cell   = 8.0e-3,    # ohm  cell series resistance [11]
    R1_cell   = 6.0e-3,    # ohm  cell RC-branch resistance [11]
    C1_cell   = 30.0e3,    # F    cell RC-branch capacitance [11] (tau ~ 180 s)
    eta_coul  = 0.995,     # -    coulombic efficiency
    m_hyst    = 150.0,     # -    hysteresis transition rate [11],[12]
    I_chg_max_cell = 10.0, # A    4C  continuous charge limit (datasheet)
    I_dis_max_cell = 50.0, # A    20C continuous discharge limit (datasheet)
    SoC_min   = 0.20,
    SoC_max   = 0.95,
    SoC_0     = 0.90,      # plug-in fully charged initial condition
    SoC_target= 0.25,      # charge-depleting terminal target
)
# Derived pack quantities
BAT['Q_pack']  = BAT['Q_cell'] * BAT['Np']                    # 25 Ah
BAT['Rs_pack'] = BAT['Rs_cell'] * BAT['Ns'] / BAT['Np']       # 76.8 mOhm
BAT['R1_pack'] = BAT['R1_cell'] * BAT['Ns'] / BAT['Np']       # 57.6 mOhm
BAT['C1_pack'] = BAT['C1_cell'] * BAT['Np'] / BAT['Ns']       # tau = R1*C1 = 180 s
BAT['I_chg_max']  = BAT['I_chg_max_cell'] * BAT['Np']         # 100 A pack charge
BAT['I_dis_max']  = BAT['I_dis_max_cell'] * BAT['Np']         # 500 A pack discharge
BAT['E_nom_Wh']   = 96 * 3.3 * BAT['Q_pack']                  # ~7.92 kWh

# ----------------------------------------------------------------------------
# 6. Price scenarios - Germany 2026 (Table 3, [23],[24])
#    M_H2 in EUR/kg, M_ele in EUR/kWh
# ----------------------------------------------------------------------------
PRICES = {
    'high'    : dict(M_H2=13.85, M_ele=0.40),
    'default' : dict(M_H2=11.00, M_ele=0.35),
    'low'     : dict(M_H2= 8.00, M_ele=0.32),
}

# ----------------------------------------------------------------------------
# 7. Trip & discretization
# ----------------------------------------------------------------------------
DT       = 1.0             # s   sampling interval
N_CYCLES = 2               # -   two consecutive WLTC class 3b cycles
GAMMA    = 1000.0          # EUR terminal SoC penalty weight, Eq. (23)

# ----------------------------------------------------------------------------
# 8. EMS solver settings
# ----------------------------------------------------------------------------
DP_CFG = dict(
    dSoC = 0.005,          # state grid resolution  (151 points in [0.20,0.95])
    dPdc = 1.0e3,          # decision grid resolution 1 kW
)
AECMS_CFG = dict(
    s0 = 0.0,              # EUR/1.0-SoC  baseline equivalence offset
                           # (monetary cost already prices grid energy, so the
                           # adaptive term only has to do SoC-reference tracking)
    kp = 150.0,            # EUR/1.0-SoC  proportional gain on SoC error
    ki = 0.30,             # EUR/(1.0-SoC s) integral gain
    # (tuned empirically over the default scenario: kp=60/ki=0.1 tracked
    #  too loosely, kp=300/ki=0.5 chattered; see README section 7.2)
    dPdc = 1.0e3,          # Hamiltonian minimized over the same 1 kW grid
)
MPC_CFG = dict(
    Np    = 15,            # steps prediction horizon (15 s)
    dPdc  = 2.0e3,         # coarser 2 kW grid (real-time budget)
    dSoC  = 0.002,         # local state grid half-window resolution
    n_loc = 15,            # local SoC grid: 2*n_loc+1 points around current SoC
    gamma_mpc = 200.0,     # EUR terminal tracking weight of Eq. (30)
    beta_int  = 0.005,     # offset-free integral gain on the tracked
                           # reference (residual constant-load bias removal;
                           # swept over {0, .005, .01, .02}: .005 minimizes
                           # total cost, see README section 7.3)
)
BLFS_CFG = dict(
    band       = 0.05,     # SoC hysteresis half-width around reference
    ramp_max   = 5.0e3,    # W/s fuel-cell load ramp limit, Eq. (31)
)

# ----------------------------------------------------------------------------
# 9. Paths (relative to the bitirme2/ root)
# ----------------------------------------------------------------------------
import os
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, 'data')
RES_DIR  = os.path.join(ROOT, 'results')
FIG_DIR  = os.path.join(RES_DIR, 'figures')
for _d in (DATA_DIR, RES_DIR, FIG_DIR):
    os.makedirs(_d, exist_ok=True)
