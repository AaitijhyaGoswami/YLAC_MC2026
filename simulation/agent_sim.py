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
d      = 12.5    # segment length (m) — D_300/N_300 = D_600/N_600 = 12.5

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
    """
    Build the full f-value array for the 900m route.

    300m stretch : 24 discrete nodes from audit_log.csv (d = 12.5m each)
    600m stretch : 48 uniform segments at bazaar_f (d = 12.5m each)

    n_fixes : top-N nodes in the 300m stretch set to f=1 (S.U.R.E. standard)
              ranked by descending f_value
    """
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300 = f_300.copy()
        f_300[fix_idx] = 1.0
    f_600 = np.full(N_600, float(bazaar_f))
    return np.concatenate([f_300, f_600])


def run_simulation(f_array: np.ndarray, persona: dict) -> dict:
    """
    Compute traversal time and Time Tax for one persona over f_array.

    Physics:
        v_eff(i) = v0 / f_i^k               (power-law velocity model)
        τ_i      = d / v_eff(i)             (segment traversal time)
        τ_i^ROW  = (d + δ) · α / v0        (ROW detour if f_i > f_max)

        T_actual = Σ τ_i
        T_ideal  = D / v0                   (all f=1, S.U.R.E.-compliant)
        Δτ       = T_actual − T_ideal

    Returns
    -------
    dict with keys:
        T_actual      : float  — total actual traversal time (s)
        T_ideal       : float  — ideal traversal time (s)
        delta_tau     : float  — Time Tax per trip (s)
        tau_i         : array  — per-segment traversal time (s)
        v_eff_i       : array  — per-segment effective speed (m/s)
        is_detour     : array  — bool, True where ROW detour triggered
        n_detours     : int    — number of impassable segments
    """
    v0    = persona["v0"]
    k     = persona["k"]
    f_max = persona["f_max"]
    alpha = persona["alpha"]
    delta = persona["delta"]
    N     = len(f_array)

    tau_i    = np.empty(N)
    v_eff_i  = np.empty(N)
    is_detour = np.zeros(N, dtype=bool)

    for i, fi in enumerate(f_array):
        if fi > f_max:
            # Impassable — reroute into vehicular ROW
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

def plot_traversal_comparison(
    results: dict, personas: dict, selected_key: str
) -> plt.Figure:
    """
    Bar chart: T_ideal vs T_actual for the selected persona.
    Handles the fully-compliant edge case (Δτ = 0) gracefully.
    """
    p   = personas[selected_key]
    res = results[selected_key]

    labels = [
        "Ideal\n(f=1 throughout\nS.U.R.E. standard)",
        "Actual\n(surveyed conditions)",
    ]
    values = [res["T_ideal"] / 60, res["T_actual"] / 60]
    colors = ["#4CAF50", p["color"]]

    fig, ax = plt.subplots(figsize=(5, 4))
    bars = ax.bar(labels, values, color=colors, width=0.45, linewidth=0)
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + max(values) * 0.02,
            f"{val:.1f} min",
            ha="center", va="bottom",
            fontsize=10, color="white", fontweight="bold",
        )

    # Only annotate Time Tax if it is non-trivial
    delta_min = res["delta_tau"] / 60
    if delta_min > 0.05:
        ax.annotate(
            f"Time Tax\n+{delta_min:.1f} min",
            xy=(1, res["T_actual"] / 60),
            xytext=(1.3, (res["T_ideal"] + res["T_actual"]) / 2 / 60),
            fontsize=8, color="#FF9800",
            arrowprops=dict(arrowstyle="->", color="#FF9800", lw=1.2),
        )
    else:
        ax.text(0.5, 0.92, "✅ Corridor fully S.U.R.E.-compliant",
                ha="center", va="top", transform=ax.transAxes,
                fontsize=8, color="#4CAF50")

    ax.set_ylabel("Traversal time (min)", fontsize=9, color="white")
    ax.set_ylim(0, max(values) * 1.30 if max(values) > 0 else 1.0)
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=9)
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_segment_breakdown(
    f_array: np.ndarray, result: dict, persona: dict
) -> plt.Figure:
    """
    Two-panel plot:
        Top   — f-value per segment, coloured by level
        Bottom — per-segment traversal time τ_i
    Detour segments marked with a cross-hatch.
    """
    F_COLORS = {1: "#9E9E9E", 2: "#4CAF50", 3: "#2196F3",
                4: "#FF9800", 5: "#F44336"}

    x      = np.arange(len(f_array)) * d
    colors = [F_COLORS.get(int(min(v, 5)), "#F44336") for v in f_array]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 4.5), sharex=True)

    # --- Top: friction ---
    ax1.bar(x, f_array, width=d * 0.88, color=colors, align="edge", linewidth=0)
    ax1.axvline(300, color="#aaaaaa", linewidth=1, linestyle="--", alpha=0.5)
    ax1.set_ylim(0, 5.8)
    ax1.set_ylabel("f", fontsize=9, color="white")
    ax1.set_yticks([1, 2, 3, 4, 5])
    ax1.set_facecolor("#1a1a1a")
    ax1.tick_params(colors="white", labelsize=8)
    ax1.spines[:].set_visible(False)
    ax1.text(150, 5.4, "300m stretch", ha="center", fontsize=7.5, color="#aaaaaa")
    ax1.text(600, 5.4, "600m Bazaar Street", ha="center", fontsize=7.5, color="#aaaaaa")

    # --- Bottom: τ_i ---
    tau_colors = [
        "#FF5722" if det else persona["color"]
        for det in result["is_detour"]
    ]
    ax2.bar(x, result["tau_i"], width=d * 0.88, color=tau_colors,
            align="edge", linewidth=0)
    ax2.axvline(300, color="#aaaaaa", linewidth=1, linestyle="--", alpha=0.5)

    # Ideal τ reference line
    tau_ideal = d / persona["v0"]
    ax2.axhline(tau_ideal, color="#4CAF50", linewidth=1.2, linestyle=":",
                label=f"Ideal τᵢ = {tau_ideal:.1f}s (S.U.R.E.)")
    ax2.legend(fontsize=7, facecolor="#2a2a2a", labelcolor="white", framealpha=0.8)

    ax2.set_ylabel("τᵢ (s)", fontsize=9, color="white")
    ax2.set_xlabel("Distance along route (m)", fontsize=9, color="white")
    # Guard against collapsed y-axis when all segments are identical
    tau_range = result["tau_i"].max() - result["tau_i"].min()
    if tau_range < 0.1:
        ax2.set_ylim(0, result["tau_i"].max() * 1.5 if result["tau_i"].max() > 0 else 1.0)
    ax2.set_facecolor("#1a1a1a")
    ax2.tick_params(colors="white", labelsize=8)
    ax2.spines[:].set_visible(False)

    # Detour annotation
    if result["n_detours"] > 0:
        det_x = x[result["is_detour"]]
        ax2.scatter(
            det_x + d / 2, result["tau_i"][result["is_detour"]],
            marker="x", color="#FF5722", s=30, zorder=5,
            label=f"{result['n_detours']} ROW detour(s)",
        )
        ax2.legend(fontsize=7, facecolor="#2a2a2a", labelcolor="white", framealpha=0.8)

    fig.patch.set_facecolor("#1a1a1a")
    fig.tight_layout()
    return fig


def plot_all_personas(results: dict, personas: dict) -> plt.Figure:
    """
    Horizontal bar chart of Time Tax per persona (minutes).
    Handles the fully-compliant edge case (all Δτ = 0) gracefully.
    """
    labels = [p["label"] for p in personas.values()]
    taxes  = [results[k]["delta_tau"] / 60 for k in personas]
    colors = [p["color"] for p in personas.values()]

    max_tax = max(taxes) if max(taxes) > 0 else 1.0   # floor at 1 min

    fig, ax = plt.subplots(figsize=(7, 3.2))
    bars = ax.barh(labels, taxes, color=colors, height=0.5, linewidth=0)
    for bar, val in zip(bars, taxes):
        label_x = val + max_tax * 0.02
        ax.text(
            label_x, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f} min",
            va="center", fontsize=8.5, color="white",
        )

    if max(taxes) == 0:
        ax.text(0.5, 0.5, "✅ Full S.U.R.E. compliance — Time Tax = 0",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=10, color="#4CAF50")

    ax.set_xlim(0, max_tax * 1.25)
    ax.set_xlabel("Time Tax per trip (min)", fontsize=9, color="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=9)
    ax.xaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("Time Tax Simulator")
    st.markdown(
        "Computes the **Time Tax** $\\Delta\\tau(\\phi)$ for each commuter persona "
        "across the 900m corridor using a power-law friction-velocity model. "
        "The Time Tax is the measurable extra time imposed by non-compliant "
        "infrastructure versus a fully "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure)-compliant "
        "route where $f = 1$ throughout."
    )
    st.markdown("---")

    # Load data
    try:
        df       = load_audit_data()
        personas = load_personas()
    except FileNotFoundError as e:
        st.error(f"Missing data file: {e}")
        return

    # -----------------------------------------------------------------------
    # SIDEBAR CONTROLS
    # -----------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⏱️ Time Tax Simulator Controls")

    persona_labels = {k: v["label"] for k, v in personas.items()}
    selected_key = st.sidebar.selectbox(
        "Commuter persona:",
        options=list(personas.keys()),
        format_func=lambda k: persona_labels[k],
    )
    p = personas[selected_key]

    st.sidebar.markdown("**Scenario settings**")
    n_fixes = st.sidebar.slider(
        "Nodes fixed to S.U.R.E. standard (top-N):",
        min_value=0, max_value=len(df), value=0, step=1,
        help=(
            "Nodes ranked by descending f-value. "
            "Each fix sets that node to f=1 and recalculates the Time Tax."
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
    )
    bazaar_f = sure_standards[bazaar_label]

    # Dynamic sidebar narration
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Persona parameters**")
    st.sidebar.markdown(
        f"- $v_0 = {p['v0']}$ m/s · free-walking speed\n"
        f"- $k = {p['k']}$ · friction sensitivity exponent\n"
        f"- $f_{{\\text{{max}}}} = {p['f_max']}$ · impassability threshold\n"
        f"- $\\alpha = {p['alpha']}$ · ROW velocity penalty\n"
        f"- $\\delta = {p['delta']}$ m · mean detour length"
    )
    if p["f_max"] < 5:
        st.sidebar.caption(
            f"⚠️ For this persona, any node with $f > {p['f_max']}$ is impassable "
            f"and triggers a vehicular ROW detour of ~{p['delta']}m."
        )
    else:
        st.sidebar.caption(
            "✅ This persona can navigate all friction levels — "
            "no ROW detours are triggered."
        )

    # -----------------------------------------------------------------------
    # RUN SIMULATION
    # -----------------------------------------------------------------------
    f_array = build_f_array(df, n_fixes, bazaar_f)
    results = {k: run_simulation(f_array, v) for k, v in personas.items()}
    res     = results[selected_key]

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    st.markdown(f"#### {p['label']} — Traversal Summary")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Ideal time (S.U.R.E.)",
        f"{res['T_ideal'] / 60:.1f} min",
        help=f"D / v₀ = {D:.0f} / {p['v0']} = {res['T_ideal']:.0f}s"
    )
    col2.metric(
        "Actual time",
        f"{res['T_actual'] / 60:.1f} min",
        delta=f"+{res['delta_tau'] / 60:.1f} min",
        delta_color="inverse",
    )
    col3.metric(
        "Time Tax Δτ",
        f"{res['delta_tau']:.0f} s",
        delta=f"+{res['delta_tau'] / res['T_ideal'] * 100:.0f}% over ideal",
        delta_color="inverse",
        help="Extra time imposed by non-compliant infrastructure per single trip."
    )
    col4.metric(
        "ROW detours",
        f"{res['n_detours']} segments",
        help=(
            f"Segments where f > f_max = {p['f_max']}. "
            "Each forces the pedestrian into vehicular Right-of-Way."
        )
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # CHARTS
    # -----------------------------------------------------------------------
    col_left, col_right = st.columns([1, 1.8])

    with col_left:
        st.markdown("#### Ideal vs Actual Traversal")
        fig = plot_traversal_comparison(results, personas, selected_key)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with col_right:
        st.markdown("#### All Personas — Time Tax Comparison")
        fig2 = plot_all_personas(results, personas)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

    st.markdown("---")
    st.markdown("#### Per-Segment Breakdown — Friction & Traversal Time")
    st.caption(
        "Top panel: friction per segment · "
        "Bottom panel: traversal time τᵢ · "
        "Orange ✕ = ROW detour · "
        "Green dotted line = S.U.R.E.-compliant ideal τᵢ"
    )
    fig3 = plot_segment_breakdown(f_array, res, p)
    st.pyplot(fig3, use_container_width=True)
    plt.close(fig3)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PHYSICS DERIVATION EXPANDER
    # -----------------------------------------------------------------------
    with st.expander("📐 Show physics derivation"):
        st.markdown("**Power-law friction-velocity model:**")
        st.latex(
            r"v_{\text{eff}}(i,\,\phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}"
        )
        st.markdown(
            f"For {p['label']}: $v_0 = {p['v0']}$ m/s, $k = {p['k']}$. "
            f"At $f=5$: $v_{{\\text{{eff}}}} = {p['v0']} / 5^{{{p['k']}}} "
            f"= {p['v0'] / 5**p['k']:.3f}$ m/s."
        )
        st.markdown("**Traversal time per segment** ($d = 12.5$ m):")
        st.latex(
            r"\tau_i(\phi) = \frac{d \cdot f_i^{\,k(\phi)}}{v_0(\phi)}"
        )
        st.markdown("**For impassable nodes** ($f_i > f_{\\text{max}}$), ROW detour:")
        st.latex(
            r"\tau_i^{\text{ROW}}(\phi) = \frac{(d + \delta) \cdot \alpha}{v_0(\phi)}"
        )
        st.markdown(
            f"For {p['label']}: $f_{{\\text{{max}}}} = {p['f_max']}$, "
            f"$\\delta = {p['delta']}$ m, $\\alpha = {p['alpha']}$. "
            f"ROW detour time = $({d} + {p['delta']}) \\times {p['alpha']} / {p['v0']} "
            f"= {(d + p['delta']) * p['alpha'] / p['v0']:.1f}$ s."
        )
        st.markdown("**Time Tax per trip:**")
        st.latex(
            r"\Delta\tau(\phi) = T_{\text{actual}} - T_{\text{ideal}} "
            r"= \frac{d}{v_0(\phi)}\left(\sum_{i=1}^{N} f_i^{\,k(\phi)} - N\right)"
        )
        st.markdown(
            f"$T_{{\\text{{actual}}}} = {res['T_actual']:.1f}$ s · "
            f"$T_{{\\text{{ideal}}}} = {res['T_ideal']:.1f}$ s · "
            f"$\\Delta\\tau = {res['delta_tau']:.1f}$ s"
        )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # PER-SEGMENT DATA TABLE
    # -----------------------------------------------------------------------
    with st.expander("📋 Show per-segment data table"):
        seg_df = pd.DataFrame({
            "Segment": range(1, len(f_array) + 1),
            "Zone": ["300m stretch"] * N_300 + ["600m Bazaar St"] * N_600,
            "f": f_array,
            "v_eff (m/s)": np.round(res["v_eff_i"], 3),
            "τᵢ (s)": np.round(res["tau_i"], 2),
            "ROW detour": res["is_detour"],
        })
        st.dataframe(seg_df, hide_index=True, use_container_width=True, height=300)
