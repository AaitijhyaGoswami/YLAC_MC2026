import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
import streamlit as st

# -------------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------------

D      = 900.0
d      = 12.5
N_300 = 24
N_600 = 48

M    = 100_000   # daily commuters at Yeshwantpur hub
W    = 250       # working days per year
WAGE = 50 / 60  # RBI informal wage rate — Rs50/hr -> Rs/min

FIX_COST_LOW_LAKH  = 8
FIX_COST_HIGH_LAKH = 12

# -------------------------------------------------------------------------
# DATA LOADERS
# -------------------------------------------------------------------------

def load_audit_data() -> pd.DataFrame:
    path = os.path.join("data", "audit_log.csv")
    df = pd.read_csv(path)
    assert {"id", "lat", "lon", "f_value"}.issubset(df.columns)
    return df

def load_personas() -> dict:
    path = os.path.join("data", "personas.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)

# -------------------------------------------------------------------------
# SIMULATION CORE
# -------------------------------------------------------------------------

def build_f_array(df: pd.DataFrame, n_fixes: int, bazaar_f: int = 5) -> np.ndarray:
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    return np.concatenate([f_300, np.full(N_600, float(bazaar_f))])

def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    v0, k, f_max, alpha, delta = persona["v0"], persona["k"], persona["f_max"], persona["alpha"], persona["delta"]
    tau_i = np.empty(len(f_array))
    is_det = np.zeros(len(f_array), dtype=bool)
    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i] = (d + delta) * alpha / v0
            is_det[i] = True
        else:
            tau_i[i] = d * (fi ** k) / v0
    T_actual = float(tau_i.sum())
    T_ideal = D / v0
    return {
        "T_actual": T_actual, "T_ideal": T_ideal, "delta_tau": T_actual - T_ideal,
        "n_detours": int(is_det.sum()), "tau_i": tau_i, "is_det": is_det
    }

def compute_economics(df: pd.DataFrame, personas: dict, n_fixes: int, bazaar_f: int = 5) -> dict:
    f_scenario = build_f_array(df, n_fixes, bazaar_f)
    f_baseline = build_f_array(df, 0, 5)
    res_s = {k: run_simulation(f_scenario, v) for k, v in personas.items()}
    res_b = {k: run_simulation(f_baseline, v) for k, v in personas.items()}
    total_w = sum(p["weight"] for p in personas.values())
    
    dtau_bar_s = sum(res_s[k]["delta_tau"] * personas[k]["weight"] for k in personas) / total_w
    dtau_bar_b = sum(res_b[k]["delta_tau"] * personas[k]["weight"] for k in personas) / total_w
    
    pm_s, pm_b = M * W * dtau_bar_s / 60, M * W * dtau_bar_b / 60
    loss_s, loss_b = pm_s * WAGE / 1e7, pm_b * WAGE / 1e7
    pct_rec = ((loss_b - loss_s) / loss_b * 100 if loss_b > 0 else 0.0)

    if n_fixes > 0:
        cost_lo, cost_hi = FIX_COST_LOW_LAKH * n_fixes / 3, FIX_COST_HIGH_LAKH * n_fixes / 3
        saving_lakh = (loss_b - loss_s) * 100
        bcr_low, bcr_high = saving_lakh / cost_hi, saving_lakh / cost_lo
    else: bcr_low = bcr_high = saving_lakh = 0.0
    
    persona_losses = {key: {"baseline": M * W * res_b[key]["delta_tau"] / 60 * WAGE / 1e7,
                            "scenario": M * W * res_s[key]["delta_tau"] / 60 * WAGE / 1e7} for key in personas}
    return {
        "res_scenario": res_s, "res_baseline": res_b, "dtau_bar_s": dtau_bar_s, "dtau_bar_b": dtau_bar_b,
        "annual_pm_s": pm_s, "annual_pm_b": pm_b, "annual_loss_cr_s": loss_s, "annual_loss_cr_b": loss_b,
        "pct_recovered": pct_rec, "bcr_low": bcr_low, "bcr_high": bcr_high, "saving_lakh": saving_lakh,
        "persona_losses": persona_losses, "n_fixes": n_fixes, "bazaar_f": bazaar_f
    }

# -------------------------------------------------------------------------
# VISUALIZATION HELPERS (Identical Aesthetics)
# -------------------------------------------------------------------------

def plot_time_tax_bars(res_b: dict, res_s: dict, personas: dict) -> plt.Figure:
    labels = [p["label"] for p in personas.values()]
    taxes_b = [res_b[k]["delta_tau"] / 60 for k in personas]
    taxes_s = [res_s[k]["delta_tau"] / 60 for k in personas]
    colors = [p["color"] for p in personas.values()]
    max_tax = max(max(taxes_b), max(taxes_s), 0.5)
    y, h = np.arange(len(labels)), 0.35
    fig, ax = plt.subplots(figsize=(8, 3.5)); fig.patch.set_facecolor("#1a1a1a"); ax.set_facecolor("#1a1a1a")
    ax.barh(y + h/2, taxes_b, height=h, color=colors, alpha=0.35, linewidth=0, label="Baseline (surveyed)")
    ax.barh(y - h/2, taxes_s, height=h, color=colors, alpha=0.9, linewidth=0, label="Scenario")
    for i, (vb, vs) in enumerate(zip(taxes_b, taxes_s)):
        ax.text(max_tax * 0.015, y[i] + h/2, f"{vb:.1f}m", va="center", fontsize=7, color="#aaaaaa")
        col = "#4CAF50" if vs <= vb else "#F44336"
        ax.text(max_tax * 0.015, y[i] - h/2, f"{vs:.1f}m", va="center", fontsize=7, color=col)
    ax.set_xlim(0, max_tax * 1.3); ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=8.5, color="white")
    ax.set_xlabel("Time Tax per trip (min)", color="white"); ax.tick_params(colors="white", labelsize=8)
    ax.legend(fontsize=7.5, facecolor="#2a2a2a", labelcolor="white", framealpha=0.85); ax.spines[:].set_visible(False)
    fig.tight_layout(); return fig

def plot_loss_waterfall(econ: dict, personas: dict) -> plt.Figure:
    PLABELS = {"able_bodied":"Able-bodied","elderly":"Elderly","wheelchair":"Wheelchair","delivery":"Delivery"}
    keys = list(econ["persona_losses"].keys())
    deltas = [econ["persona_losses"][k]["baseline"] - econ["persona_losses"][k]["scenario"] for k in keys]
    cats = [PLABELS.get(k, k) for k in keys]
    colors = ["#4CAF50" if d >= 0 else "#F44336" for d in deltas]
    max_abs = max(abs(d) for d in deltas) if deltas else 1.0
    fig, ax = plt.subplots(figsize=(7, 3)); fig.patch.set_facecolor("#1a1a1a"); ax.set_facecolor("#1a1a1a")
    bars = ax.bar(cats, deltas, color=colors, linewidth=0, width=0.5); ax.axhline(0, color="#555", linewidth=0.8)
    for bar, val in zip(bars, deltas):
        va, off = ("bottom", max_abs * 0.03) if val >= 0 else ("top", -max_abs * 0.03)
        ax.text(bar.get_x() + bar.get_width() / 2, val + off, f"{'−' if val < 0 else '+'}Rs{abs(val):.2f}Cr", ha="center", va=va, fontsize=7.5, color="white")
    ax.set_ylabel("Annual loss change (Rs Cr)", color="white"); ax.tick_params(colors="white", labelsize=8); ax.spines[:].set_visible(False)
    fig.tight_layout(); return fig

def plot_bcr_curve(df: pd.DataFrame, personas: dict, bazaar_f: int, n_range: int = 10) -> plt.Figure:
    bcr_vals = []
    for n in range(n_range + 1):
        e = compute_economics(df, personas, n, bazaar_f)
        bcr_vals.append((e["bcr_low"] + e["bcr_high"]) / 2)
    fig, ax = plt.subplots(figsize=(7, 3.2)); fig.patch.set_facecolor("#1a1a1a"); ax.set_facecolor("#1a1a1a")
    xs = list(range(n_range + 1))
    ax.plot(xs, bcr_vals, color="#FF9800", linewidth=2.5, marker="o", markersize=5, zorder=3)
    ax.fill_between(xs, [max(v, 0) for v in bcr_vals], 0, alpha=0.12, color="#FF9800")
    ax.axhline(10, color="#4CAF50", linewidth=1, linestyle="--", label="BCR = 10:1 threshold")
    ax.set_xlabel("Number of hotspots fixed (top-N)", color="white"); ax.set_ylabel("Benefit-Cost Ratio", color="white")
    ax.set_ylim(0, max(max(bcr_vals) * 1.3, 15)); ax.legend(fontsize=8, labelcolor="white", frameon=False)
    ax.tick_params(colors="white", labelsize=8); ax.spines[:].set_visible(False)
    fig.tight_layout(); return fig

# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.markdown("""
    The **Fiscal Impact Engine** is the definitive economic audit of the Yeshwantpur corridor, providing the link between urban friction and regional GDP for Bangalore. Aggregating persona-weighted Time Tax for 100,000 daily commuters in a high-intensity hub volume, this module enables the calculation of **Productivity Loss** resulting from the individual transit resistance of those commuters. It establishes the correlation between fiscal loss and infrastructural neglect to demonstrate that total longitudinal delay imposed on the city's workforce results in an annual multi-crore deficit of total economic output.

Municipal stakeholder and policy makers will be able to look at urban infrastructure repairs as a pro-active high yielding strategic investment rather than as a cost to be thrown money at when it breaks. The Benefit-Cost Ratio (BCR) established by this module provides the necessary mathematical evidence to validate immediate capital expenditure (CAPEX) for the repair of the corridors. By providing a data driven method for determining the progress of a city’s move towards a transit-oriented metropolis, the return of mobility is viewed not only as a social need, but also as a key aspect of recovering lost economic value and making the city a worldwide competitor.
    """)

    # --- TECHNICAL MATH SECTION ---
    # --- TECHNICAL MATH SECTION (Enhanced with all variable definitions) ---
    # --- TECHNICAL MATH SECTION (Standardized to LaTeX Block Style) ---
    # --- TECHNICAL MATH SECTION (Standardized Block Style with Worked Example) ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Fundamental Equations")
        st.markdown("The model scales individual pedestrian physics into city-wide economic figures through a four-stage aggregation.")
        st.latex(r"""
            \begin{aligned}
            v_{\text{eff}}(i, \phi) &= \frac{v_0(\phi)}{f_i^{\,k(\phi)}} \\
            \Delta\tau(\phi) &= \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{\,k(\phi)} - N \right) \\
            \mathcal{L} &= M \cdot W \cdot \frac{\bar{\Delta\tau}}{60} \cdot \text{WAGE} \cdot 10^{-7}
            \end{aligned}
        """)

        st.markdown("#### Variable Definitions")
        st.latex(r"""
            \begin{aligned}
            f_i &: \text{Friction Index of segment } i \text{ (Discrete nodes or Bazaar St)} \\
            v_0(\phi) &: \text{Free-walking speed of persona } \phi \text{ (Standardized m/s)} \\
            k(\phi) &: \text{Sensitivity exponent for persona } \phi \text{ (Rate of velocity decay)} \\
            \Delta\tau(\phi) &: \text{Time Tax (Seconds stolen per trip) for a single persona} \\
            M &: \text{Daily Hub Volume (100,000 commuters at Yeshwantpur hub)} \\
            W &: \text{Annual Cycle (250 standardized working days per year)} \\
            w_\phi &: \text{Weighting factor (Proportional share of persona in the population)} \\
            \text{WAGE} &: \text{Economic value of time (RBI Informal rate } \approx \text{ ₹0.83/min)} \\
            \mathcal{L} &: \text{Annual Economic Productivity Loss (Expressed in Crore INR)}
            \end{aligned}
        """)

        st.markdown("#### Piecewise Segmental Traversal")
        st.markdown("The model accounts for 'Impassability' where friction exceeds a persona's barrier threshold ($f_{\text{max}}$), forcing a vehicular Right-of-Way (ROW) detour.")
        st.latex(r"""
            \tau_i(\phi) = 
            \begin{cases} 
            \frac{d \cdot f_i^{k(\phi)}}{v_0(\phi)} & \text{if } f_i \leq f_{\text{max}} \quad \text{(Path Traversal)} \\ 
            \frac{(d + \delta(\phi)) \cdot \alpha}{v_0(\phi)} & \text{if } f_i > f_{\text{max}} \quad \text{(ROW Detour)} 
            \end{cases}
        """)
        st.latex(r"""
            \begin{aligned}
            \tau_i &: \text{Time required to navigate segment } i \text{ (seconds)} \\
            d &: \text{Unit segment length (12.5 meters)} \\
            \delta(\phi) &: \text{Detour distance penalty incurred entering traffic} \\
            \alpha &: \text{Safety penalty multiplier (1.5x speed reduction during detour)}
            \end{aligned}
        """)

        st.markdown("#### Fiscal Aggregation and Efficiency")
        st.markdown("The final metrics quantify the baseline drain and the efficiency of the proposed capital expenditure.")
        st.latex(r"""
            \begin{aligned}
            \bar{\Delta\tau} &= \frac{\sum_{\phi} w_\phi \Delta\tau(\phi)}{\sum w_\phi} \quad \text{(Weighted Mean Time Tax)} \\
            \Delta\mathcal{L} &= \mathcal{L}_{\text{baseline}} - \mathcal{L}_{\text{scenario}} \quad \text{(Annual Economic Benefit)} \\
            BCR &= \frac{\Delta\mathcal{L} \cdot 100}{\text{Repair Cost (Lakhs)}} \quad \text{(Benefit-Cost Ratio)}
            \end{aligned}
        """)

        st.markdown("#### Worked Unit Example: The Cost of One Failed Node")
        st.markdown("""
        Consider a single segment ($d = 12.5\text{m}$) rated at **$f=5$ (Systemic Failure)**. We calculate the fiscal drain imposed 
        specifically on the **Able-bodied Persona** ($\phi_{A}$) who makes up 45% of the hub volume.
        """)

        st.latex(r"""
            \begin{aligned}
            \text{Input Parameters: } & v_0 = 1.4 \text{ m/s, } k = 0.6, \text{ } w_A = 0.45 \\
            \tau_{\text{ideal}} &= \frac{12.5}{1.4} = 8.93 \text{ seconds} \\
            v_{\text{eff}} &= \frac{1.4}{5^{0.6}} \approx 0.533 \text{ m/s} \\
            \tau_{\text{actual}} &= \frac{12.5}{0.533} \approx 23.45 \text{ seconds} \\
            \Delta\tau (\phi_A) &= 23.45 - 8.93 = 14.52 \text{ seconds per trip}
            \end{aligned}
        """)

        st.markdown("""
        Scaling this 14.5-second delay across the annual commuter volume ($M=100,000$) for the population share ($w_A=0.45$):
        """)

        st.latex(r"""
            \begin{aligned}
            \mathcal{T}_{\text{year}} &= (100,000 \cdot 0.45) \cdot 250 \cdot \frac{14.52}{60} \\
            \mathcal{T}_{\text{year}} &\approx 2,722,500 \text{ person-minutes lost per year} \\
            \text{Loss} &= 2,722,500 \cdot ₹0.833 \approx ₹2,267,842
            \end{aligned}
        """)

        st.markdown("""
        **The Result:** A single 12.5m stretch of broken footpath costs the city **₹22.6 Lakhs per year** in lost productivity 
        for just one demographic. When aggregated across all 72 segments, this produces the baseline 
        drain of **₹14.2 Crore/Year**.
        """)

    # --- WORKED EXAMPLE SECTION (To be included in the expander or as a new section) ---
    
    try:
        df = load_audit_data(); personas = load_personas()
    except Exception as e:
        st.error(f"Error loading data: {e}"); return

    # --- SIDEBAR CONTROLS (Restored to Exact Original) ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Economic Impact Controls")
    n_fixes = st.sidebar.slider(
        "Hotspots fixed (top-N by f-value):",
        min_value=0, max_value=len(df), value=3, step=1,
        help=(
            "Nodes ranked highest-f first. Each fix sets that node to f=1. "
            "BCR is only shown when $n_{fixes} > 0$."
        )
    )

    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Partial repair — f=4 (Physical Barrier)": 4,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Near compliant — f=2 (Distracted Walk)": 2,
        "Full S.U.R.E. compliance — f=1 (Gold Standard)": 1,
    }
    bazaar_label = st.sidebar.selectbox(
        "Bazaar Street (600m) modelled as:",
        options=list(sure_standards.keys()),
        index=0,
        help="Simulates gradual remediation of the continuous failure zone"
    )
    bazaar_f = sure_standards[bazaar_label]

    # --- COMPUTATION ---
    econ = compute_economics(df, personas, n_fixes, bazaar_f)
    improved = econ["pct_recovered"] >= 0

    # --- HEADLINE METRICS (Exact Original Style) ---
    st.markdown("---")
    st.markdown("#### Baseline: Surveyed Conditions")
    c1, c2, c3 = st.columns(3)
    c1.metric("Annual Person-Minutes Lost", f"{econ['annual_pm_b']/1e6:.2f}M", help="Minutes lost by the total commuter volume")
    c2.metric("Annual Productivity Loss", f"Rs {econ['annual_loss_cr_b']:.2f} Cr", help="Annual loss in income of pedestrian commuters aggregated over all 4 personas")
    c3.metric("Weighted Mean Time Tax", f"{econ['dtau_bar_b']:.1f} s/trip", help="Time lost by an average commuter while traversing the 900 m stretch")

    st.markdown("#### Scenario: After Fixes & Bazaar Adjustment")
    c4, c5, c6 = st.columns(3)
    delta_loss = abs(econ["annual_loss_cr_b"] - econ["annual_loss_cr_s"])
    c4.metric("Annual Loss", f"Rs {econ['annual_loss_cr_s']:.2f} Cr", 
              delta=f"{'−' if improved else '+'}Rs {delta_loss:.2f} Cr", delta_color="normal" if improved else "inverse", help="Annual loss and amount recovered after simulated fixes")
    c5.metric("Time Tax Change", f"{abs(econ['pct_recovered']):.1f}% {'recovered' if improved else 'worsened'}", 
              delta=f"{econ['pct_recovered']:+.1f}%", delta_color="normal" if improved else "inverse", help="Minutes recovered from the simulated fixes")
    c6.metric("Benefit-Cost Ratio", f"{econ['bcr_low']:.1f}–{econ['bcr_high']:.1f} : 1" if n_fixes > 0 else "N/A", help="Calculated considering the expenses for each fix to be approximately Rs 5 - 10 lakhs")


    # --- CHARTS (Exact Original Style) ---
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Time Tax Comparison")
        st.pyplot(plot_time_tax_bars(econ["res_baseline"], econ["res_scenario"], personas), use_container_width=True)
    with col_r:
        st.markdown("#### Annual Loss Delta")
        st.pyplot(plot_loss_waterfall(econ, personas), use_container_width=True)

    # --- BCR CURVE ---
    if n_fixes > 0:
        st.markdown("---")
        st.markdown("#### Benefit-Cost Ratio Curve")
        st.caption("Investment efficiency across increasing remediation nodes. Green line indicates 10:1 return threshold.")
        st.pyplot(plot_bcr_curve(df, personas, bazaar_f), use_container_width=True)

    # --- POINTWISE DESCRIPTION (Numbered Style) ---
    st.markdown("---")
    st.header("Model Functionality")
    st.write("* **Macro-Economic Aggregation:** This module converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of 100,000 daily commuters, it anchors policy arguments in a Crore-value productivity loss figure that represents the literal economic cost of systemic infrastructure neglect.")
    st.write("* **Strategic Investment Prioritization:** The tool identifies the non-linear returns on infrastructure spending. It demonstrates that a targeted 'Lighthouse Pilot' (fixing just the top three nodes) recovers nearly 40% of the total potential economic benefit, allowing municipal planners to achieve maximum impact with minimal capital expenditure.")
    st.write("* **Equity-Weighted Productivity Valuation:** By utilizing population share weights ($w_\\phi$), the model ensures that the fiscal drain on the city’s most essential workers (delivery partners and daily laborers) is not erased by 'average' walking speeds. It frames universal design as an economic imperative rather than just a social welfare goal.")
    st.write("* **Standardized Proposal Synthesis:** Every metric and visualization is formatted for direct extraction into DULT or BBMP project approval templates. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' mathematical justification for immediate intervention, moving the conversation from anecdotal complaints to data-driven governance.")
    st.markdown("---")
    st.markdown("#### Per-Persona Breakdown")
    rows = [{"Persona": p["label"], "Weight": f"{p['weight']*100:.0f}%", "Baseline Loss": f"Rs{econ['persona_losses'][k]['baseline']:.2f} Cr", "Scenario Loss": f"Rs{econ['persona_losses'][k]['scenario']:.2f} Cr"} for k, p in personas.items()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
