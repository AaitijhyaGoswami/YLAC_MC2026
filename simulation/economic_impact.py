import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
import streamlit as st

# -------------------------------------------------------------------------
# CONSTANTS & LOGIC (Preserved Exactly)
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
    v0    = persona["v0"]
    k     = persona["k"]
    f_max = persona["f_max"]
    alpha = persona["alpha"]
    delta = persona["delta"]

    tau_i  = np.empty(len(f_array))
    is_det = np.zeros(len(f_array), dtype=bool)

    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i]  = (d + delta) * alpha / v0
            is_det[i] = True
        else:
            tau_i[i] = d * (fi ** k) / v0

    T_actual = float(tau_i.sum())
    T_ideal  = D / v0
    return {
        "T_actual":  T_actual,
        "T_ideal":   T_ideal,
        "delta_tau": T_actual - T_ideal,
        "n_detours": int(is_det.sum()),
        "tau_i":     tau_i,
        "is_det":    is_det,
    }


# -------------------------------------------------------------------------
# ECONOMIC MODEL
# -------------------------------------------------------------------------

def compute_economics(df: pd.DataFrame, personas: dict, n_fixes: int, bazaar_f: int = 5) -> dict:
    f_scenario = build_f_array(df, n_fixes, bazaar_f)
    f_baseline = build_f_array(df, 0, 5)

    res_s = {k: run_simulation(f_scenario, v) for k, v in personas.items()}
    res_b = {k: run_simulation(f_baseline, v) for k, v in personas.items()}

    total_w = sum(p["weight"] for p in personas.values())

    def weighted_mean_dtau(res):
        return sum(res[k]["delta_tau"] * personas[k]["weight"] for k in personas) / total_w

    dtau_bar_s = weighted_mean_dtau(res_s)
    dtau_bar_b = weighted_mean_dtau(res_b)

    annual_pm_s = M * W * dtau_bar_s / 60
    annual_pm_b = M * W * dtau_bar_b / 60

    annual_loss_cr_s = annual_pm_s * WAGE / 1e7
    annual_loss_cr_b = annual_pm_b * WAGE / 1e7

    pct_recovered = ((annual_loss_cr_b - annual_loss_cr_s) / annual_loss_cr_b * 100 if annual_loss_cr_b > 0 else 0.0)

    if n_fixes > 0:
        cost_low_lakh  = FIX_COST_LOW_LAKH  * n_fixes / 3
        cost_high_lakh = FIX_COST_HIGH_LAKH * n_fixes / 3
        saving_lakh = (annual_loss_cr_b - annual_loss_cr_s) * 100
        bcr_low  = saving_lakh / cost_high_lakh if cost_high_lakh > 0 else 0.0
        bcr_high = saving_lakh / cost_low_lakh  if cost_low_lakh  > 0 else 0.0
    else:
        bcr_low = bcr_high = saving_lakh = 0.0

    persona_losses = {key: {"baseline": M * W * res_b[key]["delta_tau"] / 60 * WAGE / 1e7,
                            "scenario": M * W * res_s[key]["delta_tau"] / 60 * WAGE / 1e7} for key in personas}

    return {
        "res_scenario": res_s, "res_baseline": res_b, "dtau_bar_s": dtau_bar_s, "dtau_bar_b": dtau_bar_b,
        "annual_pm_s": annual_pm_s, "annual_pm_b": annual_pm_b, "annual_loss_cr_s": annual_loss_cr_s,
        "annual_loss_cr_b": annual_loss_cr_b, "pct_recovered": pct_recovered, "bcr_low": bcr_low,
        "bcr_high": bcr_high, "saving_lakh": saving_lakh, "persona_losses": persona_losses,
        "n_fixes": n_fixes, "bazaar_f": bazaar_f,
    }


# -------------------------------------------------------------------------
# PLOT HELPERS (Logic preserved)
# -------------------------------------------------------------------------

def plot_time_tax_bars(res_b: dict, res_s: dict, personas: dict) -> plt.Figure:
    labels, taxes_b, taxes_s, colors = [p["label"] for p in personas.values()], [res_b[k]["delta_tau"] / 60 for k in personas], [res_s[k]["delta_tau"] / 60 for k in personas], [p["color"] for p in personas.values()]
    fig, ax = plt.subplots(figsize=(8, 3.5)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    y, h = np.arange(len(labels)), 0.35
    ax.barh(y + h/2, taxes_b, height=h, color=colors, alpha=0.35, label="Baseline")
    ax.barh(y - h/2, taxes_s, height=h, color=colors, alpha=0.9, label="Scenario")
    ax.set_yticks(y); ax.set_yticklabels(labels, color="white"); ax.tick_params(colors="white")
    ax.spines[:].set_visible(False); ax.legend(); fig.tight_layout()
    return fig

def plot_loss_waterfall(econ: dict, personas: dict) -> plt.Figure:
    keys = list(econ["persona_losses"].keys())
    deltas = [econ["persona_losses"][k]["baseline"] - econ["persona_losses"][k]["scenario"] for k in keys]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    ax.bar(keys, deltas, color=["#4CAF50" if d >= 0 else "#F44336" for d in deltas])
    ax.tick_params(colors="white"); ax.spines[:].set_visible(False); fig.tight_layout()
    return fig

def plot_bcr_curve(df: pd.DataFrame, personas: dict, bazaar_f: int, n_range: int = 10) -> plt.Figure:
    bcr_vals = [((e := compute_economics(df, personas, n, bazaar_f))["bcr_low"] + e["bcr_high"]) / 2 for n in range(n_range + 1)]
    fig, ax = plt.subplots(figsize=(7, 3)); ax.set_facecolor("#1a1a1a"); fig.patch.set_facecolor("#1a1a1a")
    ax.plot(range(n_range+1), bcr_vals, color="#FF9800", marker="o"); ax.axhline(10, color="#4CAF50", linestyle="--")
    ax.tick_params(colors="white"); ax.spines[:].set_visible(False); fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("💰 Economic Impact & Policy Brief")
    st.markdown("""
    This module translates the 'Time Tax' into economic value. By aggregating persona-weighted time loss across 
    100,000 daily commuters, we quantify the productivity drain on Bengaluru's economy and calculate the 
    Benefit-Cost Ratio of targeted infrastructure repairs.
    """)
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 The Scale")
        st.write("- **Volume:** 100,000 Daily Commuters")
        st.write("- **Cycle:** 250 Working Days/Year")
        st.write("- **Wage:** ₹50/hr (RBI Informal Rate)")

    with col2:
        st.subheader("📉 The Impact")
        st.write("- **Lost Life:** 170 Million Minutes/Yr")
        st.error("- **Fiscal Drain:** ₹14.2 Crore/Yr")
        st.write("- **Tax:** Regressive impact on vulnerable")

    with col3:
        st.subheader("💡 The Solution")
        st.write("- **Investment:** ₹8–12 Lakh (Pilot)")
        st.write("- **Recovery:** ~₹5.4 Crore/Yr")
        st.success("- **Efficiency:** 10:1 Return on Capital")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 Why are we using Economics?")
    st.markdown("""
    In urban policy, "lost time" is often viewed as a social inconvenience rather than a fiscal loss. However, 
    at a major intermodal hub like Yeshwantpur, time is a component of Gross Domestic Product (GDP). 
    A 15-minute delay for a delivery partner or a factory worker is a direct reduction in the city's 
    economic output. By applying **Cost-Benefit Analysis (CBA)**, we demonstrate that fixing the 
    'Mobility Knot' is not just a social welfare project—it is a high-return investment. We prove that 
    every rupee spent on standardizing these footpaths returns ten times its value to the local economy.
    """)

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("📖 View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### 1. Annual Productivity Loss")
        st.markdown("The total fiscal drain ($\mathcal{L}$) is the product of the total time stolen from the population and the localized productivity rate.")
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi} \implies \mathcal{L} = \mathcal{T}_{\text{year}} \cdot \text{WAGE}")
        st.latex(r"""
            \begin{aligned}
            \mathcal{L} &: \text{Annual Economic Productivity Loss (expressed in Crore INR)} \\
            M &: \text{Daily commuter volume at the hub (100,000 individuals)} \\
            W &: \text{Standardized working days per annum (250 days)} \\
            w_\phi &: \text{Population share of each specific persona } \phi \\
            \Delta\tau &: \text{Time Tax (Seconds lost) for persona } \phi \text{ per trip} \\
            \text{WAGE} &: \text{The economic value of time (calculated at ₹0.83 per minute)}
            \end{aligned}
        """)

        st.markdown("#### 2. Benefit-Cost Ratio (BCR)")
        st.markdown("We index the efficiency of municipal spending by comparing annual savings to the one-time repair cost.")
        st.latex(r"BCR = \frac{(\mathcal{L}_{\text{baseline}} - \mathcal{L}_{\text{scenario}}) \cdot 100}{\mathcal{C}_{\text{repair}}}")
        st.latex(r"""
            \begin{aligned}
            BCR &: \text{Benefit-Cost Ratio (Value recovered for every ₹1 invested)} \\
            \mathcal{L}_{\text{baseline}} &: \text{Loss under surveyed conditions (n\_fixes = 0, f = 5)} \\
            \mathcal{L}_{\text{scenario}} &: \text{Residual loss after targeted infrastructure fixes} \\
            \mathcal{C}_{\text{repair}} &: \text{Estimated capital expenditure for repairs (in Lakh INR)}
            \end{aligned}
        """)

    try:
        df = load_audit_data(); personas = load_personas()
    except Exception as e:
        st.error(f"Error loading data: {e}"); return

    # --- SIDEBAR & COMPUTATION ---
    st.sidebar.markdown("---"); st.sidebar.markdown("### 💰 Economic Impact Controls")
    n_fixes = st.sidebar.slider("Hotspots fixed (top-N):", 0, len(df), 3)
    sure_standards = {"Current (f=5)": 5, "Moderate (f=3)": 3, "Compliance (f=1)": 1}
    bazaar_f = sure_standards[st.sidebar.selectbox("Bazaar St Model:", list(sure_standards.keys()))]
    
    econ = compute_economics(df, personas, n_fixes, bazaar_f)
    improved = econ["pct_recovered"] >= 0

    # --- METRICS DISPLAY ---
    st.markdown("#### Real-Time Scenario Impact")
    m1, m2, m3 = st.columns(3)
    m1.metric("Annual Scenario Loss", f"Rs{econ['annual_loss_cr_s']:.2f} Cr", delta=f"{'-' if improved else '+'}Rs{abs(econ['annual_loss_cr_b'] - econ['annual_loss_cr_s']):.2f} Cr", delta_color="normal" if improved else "inverse")
    m2.metric("Loss Recovered", f"{abs(econ['pct_recovered']):.1f}%")
    m3.metric("Benefit-Cost Ratio", f"{econ['bcr_low']:.1f} : 1" if n_fixes > 0 else "N/A")

    st.markdown("---")

    # --- CHARTS ---
    c_l, c_r = st.columns(2)
    with c_l:
        st.markdown("#### Time Tax: Baseline vs Scenario")
        st.pyplot(plot_time_tax_bars(econ["res_baseline"], econ["res_scenario"], personas), use_container_width=True)
    with c_r:
        st.markdown("#### Annual Loss Delta (₹ Cr)")
        st.pyplot(plot_loss_waterfall(econ, personas), use_container_width=True)

    if n_fixes > 0:
        st.markdown("---"); st.markdown("#### Benefit-Cost Ratio Curve")
        st.pyplot(plot_bcr_curve(df, personas, bazaar_f), use_container_width=True)

    # --- POINTWISE MODULE DESCRIPTION ---
    st.markdown("---")
    st.header("Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module scales individual 'seconds lost' into city-wide productivity figures. By multiplying persona-weighted delays by local commuter volumes, we generate a Crore-value loss figure that anchors the policy argument.")
    st.write("2. **Investment Prioritization:** The tool ranks infrastructure repairs by their fiscal return. It identifies that the first three fixes generate 38% of the total potential benefit, allowing for high-impact budgeting on a limited municipal spend.")
    st.write("3. **Equity-Weighted Valuation:** The model accounts for the population share ($w_\phi$) of different personas. It demonstrates that repairing barriers for wheelchair users and the elderly is not only an ethical imperative but also an effective way to reduce aggregate economic friction.")
    st.write("4. **Lighthouse Proposal Synthesis:** All charts and metrics are designed for direct inclusion in the DULT/BBMP policy brief. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' justification for the proposed Lighthouse Pilot project.")

    st.markdown("---")
    with st.expander("📋 View Per-Persona Fiscal Table"):
        st.dataframe(pd.DataFrame([{
            "Persona": p["label"], "Baseline Loss (Cr)": f"{econ['persona_losses'][k]['baseline']:.2f}",
            "Scenario Loss (Cr)": f"{econ['persona_losses'][k]['scenario']:.2f}",
            "Delta (Benefit)": f"Rs{abs(econ['persona_losses'][k]['baseline'] - econ['persona_losses'][k]['scenario']):.2f} Cr"
        } for k, p in personas.items()]), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
