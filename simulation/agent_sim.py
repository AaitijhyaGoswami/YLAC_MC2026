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
# CONSTANTS
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
# SIMULATION CORE
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
# PLOT HELPERS
# -------------------------------------------------------------------------

def plot_traversal_comparison(results: dict, personas: dict, selected_key: str) -> plt.Figure:
    p   = personas[selected_key]
    res = results[selected_key]
    labels = ["Ideal\n(f=1 throughout)", "Actual\n(surveyed)"]
    values = [res["T_ideal"] / 60, res["T_actual"] / 60]
    colors = ["#4CAF50", p["color"]]
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.bar(labels, values, color=colors, width=0.45)
    for i, v in enumerate(values):
        ax.text(i, v + max(values)*0.02, f"{v:.1f} min", ha="center", color="white", fontweight="bold")
    ax.set_ylabel("Traversal time (min)", color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig

def plot_segment_breakdown(f_array: np.ndarray, result: dict, persona: dict) -> plt.Figure:
    F_COLORS = {1: "#9E9E9E", 2: "#4CAF50", 3: "#2196F3", 4: "#FF9800", 5: "#F44336"}
    x = np.arange(len(f_array)) * d
    colors = [F_COLORS.get(int(min(v, 5)), "#F44336") for v in f_array]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 4.5), sharex=True)
    ax1.bar(x, f_array, width=d*0.88, color=colors, align="edge")
    ax1.set_yticks([1, 2, 3, 4, 5])
    ax1.set_ylabel("f", color="white")
    ax2.bar(x, result["tau_i"], width=d*0.88, color=persona["color"], align="edge")
    ax2.axhline(d/persona["v0"], color="#4CAF50", linestyle=":", label="Ideal τᵢ")
    ax2.set_ylabel("τᵢ (s)", color="white")
    for ax in [ax1, ax2]:
        ax.set_facecolor("#1a1a1a")
        ax.tick_params(colors="white")
        ax.spines[:].set_visible(False)
        ax.axvline(300, color="#aaaaaa", linestyle="--", alpha=0.5)
    fig.patch.set_facecolor("#1a1a1a")
    fig.tight_layout()
    return fig

def plot_all_personas(results: dict, personas: dict) -> plt.Figure:
    labels = [p["label"] for p in personas.values()]
    taxes  = [results[k]["delta_tau"] / 60 for k in personas]
    colors = [p["color"] for p in personas.values()]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.barh(labels, taxes, color=colors, height=0.5)
    for i, v in enumerate(taxes):
        ax.text(v + max(taxes)*0.02, i, f"{v:.1f} min", va="center", color="white")
    ax.set_xlabel("Time Tax per trip (min)", color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.markdown("""
    The **Time Tax Simulator**’s chronological heart is the urban audit, translating static physical friction into the lived reality of systemic delay. This module measures more than distance. It quantifies the hidden “chronological penalty” of design neglect and calculates the **Time Tax of different commuter personas** across the 900m Yeshwantpur corridor. The simulator shows that infrastructure failure is not just an inconvenience but a kinetic drain that “steals” measurable seconds from each trip, turning individual micro-struggles into a macro-economic data point, using a rigorous Power-Law Friction-Velocity model.

This module is important for advocacy and policy-making on the topic of **Mobility Equity**, as it shows how bad design disproportionately impacts the most vulnerable users. The simulator offers insight into the regressiveness of the Time Tax on the least mobile, by modeling specific personas from high velocity delivery partners to friction-sensitive elderly commuters. This provides the empirical evidence for municipal authorities to re-frame urban repair as a “time-recovery” mission, prioritizing infrastructure investment on the basis of recovered productivity and the fundamental right to a dignified, seamless commute.
    """)

    # --- TECHNICAL MATH SECTION ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Fundamental Equations")
        st.markdown("We model effective velocity ($v_{\\text{eff}}$) as a non-linear decay function of infrastructure friction.")
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.latex(r"""
            \begin{aligned}
            \Delta\tau &: \text{The Time Tax (Cumulative seconds stolen per single trip)} \\
            v_0(\phi) &: \text{Ideal walking speed of the persona on a compliant footpath} \\
            f_i &: \text{Friction Index of the segment (1 = Standard, 5 = Failure)} \\
            k(\phi) &: \text{Persona-specific friction sensitivity exponent} \\
            d &: \text{Standard segment length used for discretization (12.5 meters)} \\
            N &: \text{Total number of audited segments across the 900m corridor (72)}
            \end{aligned}
        """)

        st.markdown("#### Piecewise Segmental Traversal")
        st.markdown("The model accounts for 'Impassability' where friction exceeds a persona's barrier threshold ($f_{\text{max}}$), forcing a vehicular Right-of-Way (ROW) detour.")
        st.latex(r"""
            $$\tau_i(\phi) = \frac{(d + \delta(\phi)) \cdot \alpha}{v_0(\phi)} & \text{if } f_i > f_{\text{max}} \quad \text{(ROW Detour)}$$
        """)
        st.latex(r"""
            \begin{aligned}
            \tau_i &: \text{Time required to navigate segment } i \text{ (seconds)} \\
            d &: \text{Unit segment length (12.5 meters)} \\
            \delta(\phi) &: \text{Detour distance penalty incurred entering traffic} \\
            \alpha &: \text{Safety penalty multiplier (1.5x speed reduction during detour)}
            \end{aligned}
        """)

        st.markdown("#### Detailed Sample Calculation")
        st.markdown("""
        To demonstrate the impact of the **Sensitivity Exponent ($k$)**, we compare an Able-Bodied Adult 
        against a Wheelchair User at a single $f=5$ systemic failure segment.
        """)
        
        st.markdown("**Persona A: Able-Bodied Adult** ($v_0=1.4, k=0.6, f_{max}=5$)")
        st.latex(r"\tau_{f=5} = \frac{12.5}{1.4 / 5^{0.6}} \approx \frac{12.5}{0.53} \approx 23.5\text{s} \quad (\text{Tax: } +14.6\text{s})")

        st.markdown("**Persona B: Wheelchair User** ($v_0=0.8, k=1.2, f_{max}=3$)")
        st.markdown("At $f=5$, the wheelchair exceeds $f_{max}$, triggering a vehicular Right-of-Way (ROW) detour:")
        st.latex(r"\tau_{f=5}^{ROW} = \frac{(12.5 + \delta) \cdot \alpha}{v_0} = \frac{(12.5 + 5) \cdot 1.5}{0.8} \approx 32.8\text{s} \quad (\text{Tax: } +17.2\text{s})")

    try:
        df       = load_audit_data()
        personas = load_personas()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Time Tax Simulator Controls")
    
    curr_p = personas[st.session_state.get("persona_sel", list(personas.keys())[0])]

    selected_key = st.sidebar.selectbox(
       "Commuter persona:", 
       options=list(personas.keys()), 
       format_func=lambda k: personas[k]["label"],
       key="persona_sel",
       help=rf"""
       Persona Calibration Metrics:  
       $v_0$ = {curr_p['v0']} m/s  
       $k$ = {curr_p['k']}  
       $f_{{max}}$ = {curr_p['f_max']}  
       $\alpha$ = {curr_p['alpha']}  
       $\delta$ = {curr_p['delta']} m
       """
       )
    p = personas[selected_key]

    n_fixes = st.sidebar.slider("Nodes brought to Tender S.U.R.E. standard (f=1):", 0, len(df), 0,
                                help="Simulates fixing obstacles in the 300m stretch ranked by severity")
    
    st.sidebar.markdown("**600m Bazaar Street stretch**")
    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Serious barrier — f=4 (Physical Barrier)": 4,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Minor repair — f=2 (Distracted Walk)": 2,
        "Full S.U.R.E. compliance — f=1": 1,
    }
    bazaar_label = st.sidebar.selectbox("Model Bazaar Street as:", list(sure_standards.keys()),
                                        help="Simulates gradual remediation of the continuous failure zone")
    bazaar_f = sure_standards[bazaar_label]

    # --- SIMULATION EXECUTION ---
    f_array = build_f_array(df, n_fixes, bazaar_f)
    results = {k: run_simulation(f_array, v) for k, v in personas.items()}
    res     = results[selected_key]

    st.markdown("---")

    # --- HEADLINE METRICS ---
    st.markdown(f"#### {p['label']}: Traversal Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ideal Time", f"{res['T_ideal'] / 60:.1f} min", help="Time taken if f=1 throughout")
    col2.metric("Actual Time", f"{res['T_actual'] / 60:.1f} min", delta=f"+{res['delta_tau'] / 60:.1f} min", delta_color="inverse", help="Time taken in simulated conditions")
    col3.metric("Time Tax Δτ", f"{res['delta_tau']:.0f} s", delta=f"+{res['delta_tau'] / res['T_ideal'] * 100:.0f}%", delta_color="inverse", help="Time lost due to simulated obstacles")
    col4.metric("ROW Detours", f"{res['n_detours']} segments", help="Segments forcing pedestrians into traffic")


    # --- CHARTS ---
    c_left, c_right = st.columns([1, 1.8])
    with c_left:
        st.markdown("#### Traversal Comparison")
        st.pyplot(plot_traversal_comparison(results, personas, selected_key), use_container_width=True)
    with c_right:
        st.markdown("#### Cross-Persona Time Tax")
        st.pyplot(plot_all_personas(results, personas), use_container_width=True)

    st.markdown("---")
    st.markdown("#### Per-Segment Friction & Time Breakdown")
    st.pyplot(plot_segment_breakdown(f_array, res, p), use_container_width=True)

    # --- POINTWISE DESCRIPTION ---
    st.markdown("---")
    st.header("Simulator Functionality")
    st.write("* **Agent-Based Path Simulation:** This module uses individual persona parameters (base speed $v_0$ and sensitivity $k$) to simulate how different citizens experience the same physical corridor. This moves beyond 'average' walking speeds to capture the reality of diverse commuters.")
    st.write("* **Power-Law Friction Scaling:** Unlike linear models, our simulator penalizes speed exponentially as infrastructure degrades. This accurately models how a 'doubling' of ground roughness leads to more than a doubling of traversal difficulty for vulnerable groups.")
    st.write("* **Vehicular Risk Quantification:** The simulator identifies 'Impassable' segments ($f > f_{max}$) where agents are forced into the vehicular Right-of-Way. It calculates the associated safety multiplier $\\alpha$, highlighting the direct correlation between poor footpaths and high-risk pedestrian-vehicle mixing.")
    st.write("* **Equity Gap Visualization:** By disaggregating the Time Tax across personas, the tool provides the quantitative evidence needed to argue for **Universal Design**. It demonstrates that infrastructure failure acts as a 'regressive tax' that is paid most heavily by those with limited mobility.")

    st.markdown("---")
    with st.expander("View Raw Simulation Data Table"):
        st.dataframe(pd.DataFrame({
            "Segment": range(1, len(f_array) + 1),
            "Friction (f)": f_array,
            "Speed (m/s)": np.round(res["v_eff_i"], 3),
            "Time (s)": np.round(res["tau_i"], 2),
            "Detour Triggered": res["is_detour"]
        }), hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
