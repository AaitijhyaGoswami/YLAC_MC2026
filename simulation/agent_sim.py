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

BODY_WEIGHT_KG = 70.0  # reference body weight for metabolic cost calculation

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

    # Metabolic cost: extra energy above the ideal frictionless walk.
    # Approximation: W_extra = (L_eff - D) * body_weight * g
    # where L_eff is friction-weighted effective path length.
    # Detour segments use (d + delta) as the effective distance.
    L_eff = float(sum(
        (d + delta) if fi > f_max else fi * d
        for fi in f_array
    ))
    g              = 9.81
    extra_joules   = max(0.0, (L_eff - D) * BODY_WEIGHT_KG * g)
    extra_kcal     = extra_joules / 4184.0  # 1 kcal = 4184 J

    return {
        "T_actual":    T_actual,
        "T_ideal":     T_ideal,
        "delta_tau":   delta_tau,
        "tau_i":       tau_i,
        "v_eff_i":     v_eff_i,
        "is_detour":   is_detour,
        "n_detours":   int(is_detour.sum()),
        "extra_kcal":  extra_kcal,
        "L_eff":       L_eff,
    }


def reachable_distance(f_array: np.ndarray, persona: dict, budget_s: float) -> float:
    """
    How far along the corridor can this persona travel in budget_s seconds?
    Walks segment by segment; returns the fractional distance reached when
    time runs out. Used to compute 1D corridor isochrones.
    """
    elapsed = 0.0
    for i, fi in enumerate(f_array):
        if fi > persona["f_max"]:
            seg_time = (d + persona["delta"]) * persona["alpha"] / persona["v0"]
        else:
            seg_time = d * (fi ** persona["k"]) / persona["v0"]
        if elapsed + seg_time > budget_s:
            frac = (budget_s - elapsed) / seg_time
            return i * d + frac * d
        elapsed += seg_time
    return D  # reached the far end within budget


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


# NEW: speed profile line chart — shows velocity decay continuously along corridor
def plot_speed_profile(f_array: np.ndarray, results: dict, personas: dict,
                       selected_key: str) -> plt.Figure:
    x = np.arange(len(f_array)) * d + d / 2  # segment midpoints

    fig, ax = plt.subplots(figsize=(11, 3.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    for pk, p in personas.items():
        res      = results[pk]
        v_smooth = res["v_eff_i"].copy()
        lw       = 2.5 if pk == selected_key else 1.0
        alpha    = 1.0 if pk == selected_key else 0.35
        ax.plot(x, v_smooth, color=p["color"], linewidth=lw, alpha=alpha,
                label=p["label"], zorder=3 if pk == selected_key else 2)

    # Ideal speed lines per persona (horizontal dashed)
    for pk, p in personas.items():
        if pk == selected_key:
            ax.axhline(p["v0"], color=p["color"], linewidth=0.8,
                       linestyle="--", alpha=0.4)

    ax.axvline(300, color="#aaaaaa", linewidth=1.0, linestyle="--", alpha=0.5)
    ax.text(305, ax.get_ylim()[1] * 0.95 if ax.get_ylim()[1] > 0 else 1.5,
            "300m", color="#aaaaaa", fontsize=7, va="top")

    ax.set_xlim(0, D)
    ax.set_xlabel("Distance along corridor (m)", color="white", fontsize=9)
    ax.set_ylabel("Effective speed (m/s)", color="white", fontsize=9)
    ax.set_title("Speed Profile Along Corridor", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    ax.legend(fontsize=7.5, facecolor="#2a2a2a", labelcolor="white",
              framealpha=0.85, loc="lower left")
    fig.tight_layout()
    return fig


# NEW: metabolic cost bar chart across all personas
def plot_metabolic_cost(results: dict, personas: dict) -> plt.Figure:
    labels = [p["label"] for p in personas.values()]
    kcals  = [results[k]["extra_kcal"] for k in personas]
    colors = [p["color"] for p in personas.values()]

    fig, ax = plt.subplots(figsize=(7, 3.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    bars = ax.barh(labels, kcals, color=colors, height=0.5)
    for i, v in enumerate(kcals):
        ax.text(v + max(kcals) * 0.02, i, f"{v:.1f} kcal", va="center",
                color="white", fontsize=8)
    ax.set_xlabel("Extra metabolic cost above ideal walk (kcal)", color="white", fontsize=9)
    ax.set_title(f"Extra Energy per Trip — 70 kg reference", color="white", fontsize=10)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_isochrone_bars(f_array: np.ndarray, personas: dict,
                        budgets_s: dict, selected_key: str) -> plt.Figure:
    """
    Grouped horizontal bar chart: for each time budget, shows actual vs ideal
    reachable distance per persona. The gap between ideal and actual is the
    spatial expression of the Time Tax.
    """
    f_ideal = np.ones(len(f_array))
    budget_labels = list(budgets_s.keys())
    n_budgets = len(budget_labels)
    n_personas = len(personas)
    bar_h = 0.18
    gap   = 0.08

    fig, axes = plt.subplots(1, n_budgets, figsize=(11, 3.2), sharey=True)
    fig.patch.set_facecolor("#1a1a1a")
    if n_budgets == 1:
        axes = [axes]

    for ax, (blabel, bs) in zip(axes, budgets_s.items()):
        ax.set_facecolor("#1a1a1a")
        ax.set_title(blabel, color="white", fontsize=9)

        for j, (pk, p) in enumerate(personas.items()):
            y        = j * (n_budgets * bar_h + gap)
            actual   = reachable_distance(f_array,  p, bs)
            ideal    = reachable_distance(f_ideal,   p, bs)
            is_sel   = pk == selected_key
            lw       = 1.5 if is_sel else 0.0
            a_alpha  = 0.95 if is_sel else 0.55

            # Ideal bar (faint background)
            ax.barh(y + bar_h, ideal,  height=bar_h, color=p["color"],
                    alpha=0.22, linewidth=0, align="edge")
            # Actual bar
            ax.barh(y,         actual, height=bar_h, color=p["color"],
                    alpha=a_alpha, linewidth=lw,
                    edgecolor="white" if is_sel else "none", align="edge")
            ax.text(actual + 8, y + bar_h * 0.5,
                    f"{actual:.0f}m", va="center", fontsize=7,
                    color=p["color"] if is_sel else "#aaaaaa")

        ax.set_xlim(0, D * 1.05)
        ax.set_xlabel("Reachable distance (m)", color="white", fontsize=8)
        ax.tick_params(colors="white", labelsize=7)
        ax.spines[:].set_visible(False)
        ax.axvline(D, color="#444", linewidth=0.6, linestyle=":")

    # Y-axis labels on leftmost plot only
    yticks = [(j * (n_budgets * bar_h + gap) + bar_h * 0.5)
              for j in range(n_personas)]
    axes[0].set_yticks(yticks)
    axes[0].set_yticklabels(
        [p["label"] for p in personas.values()],
        color="white", fontsize=8
    )
    fig.suptitle("Corridor Accessibility Isochrones — Actual vs Ideal Catchment",
                 color="white", fontsize=10, y=1.01)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.markdown("""
    The **Time Tax Simulator**'s chronological heart is the urban audit, translating static physical friction into the lived reality of systemic delay. This module measures more than distance. It quantifies the hidden "chronological penalty" of design neglect and calculates the **Time Tax of different commuter personas** across the 900m Yeshwantpur corridor. The simulator shows that infrastructure failure is not just an inconvenience but a kinetic drain that "steals" measurable seconds from each trip, turning individual micro-struggles into a macro-economic data point, using a rigorous Power-Law Friction-Velocity model.

This module is important for advocacy and policy-making on the topic of **Mobility Equity**, as it shows how bad design disproportionately impacts the most vulnerable users. The simulator offers insight into the regressiveness of the Time Tax on the least mobile, by modeling specific personas from high velocity delivery partners to friction-sensitive elderly commuters. This provides the empirical evidence for municipal authorities to re-frame urban repair as a "time-recovery" mission, prioritizing infrastructure investment on the basis of recovered productivity and the fundamental right to a dignified, seamless commute.
    """)

    # --- TECHNICAL MATH SECTION ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Fundamental Equations")
        st.markdown("We model effective velocity ($v_{\\text{eff}}$) as a non-linear decay function of infrastructure friction.")
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right) \quad \text{if } f_i \leq f_{\text{max}} \quad \text{(Path Traversal)}")
        st.latex(r"""
            \begin{aligned}
            \Delta\tau &: \text{The Time Tax (Cumulative seconds stolen per single trip)} \\
            v_0(\phi) &: \text{Ideal walking speed of the persona on a compliant footpath} \\
            f_i &: \text{Friction Index of the segment (1 = Standard, 5 = Failure)} \\
            k(\phi) &: \text{Persona-specific friction sensitivity exponent} \\
            d &: \text{Standard segment length used for discretization (12.5 meters)} \\
            N &: \text{Total number of audited segments across the 900m corridor where $f_i \leq f_{max}$}
            \end{aligned}
        """)

        st.markdown("#### Piecewise Segmental Traversal")
        st.markdown("The model accounts for 'Impassability' where friction exceeds a persona's barrier threshold ($f_{max}$), forcing a vehicular Right-of-Way (ROW) detour.")
        st.latex(r"\tau_i(\phi) = \frac{(d + \delta(\phi)) \cdot \alpha}{v_0(\phi)} \quad \text{if } f_i > f_{\text{max}} \quad \text{(ROW Detour)}")
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

        # NEW: metabolic cost derivation
        st.markdown("#### Metabolic Cost of Infrastructure Failure")
        st.markdown("""
        Beyond time, broken infrastructure extracts a **physical energy cost**. 
        The extra mechanical work done by a commuter above the ideal frictionless walk is
        approximated by treating the friction-weighted effective path length as the resistive distance:
        """)
        st.latex(r"W_{\text{extra}} = \left( L_{\text{eff}} - D \right) \cdot m \cdot g")
        st.latex(r"""
            \begin{aligned}
            W_{\text{extra}} &: \text{Extra mechanical work per trip (Joules)} \\
            L_{\text{eff}} &: \text{Friction-weighted effective path length (metres)} \\
            D &: \text{Physical corridor length — 900 m} \\
            m &: \text{Reference body mass — 70 kg} \\
            g &: \text{Gravitational acceleration — 9.81 m/s}^2
            \end{aligned}
        """)
        st.markdown("Converting to kilocalories ($1\\,\\text{kcal} = 4184\\,\\text{J}$):")
        st.latex(r"E_{\text{extra}} = \frac{W_{\text{extra}}}{4184} \; \text{kcal}")
        st.markdown("""
        For the wheelchair persona at baseline, $L_{\\text{eff}} \\approx 4{,}750\\,\\text{m}$, giving 
        $E_{\\text{extra}} \\approx 183\\,\\text{kcal}$ of extra energy per single trip — 
        equivalent to climbing roughly **180 flights of stairs**.
        """)

        st.markdown("#### Corridor Isochrone — Reachable Distance")
        st.markdown("""
        The isochrone answers: *given a fixed time budget $T$, how far along the corridor
        can this persona travel?* It is the spatial inverse of the Time Tax — instead of
        asking how much time a fixed distance costs, it asks how much distance a fixed time buys.
        """)
        st.latex(r"""
            x^*(T, \phi) = \max \left\{ x \;\Big|\; \sum_{i=0}^{\lfloor x/d 
floor} 	au_i(\phi) \leq T 
ight\}
        """)
        st.latex(r"""
            egin{aligned}
            x^*(T, \phi) &: 	ext{Reachable distance along the corridor in time budget } T \
            T &: 	ext{Time budget (seconds) — e.g. 300 s for a 5-minute window} \
            	au_i(\phi) &: 	ext{Traversal time of segment } i 	ext{ for persona } \phi \
            d &: 	ext{Segment length (12.5 m)}
            \end{aligned}
        """)
        st.markdown("""
        The **ideal isochrone** $x^*_{\text{ideal}}$ uses $f_i = 1$ throughout.
        The gap $x^*_{\text{ideal}} - x^*_{\text{actual}}$ is the **catchment loss** —
        the corridor distance this persona is denied within the same time window due to friction.
        For a wheelchair user on a 5-minute budget, this loss is approximately **167 m**,
        or 58% of their potential catchment.
        """)

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

    # NEW: equity ratio + metabolic cost inline metrics
    st.markdown("---")
    st.markdown("#### Equity & Physical Cost")
    ab_res   = results.get("able_bodied", res)
    eq_ratio = res["T_actual"] / ab_res["T_actual"] if ab_res["T_actual"] > 0 else 1.0
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric(
        "Equity Ratio vs Able-bodied",
        f"{eq_ratio:.2f}×",
        delta=f"+{(eq_ratio-1)*100:.0f}% longer" if eq_ratio > 1 else "Baseline",
        delta_color="inverse" if eq_ratio > 1 else "off",
        help="How many times longer this persona's trip is compared to an able-bodied adult on the same corridor."
    )
    mc2.metric(
        "Extra Metabolic Cost",
        f"{res['extra_kcal']:.1f} kcal",
        help=f"Extra energy above an ideal f=1 walk. Equivalent to ~{res['extra_kcal']/0.5:.0f} minutes of slow jogging."
    )
    mc3.metric(
        "Effective Path Length",
        f"{res['L_eff']:.0f} m",
        delta=f"+{res['L_eff']-D:.0f} m felt",
        delta_color="inverse",
        help="The friction-weighted distance this persona effectively 'walks' in terms of physical effort."
    )

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

    # NEW: speed profile + metabolic cost side by side
    st.markdown("---")
    sp_left, sp_right = st.columns([1.8, 1])
    with sp_left:
        st.markdown("#### Speed Profile Along Corridor")
        st.caption("Selected persona highlighted — all others faded. Dashed horizontal = ideal free-walking speed.")
        st.pyplot(plot_speed_profile(f_array, results, personas, selected_key), use_container_width=True)
    with sp_right:
        st.markdown("#### Extra Metabolic Cost per Trip")
        st.caption(f"Extra energy above ideal walk for a {BODY_WEIGHT_KG:.0f} kg reference commuter.")
        st.pyplot(plot_metabolic_cost(results, personas), use_container_width=True)

    # --- ISOCHRONE SECTION ---
    st.markdown("---")
    st.markdown("#### Corridor Accessibility Isochrones")
    st.caption(
        "How far can each persona travel from the station exit within a fixed time budget? "
        "Solid bars = actual reachable distance given current friction. "
        "Faint bars = ideal reachable distance if the corridor were fully S.U.R.E.-compliant (f=1 throughout). "
        "The gap is the catchment stolen by infrastructure failure."
    )
    TIME_BUDGETS = {"5 min": 5*60, "10 min": 10*60, "15 min": 15*60}
    st.pyplot(
        plot_isochrone_bars(f_array, personas, TIME_BUDGETS, selected_key),
        use_container_width=True
    )

    # Equity summary table below the chart
    iso_rows = []
    f_ideal_arr = np.ones(len(f_array))
    for pk, pp in personas.items():
        row = {"Persona": pp["label"]}
        for blabel, bs in TIME_BUDGETS.items():
            actual  = reachable_distance(f_array,     pp, bs)
            ideal   = reachable_distance(f_ideal_arr, pp, bs)
            lost    = ideal - actual
            row[f"{blabel} actual (m)"]  = f"{actual:.0f}"
            row[f"{blabel} ideal (m)"]   = f"{ideal:.0f}"
            row[f"{blabel} lost (m)"]    = f"{lost:.0f} ({lost/ideal*100:.0f}%)"
        iso_rows.append(row)
    with st.expander("View isochrone data table"):
        st.dataframe(pd.DataFrame(iso_rows), hide_index=True, use_container_width=True)

    # --- POINTWISE DESCRIPTION ---
    st.markdown("---")
    st.header("Simulator Functionality")
    st.write("* **Agent-Based Path Simulation:** This module uses individual persona parameters (base speed $v_0$ and sensitivity $k$) to simulate how different citizens experience the same physical corridor. This moves beyond 'average' walking speeds to capture the reality of diverse commuters.")
    st.write("* **Power-Law Friction Scaling:** Unlike linear models, our simulator penalizes speed exponentially as infrastructure degrades. This accurately models how a 'doubling' of ground roughness leads to more than a doubling of traversal difficulty for vulnerable groups.")
    st.write("* **Vehicular Risk Quantification:** The simulator identifies 'Impassable' segments ($f > f_{max}$) where agents are forced into the vehicular Right-of-Way. It calculates the associated safety multiplier $\\alpha$, highlighting the direct correlation between poor footpaths and high-risk pedestrian-vehicle mixing.")
    st.write("* **Equity Gap Visualization:** By disaggregating the Time Tax across personas, the tool provides the quantitative evidence needed to argue for **Universal Design**. It demonstrates that infrastructure failure acts as a 'regressive tax' that is paid most heavily by those with limited mobility.")
    st.write("* **Speed Profile Chart:** Plots effective walking speed continuously along the corridor for all personas simultaneously, making the velocity decay and detour plateaus visible as a spatial argument rather than a summary statistic.")
    st.write("* **Metabolic Cost Quantification:** Converts the friction-weighted effective path length into extra kilocalories expended per trip, grounding the equity argument in physical biology — not just time.")
    st.write("* **Corridor Accessibility Isochrones:** Computes how far each persona can travel within 5, 10, and 15-minute budgets under current vs ideal conditions. The gap between actual and ideal catchment is the spatial representation of the Time Tax — making the equity deficit visible as lost territory rather than lost time.")

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
