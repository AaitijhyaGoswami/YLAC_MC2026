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
# CONSTANTS (Logic Intact)
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
# CHART BUILDERS (Logic Intact)
# -------------------------------------------------------------------------

def build_map(df: pd.DataFrame, n_fixes: int = 0, bazaar_f: int = 5) -> folium.Map:
    m = folium.Map(location=MAP_CENTRE, zoom_start=15, tiles="CartoDB dark_matter")
    folium.PolyLine(locations=ROUTE_600M, color=F_COLORS.get(bazaar_f, F_COLORS[5]), weight=5, opacity=0.85).add_to(m)
    f_values = df["f_value"].values.astype(float)
    fix_indices = set(df.index[np.argsort(f_values)[::-1][:n_fixes]]) if n_fixes > 0 else set()
    for idx, row in df.iterrows():
        is_fixed = idx in fix_indices
        f = int(row["f_value"])
        color = F_COLORS[1] if is_fixed else F_COLORS.get(f, F_COLORS[5])
        folium.CircleMarker(location=(row["lat"], row["lon"]), radius=8, color="white", weight=0.8, fill=True, fill_color=color, fill_opacity=0.9).add_to(m)
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
    ax.bar(x, f_all, width=d * 0.88, color=colors, align="edge")
    ax.set_xlim(0, 900)
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    fig.tight_layout()
    return fig

def plot_severity_donut(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    f_vals = df["f_value"].values.astype(float).copy()
    if n_fixes > 0:
        f_vals[np.argsort(f_vals)[::-1][:n_fixes]] = 1.0
    counts = {f: int((f_vals == f).sum()) for f in [1, 2, 3, 4, 5]}
    sizes = [c for c in counts.values() if c > 0]
    colors = [F_COLORS[f] for f, c in counts.items() if c > 0]
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#1a1a1a")
    ax.pie(sizes, colors=colors, startangle=90, wedgeprops=dict(width=0.5, edgecolor="#1a1a1a"))
    ax.axis("off")
    return fig

def plot_leff_comparison(L_eff_base: float, L_eff_now: float, f_bar_base: float, f_bar_now: float, n_fixes: int, bazaar_f: int) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.barh(0, L_eff_base, color="#F44336")
    ax.barh(1, L_eff_now, color="#FF9800")
    ax.barh(2, 900, color="#4CAF50")
    ax.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    fig.tight_layout()
    return fig

def plot_sure_compliance_bar(f_bar_now: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(7, 1.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    ax.barh(0, 4, left=1, color="#2a2a2a")
    ax.axvline(f_bar_now, color="white")
    ax.set_xlim(0.8, 5.4)
    ax.axis("off")
    return fig

# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("📍 Friction Mapper")
    st.markdown("### Mapping the Invisible Struggle of Yeshwantpur")
    
    st.markdown("""
    This module visualizes the pedestrian environment as a spatially varying friction field. By geotagging 
    individual obstacles and modeling systemic failures, we create a technical baseline for last-mile 
    accessibility.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("📊 The Scale")
        st.write("- **Area:** 900m Transit Corridor")
        st.write("- **Audit:** 24 Discrete Nodes")
        st.write("- **Zone:** Bazaar St + Constitution Circle")

    with col2:
        st.subheader("📉 The Impact")
        st.write("- **Baseline f̄:** 4.65 (High Friction)")
        st.write("- **Access:** 96% Wheelchair Failure")
        st.error("- **Distance:** 900m feels like 4.2km")

    with col3:
        st.subheader("💡 The Solution")
        st.write("- **Pilot:** Fix Top 3 Hotspots")
        st.write("- **Target:** f=1 (S.U.R.E. Standard)")
        st.success("- **Impact:** 38% Friction Recovery")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 The Mechanics of Resistance")
    st.markdown("""
    Why do we treat a sidewalk like a physics experiment? Because a "bad road" is more than a visual 
    nuisance—it is a physical barrier that demands mechanical work from the human body. In this audit, 
    every geotagged point represents a 'potential energy barrier' that a commuter must navigate. By 
    mapping these points as friction values, we move beyond subjective complaints and provide the city 
    with a measurable, objective map of where time and energy are being lost.
    """)

    # --- TECHNICAL MATH SECTION (Prose + Latex) ---
    with st.expander("🔬 View Technical Methodology and Variables"):
        st.markdown("""
        The quality of the corridor is indexed by the **Mean Friction Index**, which represents the 
        average struggle factor across the total surveyed distance. It is calculated by aggregating 
        the discrete obstacles and the continuous failure zones.
        """)
        st.latex(r"\bar{f} = \frac{1}{D} \left[ \left( d \sum_{i=1}^{N} f_i \right) + \int_{0}^{L_{B}} f_{B}(x) \, dx \right]")
        st.latex(r"""
            \begin{aligned}
            \bar{f} &: \text{Mean Friction Index of the full 900m corridor (1 = Gold Standard)} \\
            D &: \text{The total physical corridor distance surveyed (900 meters)} \\
            d &: \text{The length of each audited segment block (12.5 meters)} \\
            i &: \text{The index of each discrete segment audited within the 300m stretch} \\
            N &: \text{The total number of discrete segments (24 blocks)} \\
            f_i &: \text{The specific Friction Value recorded at the } i\text{-th segment} \\
            L_{B} &: \text{The length of the Bazaar Street continuous failure zone (600 meters)} \\
            f_{B} &: \text{The modelled Friction Value for the Bazaar Street stretch} \\
            dx &: \text{The infinitesimal position element along the Bazaar Street route}
            \end{aligned}
        """)

    try:
        df = load_audit_data()
    except Exception as e:
        st.error(f"Error: {e}")
        return

    # -----------------------------------------------------------------------
    # SIDEBAR CONTROLS (Mapping Code Logic Restored)
    # -----------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Friction Mapper Controls")
    n_fixes = st.sidebar.slider("Nodes brought to S.U.R.E. standard (f=1):", 0, len(df), 0)
    
    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Full S.U.R.E. compliance — f=1": 1,
    }
    bazaar_label = st.sidebar.selectbox("Model Bazaar Street as:", list(sure_standards.keys()))
    bazaar_f = sure_standards[bazaar_label]

    # -----------------------------------------------------------------------
    # COMPUTE METRICS
    # -----------------------------------------------------------------------
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0:
        f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_base = 12.5 * f_300.sum()
    L_eff_300_now = 12.5 * f_fixed.sum()
    L_eff_base = L_eff_300_base + 3000
    L_eff_now = L_eff_300_now + (600 * bazaar_f)
    f_bar_base = L_eff_base / 900
    f_bar_now = L_eff_now / 900

    st.markdown("---")

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Current f̄", f"{f_bar_now:.2f}", delta=f"{f_bar_now - f_bar_base:.2f}" if f_bar_now != f_bar_base else None, delta_color="normal")
    m_col2.metric("Impassable (f≥4)", f"{int((f_fixed > 3).sum())} / 24")
    m_col3.metric("Effective Length", f"{L_eff_now:.0f}m")

    # -----------------------------------------------------------------------
    # MAP & VISUALS (Logic Same to Same)
    # -----------------------------------------------------------------------
    st_folium(build_map(df, n_fixes, bazaar_f), width=None, height=500)
    
    st.markdown("#### Friction Gradient — Full 900m Route")
    st.pyplot(plot_friction_bar(df, n_fixes, bazaar_f), use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.caption("Obstacle Severity (300m)")
        st.pyplot(plot_severity_donut(df, n_fixes), use_container_width=True)
    with c2:
        st.caption("S.U.R.E. Target Gauge")
        st.pyplot(plot_sure_compliance_bar(f_bar_now), use_container_width=True)
        st.pyplot(plot_leff_comparison(L_eff_base, L_eff_now, f_bar_base, f_bar_now, n_fixes, bazaar_f), use_container_width=True)

    # -----------------------------------------------------------------------
    # POINTWISE DESCRIPTIONS
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.header("🛠️ Mapper Functionality")
    st.write("1. **Live Geotagging:** Every circle marker on the map corresponds to a physical obstacle audited on-site.")
    st.write("2. **Rubric Alignment:** Colors strictly follow the Active Mobility Bill rubric, where Red (f=5) denotes a total failure of infrastructure.")
    # 
    st.write("3. **Intervention Simulation:** The slider allows planners to 'repair' hotspots and see the real-time drop in total corridor friction.")
    st.write("4. **Evidence Generation:** This module provides the geotagged baseline used in policy briefs for the BBMP and DULT.")

    st.caption("Developed for Bengawalk · YLAC Mobility Champions 2026")

if __name__ == "__main__":
    app()
