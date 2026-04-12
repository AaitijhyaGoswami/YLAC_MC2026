import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import os

# -------------------------------------------------------------------------
# CONSTANTS
# -------------------------------------------------------------------------

F_COLORS = {
    1: "#9E9E9E",
    2: "#4CAF50",
    3: "#2196F3",
    4: "#FF9800",
    5: "#F44336",
}

F_LABELS = {
    1: "f=1 · Gold Standard (reference)",
    2: "f=2 · Distracted Walk",
    3: "f=3 · Obstacle Course",
    4: "f=4 · Physical Barrier",
    5: "f=5 · Systemic Failure",
}

F_SHORT = {
    1: "Gold Standard",
    2: "Distracted Walk",
    3: "Obstacle Course",
    4: "Physical Barrier",
    5: "Systemic Failure",
}

ROUTE_600M = [
    [13.02007, 77.55546], [13.0201,  77.55547], [13.02011, 77.55546],
    [13.02053, 77.55475], [13.02063, 77.55458], [13.02102, 77.55398],
    [13.02117, 77.5537],  [13.02121, 77.55367], [13.02124, 77.55365],
    [13.0212,  77.55359], [13.02162, 77.55335], [13.02164, 77.55335],
    [13.02171, 77.55333], [13.022,   77.55316], [13.02196, 77.55307],
    [13.02194, 77.553],   [13.0219,  77.55294], [13.02194, 77.55292],
    [13.02238, 77.55268], [13.02257, 77.55257], [13.02349, 77.55205],
    [13.02383, 77.55187],
]

MAP_CENTRE = [13.0215, 77.5555]

# -------------------------------------------------------------------------
# DATA LOADER
# -------------------------------------------------------------------------

@st.cache_data
def load_audit_data() -> pd.DataFrame:
    path = os.path.join("data", "audit_log.csv")
    df = pd.read_csv(path)
    assert {"id", "lat", "lon", "f_value"}.issubset(df.columns), \
        "audit_log.csv must contain: id, lat, lon, f_value"
    return df


# -------------------------------------------------------------------------
# MAP BUILDER
# -------------------------------------------------------------------------

def build_map(df: pd.DataFrame, n_fixes: int = 0, bazaar_f: int = 5) -> folium.Map:
    m = folium.Map(location=MAP_CENTRE, zoom_start=15, tiles="CartoDB dark_matter")

    folium.PolyLine(
        locations=ROUTE_600M,
        color=F_COLORS.get(bazaar_f, F_COLORS[5]),
        weight=5, opacity=0.85,
        tooltip=f"600m Bazaar Street — {F_LABELS.get(bazaar_f, f'f={bazaar_f}')}",
    ).add_to(m)
    folium.CircleMarker(
        location=ROUTE_600M[0], radius=5, color="white", fill=True,
        fill_color=F_COLORS.get(bazaar_f, F_COLORS[5]), fill_opacity=1.0,
        tooltip="600m stretch — south end",
    ).add_to(m)
    folium.CircleMarker(
        location=ROUTE_600M[-1], radius=5, color="white", fill=True,
        fill_color=F_COLORS.get(bazaar_f, F_COLORS[5]), fill_opacity=1.0,
        tooltip="Yeshwantpur Junction",
    ).add_to(m)

    f_values = df["f_value"].values.astype(float)
    fix_indices = set(df.index[np.argsort(f_values)[::-1][:n_fixes]]) if n_fixes > 0 else set()

    for idx, row in df.iterrows():
        is_fixed = idx in fix_indices
        f = int(row["f_value"])
        color = F_COLORS[1] if is_fixed else F_COLORS.get(f, F_COLORS[5])
        label = "FIXED → f=1" if is_fixed else F_LABELS.get(f, f"f={f}")
        folium.CircleMarker(
            location=(row["lat"], row["lon"]), radius=8,
            color="white", weight=0.8, fill=True,
            fill_color=color, fill_opacity=0.9,
            tooltip=f"Node {int(row['id'])} · {label}",
        ).add_to(m)

    legend_html = """
    <div style="position:fixed;bottom:20px;left:20px;z-index:9999;
         background:#1a1a1a;padding:10px 14px;border-radius:8px;
         border:1px solid #444;font-size:12px;color:white;font-family:monospace">
      <b>Friction Level</b><br>
      <span style="color:#9E9E9E">●</span> f=1 · Gold Standard / Fixed<br>
      <span style="color:#4CAF50">●</span> f=2 · Distracted Walk<br>
      <span style="color:#2196F3">●</span> f=3 · Obstacle Course<br>
      <span style="color:#FF9800">●</span> f=4 · Physical Barrier<br>
      <span style="color:#F44336">●</span> f=5 · Systemic Failure<br>
      <hr style="border-color:#444;margin:5px 0">
      <span style="color:#F44336">━━</span> 600m Bazaar St route (f=5)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


# -------------------------------------------------------------------------
# FRICTION GRADIENT BAR
# -------------------------------------------------------------------------

def plot_friction_bar(df: pd.DataFrame, n_fixes: int = 0, bazaar_f: int = 5) -> plt.Figure:
    f_300 = df["f_value"].values.astype(float)
    if n_fixes > 0:
        f_display = f_300.copy()
        f_display[np.argsort(f_display)[::-1][:n_fixes]] = 1.0
    else:
        f_display = f_300.copy()

    f_600 = np.full(48, float(bazaar_f))
    f_all = np.concatenate([f_display, f_600])
    d = 12.5
    x = np.arange(len(f_all)) * d
    colors = [F_COLORS.get(int(min(v, 5)), F_COLORS[5]) for v in f_all]

    fig, ax = plt.subplots(figsize=(11, 2.5))
    ax.bar(x, f_all, width=d * 0.88, color=colors, align="edge", linewidth=0)
    ax.axvline(300, color="#aaaaaa", linewidth=1.2, linestyle="--", alpha=0.6)
    ax.text(150, 5.35, "300m · discrete nodes", ha="center", fontsize=7.5, color="#aaaaaa")
    ax.text(600, 5.35, f"600m · Bazaar Street (f={bazaar_f})", ha="center", fontsize=7.5, color="#aaaaaa")
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 5.7)
    ax.set_xlabel("Distance along route (m)", fontsize=9, color="white")
    ax.set_ylabel("f", fontsize=9, color="white")
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    patches = [mpatches.Patch(color=F_COLORS[f], label=F_LABELS[f]) for f in sorted(F_COLORS)]
    ax.legend(handles=patches, loc="upper left", fontsize=7,
              facecolor="#2a2a2a", labelcolor="white", framealpha=0.85, ncol=5)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# PIE CHART
# -------------------------------------------------------------------------

def plot_severity_pie(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    """
    Standard pie chart of friction distribution for the 300m stretch.
    """
    f_vals = df["f_value"].values.astype(float).copy()
    if n_fixes > 0:
        f_vals[np.argsort(f_vals)[::-1][:n_fixes]] = 1.0

    counts = {f: int((f_vals == f).sum()) for f in [1, 2, 3, 4, 5]}
    present = {f: c for f, c in counts.items() if c > 0}
    
    sizes = list(present.values())
    labels = [F_SHORT[f] for f in present.keys()]
    colors = [F_COLORS[f] for f in present.keys()]

    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct='%1.0f%%',
        startangle=90,
        textprops={'color':"white", 'fontsize': 8},
        counterclock=False,
    )

    ax.set_title("Obstacle Severity Breakdown (300m)", color="white", fontsize=10)
    fig.tight_layout()
    return fig


def plot_leff_comparison(L_eff_base: float, L_eff_now: float,
                         f_bar_base: float, f_bar_now: float,
                         n_fixes: int, bazaar_f: int) -> plt.Figure:
    """
    Horizontal bar comparing baseline vs modified vs target.
    """
    scenarios = [
        ("Surveyed Baseline", L_eff_base, f_bar_base),
        ("Modified Scenario", L_eff_now,  f_bar_now),
        ("S.U.R.E. Target", 900.0,       1.0),
    ]

    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    bar_h = 0.4
    for i, (label, leff, fbar) in enumerate(scenarios):
        ax.barh(i, 900, height=bar_h, color="#4CAF50", alpha=0.8)
        excess = leff - 900
        if excess > 0:
            ax.barh(i, excess, height=bar_h, color="#F44336", left=900, alpha=0.8)
        
        ax.text(leff + 20, i, f"{leff:.0f}m (f̄={fbar:.2f})", va="center", color="white", fontsize=8.5)

    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels([s[0] for s in scenarios], fontsize=8.5, color="white")
    ax.set_xlim(0, max(L_eff_base, L_eff_now) * 1.2)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    ax.set_title("Effective Path Length Comparison", color="white", fontsize=10)
    fig.tight_layout()
    return fig


def plot_sure_compliance_bar(f_bar_now: float) -> plt.Figure:
    """
    Detailed horizontal progress bar with f-level labels and current marker.
    """
    fig, ax = plt.subplots(figsize=(7, 1.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    # Background track
    ax.barh(0, 4.0, height=0.45, color="#2a2a2a", linewidth=0, left=1.0)
    
    # Current f̄ fill
    fill_color = (
        "#4CAF50" if f_bar_now < 1.5 else
        "#FF9800" if f_bar_now < 3.0 else
        "#F44336"
    )
    ax.barh(0, f_bar_now - 1.0, height=0.45, color=fill_color,
            linewidth=0, left=1.0, alpha=0.9)

    # Tick marks at each f level
    for f in [1, 2, 3, 4, 5]:
        ax.axvline(f, color="#555", linewidth=0.8, ymin=0.1, ymax=0.9)
        ax.text(f, -0.38, str(f), ha="center", fontsize=7.5, color="#aaaaaa")

    # Current f̄ marker
    ax.axvline(f_bar_now, color="white", linewidth=2.0)
    ax.text(f_bar_now, 0.32, f" f̄ = {f_bar_now:.3f}",
            va="bottom", ha="left" if f_bar_now < 4 else "right",
            fontsize=9, color="white", fontweight="bold")

    # Target label
    ax.text(1.0, 0.32, "S.U.R.E. →", va="bottom", ha="left",
            fontsize=7, color="#4CAF50")

    ax.set_xlim(0.8, 5.4)
    ax.set_ylim(-0.5, 0.6)
    ax.axis("off")
    fig.tight_layout(pad=0.3)
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("Friction Mapper")
    
    st.markdown("""
    This module maps the physical resistance encountered by pedestrians along the 900m Yeshwantpur corridor. 
    By quantifying geotagged obstacles as friction values, we measure the corridor quality and model how 
    infrastructure repairs directly reduce the effort required for urban navigation.
    """)
    
    st.markdown("---")

    # --- MOTIVATION ---
    st.header("The Mechanics of Resistance")
    st.markdown("""
    In this audit, the sidewalk is modeled as a system of physical resistance. Every broken drain, encroachment, 
    or missing footpath segment acts as a friction point that increases the energy required to traverse the path. 
    By calculating the Mean Friction Index, we translate these physical barriers into an objective metric of street 
    quality. This allows us to move beyond subjective complaints and provide a data-driven blueprint for 
    targeted municipal intervention.
    """)

    # --- TECHNICAL MATH SECTION ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("""
        Corridor quality is defined by the **Mean Friction Index**, representing the average struggle factor 
        across the total surveyed distance. We calculate this by aggregating the friction of discrete obstacles 
        and continuous failure zones.
        """)
        st.latex(r"\bar{f} = \frac{1}{D} \left[ \left( d \sum_{i=1}^{N} f_i \right) + \int_{0}^{L_{B}} f_{B}(x) \, dx \right]")
        st.latex(r"""
            \begin{aligned}
            \bar{f} &: \text{Mean Friction Index of the full 900m corridor (Target = 1.0)} \\
            D &: \text{Total physical distance of the surveyed route (900 meters)} \\
            d &: \text{Fixed length of each audited segment block (12.5 meters)} \\
            i &: \text{Summation index for segments within the 300m discrete node zone} \\
            N &: \text{Total number of discrete segments surveyed (24 nodes)} \\
            f_i &: \text{The recorded friction value for the } i\text{-th segment} \\
            L_{B} &: \text{Length of the Bazaar Street continuous failure zone (600 meters)} \\
            f_{B} &: \text{The modelled friction value for the Bazaar Street stretch} \\
            dx &: \text{Infinitesimal position element for integration across the continuous zone}
            \end{aligned}
        """)

    try:
        df = load_audit_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Friction Mapper Controls")
    st.sidebar.markdown("**300m stretch — hotspot fixes**")

    n_fixes = st.sidebar.slider(
        "Nodes brought to Tender S.U.R.E. standard (f=1):",
        min_value=0, max_value=len(df), value=0, step=1,
        help=(
            "Nodes are ranked by f-value descending — highest friction first. "
            "Setting n=1 fixes the single worst obstacle. "
            "n=3 is the Lighthouse Pilot ask. "
            "n=24 models a fully remediated 300m stretch."
        )
    )

    if n_fixes == 0:
        st.sidebar.caption("📍 Showing surveyed conditions — no fixes applied.")
    elif n_fixes <= 3:
        st.sidebar.caption(f"🔧 Lighthouse Pilot scenario — {n_fixes} fixed.")
    elif n_fixes <= 9:
        st.sidebar.caption(f"🔧 {n_fixes} nodes fixed — all f=5 obstacles remediated.")
    elif n_fixes <= 17:
        st.sidebar.caption(f"🔧 {n_fixes} nodes fixed — wheelchair-navigable baseline.")
    else:
        st.sidebar.caption(f"🔧 {n_fixes} nodes fixed — full S.U.R.E. compliance approach.")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**600m Bazaar Street stretch**")
    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Full S.U.R.E. compliance — f=1": 1,
    }
    bazaar_label = st.sidebar.selectbox("Model Bazaar Street as:", list(sure_standards.keys()))
    bazaar_f = sure_standards[bazaar_label]

    # --- COMPUTATION ---
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0:
        f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_base = 12.5 * f_300.sum()
    L_eff_300_now  = 12.5 * f_fixed.sum()
    L_eff_base     = L_eff_300_base + (600 * 5)
    L_eff_now      = L_eff_300_now  + (600 * bazaar_f)
    f_bar_base     = L_eff_base / 900
    f_bar_now      = L_eff_now  / 900

    # --- HEADLINE METRICS ---
    st.markdown("#### The State of the Corridor")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Compliance Rate", "9.7%")
    col2.metric("Wheelchair Inaccessible", "96.0%")
    col3.metric("Impassable Nodes", f"{int((f_fixed > 3).sum())} / 24")
    col4.metric("Difficulty Multiplier", f"{f_bar_now:.2f}x")

    st.markdown("---")

    # --- MAP ---
    m = build_map(df, n_fixes, bazaar_f)
    st_folium(m, width=None, height=520, returned_objects=[])

    st.markdown("---")

    # --- GRADIENT BAR ---
    st.markdown("#### Friction Gradient — Full 900m Route")
    fig_bar = plot_friction_bar(df, n_fixes, bazaar_f)
    st.pyplot(fig_bar, use_container_width=True)
    plt.close(fig_bar)

    st.markdown("---")

    # --- CORRIDOR ANALYSIS ---
    st.markdown("#### Corridor Analysis")
    col_left, col_right = st.columns(2)

    with col_left:
        fig_pie = plot_severity_pie(df, n_fixes)
        st.pyplot(fig_pie, use_container_width=True)
        plt.close(fig_pie)

    with col_right:
        st.caption("S.U.R.E. Compliance Gauge")
        st.pyplot(plot_sure_compliance_bar(f_bar_now), use_container_width=True)
        st.pyplot(plot_leff_comparison(L_eff_base, L_eff_now, f_bar_base, f_bar_now, n_fixes, bazaar_f), use_container_width=True)

    # --- POINTWISE DESCRIPTION ---
    st.markdown("---")
    st.header("Mapper Functionality")
    st.write("1. **Live Geotagging:** Every marker on the map corresponds to a physical obstacle audited on-site.")
    st.write("2. **Rubric Alignment:** Colors follow the Active Mobility Bill standards, where Red represents a total failure.")
    st.write("3. **Intervention Simulation:** The slider allows planners to 'repair' hotspots and see the real-time drop in total friction.")
    st.write("4. **Policy Data:** Provides the technical baseline required for government project approval.")

    st.markdown("---")
    st.markdown("#### Friction Rubric")
    rubric = pd.DataFrame({
        "f": [1, 2, 3, 4, 5],
        "Label": ["Gold Standard", "Distracted Walk", "Obstacle Course", "Physical Barrier", "Systemic Failure"],
        "Infrastructure State": [
            "Continuous, unobstructed 3m+ footpath",
            "Minor cracks, unlevelled slabs",
            "Broken slabs, rubble, utility excavation",
            "Missing drain cover, partial blockage",
            "Footpath ends entirely",
        ],
        "Wheelchair Access": ["Full", "Partial", "Restricted", "Impassable", "Fully Impassable"],
    })
    st.dataframe(rubric, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    app()
