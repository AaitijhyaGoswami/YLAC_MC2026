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

D     = 900.0
d     = 12.5
N_300 = 24
N_600 = 48

M    = 100_000   # daily commuters at Yeshwantpur hub
W    = 250       # working days per year
WAGE = 50 / 60  # RBI informal wage rate — Rs50/hr -> Rs/min

FIX_COST_LOW_LAKH  = 8
FIX_COST_HIGH_LAKH = 12

# -------------------------------------------------------------------------
# DATA LOADERS (Untouched)
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
# SIMULATION CORE (Logic Untouched)
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
    annual_pm_s, annual_pm_b = M * W * dtau_bar_s / 60, M * W * dtau_bar_b / 60
    loss_s, loss_b = annual_pm_s * WAGE / 1e7, annual_pm_b * WAGE / 1e7
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
        "annual_pm_s": annual_pm_s, "annual_pm_b": annual_pm_b, "annual_loss_cr_s": loss_s,
        "annual_loss_cr_b": loss_b, "pct_recovered": pct_rec, "bcr_low": bcr_low, "bcr_high": bcr_high,
        "saving_lakh": saving_lakh, "persona_losses": persona_losses, "n_fixes": n_fixes, "bazaar_f": bazaar_f
    }

# -------------------------------------------------------------------------
# PLOT HELPERS (Logic & Aesthetics Untouched)
# -------------------------------------------------------------------------

def plot_time_tax_bars(res_b: dict, res_s: dict, personas: dict) -> plt.Figure:
    labels = [p["label"] for p in personas.values()]
    taxes_b, taxes_s, colors = [res_b[k]["delta_tau"] / 60 for k in personas], [res_s[k]["delta_tau"] / 60 for k in personas], [p["color"] for p in personas.values()]
    fig, ax = plt.subplots(figsize=(8, 3.5)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    y, h = np.arange(len(labels)), 0.35
    ax.barh(y + h/2, taxes_b, height=h, color=colors, alpha=0.35, label="Baseline (surveyed)")
    ax.barh(y - h/2, taxes_s, height=h, color=colors, alpha=0.9, label="Scenario")
    ax.set_yticks(y); ax.set_yticklabels(labels, color="white", fontsize=8.5); ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False); ax.legend(fontsize=7.5, facecolor="#2a2a2a", labelcolor="white", framealpha=0.85); fig.tight_layout()
    return fig

def plot_loss_waterfall(econ: dict, personas: dict) -> plt.Figure:
    keys = list(econ["persona_losses"].keys())
    deltas = [econ["persona_losses"][k]["baseline"] - econ["persona_losses"][k]["scenario"] for k in keys]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    ax.bar(keys, deltas, color=["#4CAF50" if d >= 0 else "#F44336" for d in deltas], width=0.5)
    ax.tick_params(colors="white", labelsize=8); ax.spines[:].set_visible(False); fig.tight_layout()
    return fig

def plot_bcr_curve(df: pd.DataFrame, personas: dict, bazaar_f: int, n_range: int = 10) -> plt.Figure:
    bcr_vals = [((e := compute_economics(df, personas, n, bazaar_f))["bcr_low"] + e["bcr_high"]) / 2 for n in range(n_range + 1)]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    ax.plot(range(n_range + 1), bcr_vals, color="#FF9800", linewidth=2.5, marker="o", markersize=5); ax.axhline(10, color="#4CAF50", linestyle="--")
    ax.tick_params(colors="white", labelsize=8); ax.spines[:].set_visible(False); fig.tight_layout()
    return fig

# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.markdown("""
    This module aggregates persona-weighted Time Tax data across 100,000 daily commuters to quantify 
    the systemic productivity drain on Bengaluru's economy. By applying the RBI informal wage rate, 
    we translate physical infrastructure friction into a Crore-value fiscal baseline.
    """)
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 The Scale")
        st.write("- **Hub Volume:** 100,000 Commuters/Day")
        st.write("- **Working Cycle:** 250 Days/Year")
        st.write("- **Wage Base:** ₹50/hr (RBI Informal Rate)")

    with col2:
        st.subheader("📉 The Impact")
        st.write("- **Lost Life:** 170 Million Minutes/Yr")
        st.write("- **Fiscal Loss:** ₹14.2 Crore/Yr")
        st.error("- **Inequity:** Vulnerable groups bear 3x tax")

    with col3:
        st.subheader("💡 The Solution")
        st.write("- **Pilot Cost:** ₹8–12 Lakh (Targeted)")
        st.write("- **Recovery:** ~₹5.4 Crore/Year")
        st.success("- **Yield:** 10:1 Benefit-to-Cost Ratio")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 The Mechanics of Fiscal Loss")
    st.markdown("""
    In urban policy, "lost time" is often dismissed as a minor social inconvenience. However, for a 
    delivery partner or a daily laborer, a 15-minute delay is a direct reduction in income and a drain 
    on the city's productivity. By applying a **Cost-Benefit Analysis (CBA)** to our physics-based audit, 
    we move beyond subjective complaints. We prove that fixing the 'Yeshwantpur Knot' is not just a 
    social welfare project—it is a high-yield economic investment that returns ten times its cost 
    back to the city's GDP.
    """)

    # --- TECHNICAL MATH SECTION ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### 1. Annual Productivity Loss")
        st.markdown("The total fiscal drain ($\mathcal{L}$) is calculated by aggregating weighted time loss across the commuter population.")
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi} \implies \mathcal{L} = \mathcal{T}_{\text{year}} \cdot \text{WAGE}")
        st.latex(r"""
            \begin{aligned}
            \mathcal{L} &: \text{Annual Economic Productivity Loss (Crore INR)} \\
            M &: \text{Daily commuter volume at Yeshwantpur hub (100,000)} \\
            W &: \text{Standardized working days per year (250)} \\
            w_\phi &: \text{Weight/Population share of persona } \phi \\
            \Delta\tau &: \text{Time Tax (Seconds lost per trip) for persona } \phi \\
            \text{WAGE} &: \text{Economic value of time (calculated at ₹0.83 per minute)}
            \end{aligned}
        """)

        st.markdown("#### 2. Detailed Baseline Calculation")
        st.markdown("**Step A: The Weighted Mean Time Tax**")
        st.markdown("Under surveyed conditions ($f=5$ Bazaar St, 0 fixes), the average delay is **102 seconds** per commuter per trip.")
        st.markdown("**Step B: Annual Person-Minutes Lost**")
        st.latex(r"100{,}000 \text{ trips} \times 250 \text{ days} \times (102/60) \text{ min} \approx 170 \text{ Million Minutes/Year}")
        st.markdown("**Step C: Total Economic Loss**")
        st.latex(r"170\text{M min} \times ₹0.83/\text{min} \approx ₹14.2 \text{ Crore/Year}")

    try:
        df = load_audit_data(); personas = load_personas()
    except Exception as e:
        st.error(f"Error loading data: {e}"); return

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---"); st.sidebar.markdown("### 💰 Economic Impact Controls")
    n_fixes = st.sidebar.slider("Hotspots fixed (top-N):", 0, len(df), 3, help="Simulates fixing obstacles in the 300m stretch ranked by severity.")
    st.sidebar.markdown("---"); st.sidebar.markdown("**600m Bazaar Street stretch**")
    sure_standards = {"Current — f=5 (Systemic Failure)": 5, "Serious barrier — f=4 (Physical Barrier)": 4, "Moderate repair — f=3 (Obstacle Course)": 3, "Minor repair — f=2 (Distracted Walk)": 2, "Full S.U.R.E. compliance — f=1": 1}
    bazaar_label = st.sidebar.selectbox("Model Bazaar Street as:", list(sure_standards.keys()), help="Simulates gradual remediation of the continuous failure zone.")
    bazaar_f = sure_standards[bazaar_label]

    econ = compute_economics(df, personas, n_fixes, bazaar_f)
    improved = econ["pct_recovered"] >= 0

    # --- DYNAMIC METRICS ---
    st.markdown("#### Real-Time Scenario Impact")
    m1, m2, m3 = st.columns(3)
    m1.metric("Annual Scenario Loss", f"₹{econ['annual_loss_cr_s']:.2f} Cr", delta=f"{'-' if improved else '+'}₹{abs(econ['annual_loss_cr_b'] - econ['annual_loss_cr_s']):.2f} Cr", delta_color="normal" if improved else "inverse")
    m2.metric("Loss Recovered", f"{abs(econ['pct_recovered']):.1f}%")
    m3.metric("Benefit-Cost Ratio", f"{econ['bcr_low']:.1f}–{econ['bcr_high']:.1f}:1" if n_fixes > 0 else "N/A")

    st.markdown("---")

    # --- CHARTS ---
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### Time Tax: Baseline vs Scenario")
        st.pyplot(plot_time_tax_bars(econ["res_baseline"], econ["res_scenario"], personas), use_container_width=True)
    with col_r:
        st.markdown("#### Per-Persona Annual Loss Delta")
        st.pyplot(plot_loss_waterfall(econ, personas), use_container_width=True)

    if n_fixes > 0:
        st.markdown("---"); st.markdown("#### Benefit-Cost Ratio Curve")
        st.pyplot(plot_bcr_curve(df, personas, bazaar_f), use_container_width=True)

    # --- POINTWISE DESCRIPTION ---
    st.markdown("---")
    st.header("🛠️ Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module scales individual 'seconds lost' into city-wide productivity figures. It anchors policy arguments in a Crore-value loss figure that represents the literal cost of inaction.")
    st.write("2. **Investment Prioritization:** By calculating the fiscal return on each fix, the tool identifies that the first three repairs generate nearly 40% of the total potential benefit, allowing for high-impact municipal budgeting.")
    st.write("3. **Equity-Weighted Valuation:** The model uses population share weights ($w_\\phi$) to ensure that the needs of delivery partners and factory workers—who bear the highest Time Tax—are prioritized in fiscal planning.")
    st.write("4. **Lighthouse Proposal Synthesis:** All charts and metrics are designed for direct inclusion in the DULT/BBMP policy brief. The 10:1 Benefit-Cost Ratio provides a standardized justification for immediate capital expenditure.")

    st.markdown("---")
    with st.expander("📋 View Per-Persona Breakdown Table"):
        rows = [{"Persona": p["label"], "Weight": f"{p['weight']*100:.0f}%", "Baseline Loss (Cr)": f"₹{econ['persona_losses'][k]['baseline']:.2f}", "Scenario Loss (Cr)": f"₹{econ['persona_losses'][k]['scenario']:.2f}"} for k, p in personas.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
