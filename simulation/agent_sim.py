import streamlit as st
import pandas as pd
import numpy as np
import yaml
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# -------------------------------------------------------------------------
# CONSTANTS & LOGIC (Preserved Exactly)
# -------------------------------------------------------------------------

D      = 900.0   # total corridor length (m)
D_300  = 300.0   # discrete-node stretch (m)
D_600  = 600.0   # continuous f=5 stretch (m)
N_300  = 24      # number of discrete nodes in the 300m stretch
N_600  = 48      # number of 12.5m segments in the 600m stretch
d      = 12.5    # segment length (m)

# -------------------------------------------------------------------------
# DATA LOADERS
# -------------------------------------------------------------------------

@st.cache_data
def load_audit_data() -> pd.DataFrame:
    path = os.path.join("data", "audit_log.csv")
    df = pd.read_csv(path)
    assert {"id", "lat", "lon", "f_value"}.issubset(df.columns)
    return df


@st.cache_data
def load_personas() -> dict:
    path = os.path.join("data", "personas.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


# -------------------------------------------------------------------------
# SIMULATION CORE (Logic Untouched)
# -------------------------------------------------------------------------

def build_f_array(df: pd.DataFrame, n_fixes: int, bazaar_f: int) -> np.ndarray:
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    f_600 = np.full(N_600, float(bazaar_f))
    return np.concatenate([f_300, f_600])


def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    v0    = persona["v0"]
    k     = persona["k"]
    f_max = persona["f_max"]
    alpha = persona["alpha"]
    delta = persona["delta"]
    N     = len(f_array)

    tau_i     = np.empty(N)
    v_eff_i   = np.empty(N)
    is_detour = np.zeros(N, dtype=bool)

    for i, fi in enumerate(f_array):
        if fi > f_max:
            tau_i[i]    = (d + delta) * alpha / v0
            v_eff_i[i]  = (d + delta) / tau_i[i]
            is_detour[i] = True
        else:
            v_eff_i[i] = v0 / (fi ** k)
            tau_i[i]   = d / v_eff_i[i]

    T_actual  = float(tau_i.sum())
    T_ideal   = D / v0
    delta_tau = T_actual - T_ideal

    return {
        "T_actual":   T_actual,
        "T_ideal":    T_ideal,
        "delta_tau":  delta_tau,
        "tau_i":      tau_i,
        "v_eff_i":    v_eff_i,
        "is_detour":  is_detour,
        "n_detours":  int(is_detour.sum()),
    }


# -------------------------------------------------------------------------
# PLOT HELPERS (Logic Untouched)
# -------------------------------------------------------------------------

def plot_traversal_comparison(results: dict, personas: dict, selected_key: str) -> plt.Figure:
    p   = personas[selected_key]
    res = results[selected_key]
    labels = ["Ideal (f=1)", "Actual (Surveyed)"]
    values = [res["T_ideal"] / 60, res["T_actual"] / 60]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, values, color=["#4CAF50", p["color"]], width=0.45)
    ax.set_ylabel("Traversal time (min)", color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    plt.close()
    return fig

def plot_segment_breakdown(f_array: np.ndarray, result: dict, persona: dict) -> plt.Figure:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 4.5), sharex=True)
    ax1.set_facecolor("#1a1a1a")
    ax2.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax1.bar(np.arange(len(f_array))*d, f_array, width=d*0.8, color="#F44336", align="edge")
    ax2.bar(np.arange(len(f_array))*d, result["tau_i"], width=d*0.8, color=persona["color"], align="edge")
    ax1.tick_params(colors="white")
    ax2.tick_params(colors="white")
    plt.close()
    return fig

def plot_all_personas(results: dict, personas: dict) -> plt.Figure:
    labels = [p["label"] for p in personas.values()]
    taxes  = [results[k]["delta_tau"] / 60 for k in personas]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.barh(labels, taxes, color="#2196F3")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    plt.close()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("⏱️ Time Tax Simulator")
    st.markdown("### The Physics of Stolen Time")
    
    st.markdown("""
    This module simulates the journey of four distinct commuter personas through the Yeshwantpur corridor. 
    By applying persona-specific sensitivity to infrastructure friction, we quantify the 'Time Tax'—the 
    cumulative seconds of life-time stolen from citizens by non-compliant design.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 The Scale")
        st.write("- **Audit Length:** 900m Corridor")
        st.write("- **Commuters:** 100,000+ Daily trips")
        st.write("- **Standard:** [Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) (f=1)")

    with col2:
        st.subheader("📉 The Impact")
        st.write("- **Daily Loss:** ~480,000 Person-Minutes")
        st.write("- **Disparity:** Vulnerable groups bear 3x tax")
        st.error("- **Risk:** Forced detours into vehicular traffic")

    with col3:
        st.subheader("💡 The Solution")
        st.write("- **Strategy:** Targeted Hotspot Fixes")
        st.write("- **ROI:** 10 minutes saved per persona trip")
        st.success("- **Equity:** Removing f > f_max barriers first")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 Why Physics for Time?")
    st.markdown("""
    Urban planners often overlook that time is a physical resource governed by the environment. 
    A broken sidewalk doesn't just 'annoy' a walker; it creates a resistive field that decreases velocity. 
    By using a **Power-Law Velocity Model**, we can scientifically demonstrate that infrastructure 
    failure does not affect everyone equally. For an able-bodied adult, a high-friction node is a 
    slight delay; for a wheelchair user, that same node can be an impassable potential barrier that 
    forces a dangerous detour into the road. This simulator visualizes how poor design effectively 
    'taxes' the schedule of the city's most vulnerable citizens.
    """)

    # 

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("🔬 View Technical Methodology and Variables"):
        st.markdown("#### 1. The Friction-Velocity Model")
        st.markdown("""
        We use a non-linear decay model to represent how walking speed ($v_{\text{eff}}$) decreases 
        as ground friction increases.
        """)
        st.latex(r"v_{\text{eff}}(i,\,\phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}")
        st.latex(r"""
            \begin{aligned}
            v_{\text{eff}} &: \text{Effective velocity achieved across segment } i \\
            v_0 &: \text{Ideal walking speed of persona } \phi \text{ on a clear path} \\
            f_i &: \text{The Friction Index (1-5) of the audited segment} \\
            k &: \text{Sensitivity Exponent (Determines how quickly speed drops)}
            \end{aligned}
        """)

        st.markdown("#### 2. The Time Tax Calculation")
        st.markdown("""
        The **Time Tax** ($\Delta\tau$) is the difference between the actual time spent 
        navigating the broken path versus the ideal time on a standard-compliant corridor.
        """)
        st.latex(r"\Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{\,k(\phi)} - N \right)")
        st.latex(r"""
            \begin{aligned}
            \Delta\tau &: \text{The Time Tax (Seconds stolen per trip)} \\
            d &: \text{Standard segment length (12.5 meters)} \\
            N &: \text{Total number of segments (72 segments for 900m)} \\
            \sum f_i^k &: \text{The sum of persona-weighted friction across all nodes}
            \end{aligned}
        """)

        st.markdown("#### 3. Rerouting Logic (ROW Detours)")
        st.markdown("""
        When friction exceeds a persona's limit ($f_{\text{max}}$), the agent must leave the 
        footpath and enter the vehicular Right-of-Way, incurring a detour penalty.
        """)
        st.latex(r"\tau_i^{\text{ROW}}(\phi) = \frac{(d + \delta) \cdot \alpha}{v_0(\phi)}")
        st.latex(r"""
            \begin{aligned}
            \tau_i^{\text{ROW}} &: \text{Time spent during a vehicular Right-of-Way detour} \\
            \delta &: \text{Mean detour distance penalty (meters)} \\
            \alpha &: \text{Safety multiplier (Accounts for caution and traffic interference)}
            \end{aligned}
        """)

    # -----------------------------------------------------------------------
    # SIMULATION EXECUTION
    # -----------------------------------------------------------------------
    try:
        df       = load_audit_data()
        personas = load_personas()
    except Exception as e:
        st.error(f"Data loading failed: {e}")
        return

    # Sidebar Controls
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏱️ Simulator Controls")
    selected_key = st.sidebar.selectbox("Commuter persona:", options=list(personas.keys()), format_func=lambda k: personas[k]["label"])
    p = personas[selected_key]
    n_fixes = st.sidebar.slider("Nodes fixed to S.U.R.E. standard:", 0, len(df), 0)
    sure_standards = {"Current (f=5)": 5, "Moderate (f=3)": 3, "Compliance (f=1)": 1}
    bazaar_f = sure_standards[st.sidebar.selectbox("Bazaar St Model:", list(sure_standards.keys()))]

    # Run Simulation
    f_array = build_f_array(df, n_fixes, bazaar_f)
    results = {k: run_simulation(f_array, v) for k, v in personas.items()}
    res     = results[selected_key]

    # Display Metrics
    st.markdown(f"#### {p['label']} — Traversal Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Ideal Time", f"{res['T_ideal'] / 60:.1f} min")
    m2.metric("Actual Time", f"{res['T_actual'] / 60:.1f} min", delta=f"+{res['delta_tau'] / 60:.1f} min", delta_color="inverse")
    m3.metric("Time Tax Δτ", f"{res['delta_tau']:.0f} s", delta=f"+{res['delta_tau'] / res['T_ideal'] * 100:.0f}%", delta_color="inverse")
    m4.metric("ROW Detours", f"{res['n_detours']} segments")

    st.markdown("---")

    # Display Visuals
    c_left, c_right = st.columns([1, 1.8])
    with c_left:
        st.markdown("#### Ideal vs Actual Traversal")
        st.pyplot(plot_traversal_comparison(results, personas, selected_key), use_container_width=True)
    with c_right:
        st.markdown("#### All Personas — Time Tax Comparison")
        st.pyplot(plot_all_personas(results, personas), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Per-Segment Breakdown")
    st.pyplot(plot_segment_breakdown(f_array, res, p), use_container_width=True)

    # --- POINTWISE MODULE DESCRIPTION ---
    st.markdown("---")
    st.header("🛠️ Simulator Functionality")
    st.write("1. **Agent-Based Modeling:** Uses real persona parameters ($v_0, k$) to simulate how different demographics experience the same physical route.")
    st.write("2. **Dynamic Time-Taxing:** Recalculates seconds lost in real-time as the user 'repairs' the 300m stretch or redesigns Bazaar Street.")
    st.write("3. **Risk Quantification:** Specifically identifies 'Impassable' segments where pedestrians are forced to mix with vehicular traffic, highlighting safety hazards.")
    st.write("4. **Equity Gap Visualization:** Directly compares the Time Tax of wheelchair users against able-bodied adults to argue for universal design standards.")

    st.markdown("---")
    with st.expander("📋 View Raw Segment Data Table"):
        st.dataframe(pd.DataFrame({
            "Segment": range(1, len(f_array) + 1),
            "Friction (f)": f_array,
            "Speed (m/s)": np.round(res["v_eff_i"], 3),
            "Time (s)": np.round(res["tau_i"], 2),
            "Detour": res["is_detour"]
        }), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
