import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import os

# -------------------------------------------------------------------------
# CONSTANTS & STYLING
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
# VISUALIZATION BUILDERS (LOGIC UNTOUCHED)
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
    legend_html = f"""
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
      <span style="color:#F44336">━━</span> 600m Bazaar St route (Baseline)
    </div>"""
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

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
    ax.text(150, 5.35, "300m · Discrete Obstacles", ha="center", fontsize=7.5, color="#aaaaaa")
    ax.text(600, 5.35, f"600m · Bazaar Street Failure", ha="center", fontsize=7.5, color="#aaaaaa")
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 5.7)
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig

def plot_severity_donut(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    f_vals = df["f_value"].values.astype(float).copy()
    if n_fixes > 0:
        f_vals[np.argsort(f_vals)[::-1][:n_fixes]] = 1.0
    counts = {f: int((f_vals == f).sum()) for f in [1, 2, 3, 4, 5]}
    present = {f: c for f, c in counts.items() if c > 0}
    sizes, labels = list(present.values()), list(present.keys())
    colors = [F_COLORS[f] for f in labels]
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#1a1a1a")
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.52, edgecolor="#1a1a1a", linewidth=2), counterclock=False)
    ax.text(0, 0, f"{counts.get(5, 0) + counts.get(4, 0)}\nImpassable", ha="center", va="center", fontsize=14, fontweight="bold", color="white")
    ax.axis("off")
    fig.tight_layout()
    return fig

def plot_sure_compliance_bar(f_bar_now: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 1.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    ax.barh(0, 4.0, height=0.45, color="#2a2a2a", left=1.0)
    fill_color = "#4CAF50" if f_bar_now < 1.5 else ("#FF9800" if f_bar_now < 3.0 else "#F44336")
    ax.barh(0, f_bar_now - 1.0, height=0.45, color=fill_color, left=1.0, alpha=0.9)
    for f in [1, 2, 3, 4, 5]:
        ax.axvline(f, color="#555", linewidth=0.8)
    ax.axvline(f_bar_now, color="white", linewidth=2.0)
    ax.set_xlim(0.8, 5.4)
    ax.axis("off")
    return fig

def plot_leff_comparison(L_eff_base: float, L_eff_now: float, n_fixes: int, bazaar_f: int) -> plt.Figure:
    scenarios = [("Surveyed Baseline", L_eff_base), (f"Modified Scenario", L_eff_now), ("S.U.R.E. Target", 900.0)]
    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    for i, (label, leff) in enumerate(scenarios):
        ax.barh(i, 900, height=0.4, color="#4CAF50", alpha=0.8)
        if leff > 900:
            ax.barh(i, leff-900, height=0.4, color="#F44336", left=900, alpha=0.8)
        ax.text(leff+20, i, f"{leff:.0f}m", va='center', color='white', fontsize=9)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels([s[0] for s in scenarios], color='white')
    ax.spines[:].set_visible(False)
    ax.tick_params(axis='x', colors='white')
    fig.tight_layout()
    return fig

# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("📍 Friction Mapper")
    
    # 1. THE MOTIVATION PARAGRAPH
    st.markdown("#### Mapping the Invisible Struggle")
    st.markdown("""
    Walking through Yeshwantpur is not just a distance problem; it is a resistance problem. This map 
    visualizes the 900m corridor as a **Friction Field**, where every obstruction is a measurable force 
    slowing down the city. By geotagging 24 distinct nodes of failure and the 600m Bazaar Street 
    stretch, we translate human frustration into a technical audit. This tool allows you to simulate 
    remediation: by selecting 'hotspots' to fix, you can see how much effective distance is recovered 
    and how close the corridor moves toward the **Tender S.U.R.E.** gold standard.
    """)

    try:
        df = load_audit_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # -----------------------------------------------------------------------
    # SIDEBAR CONTROLS
    # -----------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Infrastructure Intervention")
    
    st.sidebar.markdown("**Step 1: Fix the Hotspots**")
    n_fixes = st.sidebar.slider(
        "Select number of nodes to repair (f=1):",
        min_value=0, max_value=len(df), value=0, step=1,
        help="Targeting the most severe nodes (f=5) first to maximize impact."
    )

    st.sidebar.markdown("**Step 2: Model Bazaar Street**")
    sure_standards = {
        "Current (Systemic Failure)": 5,
        "Partial Remediation": 3,
        "Full S.U.R.E. Standard": 1,
    }
    bazaar_label = st.sidebar.selectbox("Simulate Bazaar Street redesign as:", options=list(sure_standards.keys()))
    bazaar_f = sure_standards[bazaar_label]

    # -----------------------------------------------------------------------
    # MATHEMATICAL FRAMEWORK (PROSE & LATEX)
    # -----------------------------------------------------------------------
    with st.expander("🔬 How the map calculates struggle"):
        st.markdown("""
        The map calculates the difficulty of the walk by treating each infrastructure failure as a 
        resistance point. We define the **Mean Friction Index** as the primary indicator of corridor 
        quality.
        """)
        st.latex(r"\bar{f} = \frac{1}{D} \left( \sum_{i=1}^{N} f_i \cdot d + \int_{Bazaar} f_{B} \, dx \right)")
        
        st.latex(r"\bar{f} : \text{The Mean Friction Index of the full 900m corridor}")
        st.latex(r"D : \text{The total surveyed physical distance (900 meters)}")
        st.latex(r"f_i : \text{The Friction Value assigned to the } i\text{-th discrete node}")
        st.latex(r"d : \text{The standard segment length of 12.5 meters used for discrete nodes}")
        st.latex(r"N : \text{The total number of discrete nodes in the 300m stretch (24)}")
        st.latex(r"f_B : \text{The constant Friction Value modeled for the 600m Bazaar Street stretch}")
        st.latex(r"dx : \text{The integration element along the Bazaar Street route}")

    # -----------------------------------------------------------------------
    # COMPUTE METRICS
    # -----------------------------------------------------------------------
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0:
        f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_now = 12.5 * f_fixed.sum()
    L_eff_600_now = 600 * float(bazaar_f)
    L_eff_now = L_eff_300_now + L_eff_600_now
    f_bar_now = L_eff_now / 900
    n_impassable = int((f_300 > 3).sum())

    st.markdown("---")

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    st.markdown("#### Real-Time Audit Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Compliance Rate", "9.7%", help="Percentage of the corridor meeting S.U.R.E. standards.")
    col2.metric("Impassable Nodes", f"{int((f_fixed > 3).sum())} / 24", delta=f"-{n_impassable - int((f_fixed > 3).sum())}" if n_fixes > 0 else None, delta_color="normal")
    col3.metric("Difficulty Multiplier", f"{f_bar_now:.2f}x", help="Walking here is this many times harder than a standard sidewalk.")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MAP & GRADIENT
    # -----------------------------------------------------------------------
    m = build_map(df, n_fixes, bazaar_f)
    st_folium(m, width=None, height=520, returned_objects=[])

    st.markdown("---")
    st.markdown("#### The Friction Gradient")
    st.caption("Visualizing the intensity of obstacles along the 900m journey.")
    fig_bar = plot_friction_bar(df, n_fixes, bazaar_f)
    st.pyplot(fig_bar, use_container_width=True)
    plt.close(fig_bar)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # INFOGRAPHIC STATS
    # -----------------------------------------------------------------------
    st.markdown("#### Corridor Impact Analysis")
    col_donut, col_right = st.columns([1, 1])

    with col_donut:
        st.caption("Obstacle Severity Breakdown (300m Stretch)")
        fig_donut = plot_severity_donut(df, n_fixes)
        st.pyplot(fig_donut, use_container_width=True)
        plt.close(fig_donut)

    with col_right:
        st.caption("S.U.R.E. Compliance Gauge")
        fig_gauge = plot_sure_compliance_bar(f_bar_now)
        st.pyplot(fig_gauge, use_container_width=True)
        plt.close(fig_gauge)

        st.caption("Effective Path Comparison (Baseline vs Scenario)")
        L_eff_base = (12.5 * f_300.sum()) + (600 * 5)
        fig_leff = plot_leff_comparison(L_eff_base, L_eff_now, n_fixes, bazaar_f)
        st.pyplot(fig_leff, use_container_width=True)
        plt.close(fig_leff)

    # -----------------------------------------------------------------------
    # THE AUDIT MODULES (NUMBERED DESCRIPTION)
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### 🛠️ Mapper Functionality")
    st.write("1. **Live Geotagging:** Every circle marker on the map corresponds to a physical obstacle audited on-site.")
    st.write("2. **Friction Rubric Integration:** The colors correlate to the 5-point rubric, where Red (f=5) represents a total infrastructure failure.")
    st.write("3. **Intervention Modeling:** The sidebar allows planners to 'repair' nodes and see the immediate drop in the Difficulty Multiplier.")
    st.write("4. **Zonal Distinction:** The tool separates 'Staccato' failures (individual holes/poles) from 'Systemic' failures (the missing Bazaar St footpath).")

    st.markdown("---")
    st.caption("Data Source: Yeshwantpur Mobility Audit (March 7-8, 2026) · Bengawalk advocacy project")

if __name__ == "__main__":
    app()
