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

# Colour scheme:
# f=1 — reference point (grey, rarely plotted)
# f=2 — green
# f=3 — blue
# f=4 — orange
# f=5 — red
F_COLORS = {
    1: "#9E9E9E",  # grey  — reference / Tender S.U.R.E. standard
    2: "#4CAF50",  # green
    3: "#2196F3",  # blue
    4: "#FF9800",  # orange
    5: "#F44336",  # red
}

F_LABELS = {
    1: "f=1 · Gold Standard (reference)",
    2: "f=2 · Distracted Walk",
    3: "f=3 · Obstacle Course",
    4: "f=4 · Physical Barrier",
    5: "f=5 · Systemic Failure",
}

# 600m Bazaar Street route — [lat, lon] ordered from south end to Yeshwantpur Jn
# Source: route_nodes1.geojson exported from Google My Maps
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

# Map centre — midpoint of full survey area
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
    """
    Folium map with:
    - 24 circle markers for the 300m stretch obstacle nodes
    - Polyline for the 600m Bazaar Street stretch (red, f=5)
    - Fixed nodes shown in grey (f=1 reference colour)
    """
    m = folium.Map(
        location=MAP_CENTRE,
        zoom_start=15,
        tiles="CartoDB dark_matter",
    )

    # --- 600m Bazaar Street stretch — polyline ---
    folium.PolyLine(
        locations=ROUTE_600M,
        color=F_COLORS.get(bazaar_f, F_COLORS[5]),
        weight=5,
        opacity=0.85,
        tooltip=f"600m Bazaar Street — {F_LABELS.get(bazaar_f, f'f={bazaar_f}')}",
    ).add_to(m)

    # Start/end markers for the 600m stretch
    folium.CircleMarker(
        location=ROUTE_600M[0],
        radius=5,
        color="white",
        fill=True,
        fill_color=F_COLORS.get(bazaar_f, F_COLORS[5]),
        fill_opacity=1.0,
        tooltip="600m stretch — south end",
    ).add_to(m)
    folium.CircleMarker(
        location=ROUTE_600M[-1],
        radius=5,
        color="white",
        fill=True,
        fill_color=F_COLORS.get(bazaar_f, F_COLORS[5]),
        fill_opacity=1.0,
        tooltip="Yeshwantpur Junction",
    ).add_to(m)

    # --- 300m stretch — obstacle pins ---
    f_values = df["f_value"].values.astype(float)
    fix_indices = set(
        df.index[np.argsort(f_values)[::-1][:n_fixes]]
    ) if n_fixes > 0 else set()

    for idx, row in df.iterrows():
        is_fixed = idx in fix_indices
        f = int(row["f_value"])
        color = F_COLORS[1] if is_fixed else F_COLORS.get(f, F_COLORS[5])
        label = "FIXED → f=1" if is_fixed else F_LABELS.get(f, f"f={f}")

        folium.CircleMarker(
            location=(row["lat"], row["lon"]),
            radius=8,
            color="white",
            weight=0.8,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"Node {int(row['id'])} · {label}",
        ).add_to(m)

    # --- Legend ---
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
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# -------------------------------------------------------------------------
# FRICTION GRADIENT BAR CHART
# -------------------------------------------------------------------------

def plot_friction_bar(df: pd.DataFrame, n_fixes: int = 0, bazaar_f: int = 5) -> plt.Figure:
    """
    Colour-coded bar chart across the full 900m.
    Left 24 bars = 300m discrete nodes. Right 48 bars = 600m Bazaar St.
    """
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
    ax.text(150, 5.35, "300m · discrete nodes",
            ha="center", fontsize=7.5, color="#aaaaaa")
    ax.text(600, 5.35, f"600m · Bazaar Street (f={bazaar_f})",
            ha="center", fontsize=7.5, color="#aaaaaa")

    ax.set_xlim(0, 900)
    ax.set_ylim(0, 5.7)
    ax.set_xlabel("Distance along route (m)", fontsize=9, color="white")
    ax.set_ylabel("f", fontsize=9, color="white")
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)

    patches = [
        mpatches.Patch(color=F_COLORS[f], label=F_LABELS[f])
        for f in sorted(F_COLORS)
    ]
    ax.legend(handles=patches, loc="upper left", fontsize=7,
              facecolor="#2a2a2a", labelcolor="white",
              framealpha=0.85, ncol=5)

    fig.tight_layout()
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.title("Friction Mapper")
    st.markdown(
        "Interactive map of the 900m Yeshwantpur–Constitution Circle corridor. "
        "Circle markers show the 24 geotagged obstacle nodes from the March 2026 "
        "field audit. The red polyline traces the 600m Bazaar Street stretch — "
        "a continuous $f = 5$ failure. "
        "Use the controls below to simulate "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
        "remediation scenarios."
    )
    

    # Load data
    try:
        df = load_audit_data()
    except FileNotFoundError:
        st.error("data/audit_log.csv not found. Please add the file and restart.")
        return
    except AssertionError as e:
        st.error(f"audit_log.csv schema error: {e}")
        return

    # -----------------------------------------------------------------------
    # SIDEBAR CONTROLS
    # -----------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🗺️ Friction Mapper Controls")

    st.sidebar.markdown("**300m stretch — hotspot fixes**")
    n_fixes = st.sidebar.slider(
        "Nodes brought to Tender S.U.R.E. standard (f=1):",
        min_value=0, max_value=len(df), value=0, step=1,
        help=(
            "Nodes are ranked by f-value descending — highest friction first. "
            "Setting n=1 fixes the single worst obstacle. n=3 is the Lighthouse Pilot ask. "
            "n=24 models a fully remediated 300m stretch."
        )
    )

    # Dynamic annotation below the slider
    if n_fixes == 0:
        st.sidebar.caption("📍 Showing surveyed conditions — no fixes applied.")
    elif n_fixes <= 3:
        st.sidebar.caption(
            f"🔧 **Lighthouse Pilot scenario** — {n_fixes} node(s) fixed. "
            "This is the minimum viable intervention argued in the DULT brief."
        )
    elif n_fixes <= 9:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — all f=5 obstacles on the 300m stretch "
            "would be remediated at this level."
        )
    elif n_fixes <= 17:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — all f=4 and f=5 obstacles cleared. "
            "The stretch would be wheelchair-navigable for the first time."
        )
    else:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — full 300m stretch approaching "
            "Tender S.U.R.E. compliance."
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**600m Bazaar Street stretch**")
    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Partial repair — f=4 (Physical Barrier)": 4,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Near compliant — f=2 (Distracted Walk)": 2,
        "Full S.U.R.E. compliance — f=1 (Gold Standard)": 1,
    }
    bazaar_label = st.sidebar.selectbox(
        "Model Bazaar Street as:",
        options=list(sure_standards.keys()),
        index=0,
        help=(
            "Toggle what Tender S.U.R.E. compliance looks like for the 600m stretch. "
            "f=1 models full pipe-and-chamber drain replacement and continuous 3m footpath. "
            "f=2 models a partial improvement — surface levelled but utilities still overhead."
        )
    )
    bazaar_f = sure_standards[bazaar_label]

    if bazaar_f < 5:
        st.sidebar.caption(
            f"The 600m stretch is modelled at $f={bazaar_f}$. "
            "This scenario is speculative — it represents what the corridor "
            "could achieve under "
            "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) intervention."
        )

    # -----------------------------------------------------------------------
    # COMPUTE LIVE FRICTION METRICS
    # -----------------------------------------------------------------------
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0:
        f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_base = 12.5 * f_300.sum()           # baseline (no fixes)
    L_eff_300_now  = 12.5 * f_fixed.sum()          # after fixes
    L_eff_600_base = 600 * 5.0
    L_eff_600_now  = 600 * float(bazaar_f)
    L_eff_base     = L_eff_300_base + L_eff_600_base
    L_eff_now      = L_eff_300_now  + L_eff_600_now
    f_bar_base     = L_eff_base / 900
    f_bar_now      = L_eff_now  / 900

    pct_fail       = 90.3                          # from survey
    pct_wheelchair = 96.0
    n_impassable   = int((f_300 > 3).sum())        # f=4 or f=5 nodes
    n_impassable_now = int((f_fixed > 3).sum()) + (48 if bazaar_f > 3 else 0)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # GRAVITY METRICS — lead with the damage, not the numbers
    # -----------------------------------------------------------------------
    st.markdown("#### The State of the Corridor")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Fails Active Mobility Bill",
        f"{pct_fail}%",
        help="90.3% of the 900m stretch does not meet minimum pedestrian standards."
    )
    col2.metric(
        "Wheelchair inaccessible",
        f"{pct_wheelchair}%",
        help="96% of the route has f > f_max for wheelchair users (f_max = 3)."
    )
    col3.metric(
        "Impassable nodes (f ≥ 4)",
        f"{n_impassable} / 24",
        delta=f"−{n_impassable - int((f_fixed > 3).sum())} after fixes" if n_fixes > 0 else None,
        delta_color="normal",
        help="Nodes rated f=4 or f=5 force pedestrians into vehicular Right-of-Way."
    )
    col4.metric(
        "Effective path multiplier",
        f"{f_bar_now:.2f}×",
        delta=f"{f_bar_now - f_bar_base:.3f}" if (n_fixes > 0 or bazaar_f < 5) else None,
        delta_color="normal",
        help=(
            "The corridor makes a 900m walk feel like "
            f"{f_bar_now:.2f}× that distance on a compliant footpath. "
            "A fully S.U.R.E.-compliant route would be 1.00×."
        )
    )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MAP
    # -----------------------------------------------------------------------
    m = build_map(df, n_fixes, bazaar_f)
    st_folium(m, width=None, height=520, returned_objects=[])

    st.markdown("---")

    # -----------------------------------------------------------------------
    # FRICTION GRADIENT BAR
    # -----------------------------------------------------------------------
    st.markdown("#### Friction Gradient — Full 900m Route")
    st.caption(
        "Each bar = one 12.5m segment · "
        "Left 24 = 300m discrete nodes · "
        "Right 48 = 600m Bazaar Street · "
        "Grey = brought to f=1"
    )
    fig = plot_friction_bar(df, n_fixes, bazaar_f)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # STATISTICS — framed around severity
    # -----------------------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Obstacle Severity — 300m Stretch")
        st.caption(
            "79% of obstacles rated f=5 — footpath ends entirely, "
            "pedestrians forced into vehicular traffic."
        )
                dist = (
            df["f_value"]
            .value_counts()
            .sort_index(ascending=False)
            .reset_index()
            .rename(columns={"f_value": "f", "count": "Count"})
        )
        dist["Level"] = dist["f"].map(
            {v: l.split(" · ")[1] for v, l in F_LABELS.items()}
        )
        dist["Share of route"] = (dist["Count"] / len(df) * 100).round(1).astype(str) + "%"
        dist["S.U.R.E. compliant?"] = dist["f"].map(
            {1: "✅ Yes", 2: "⚠️ Marginal", 3: "❌ No", 4: "❌ No", 5: "❌ No"}
        )
        st.dataframe(
            dist[["f", "Level", "Count", "Share of route", "S.U.R.E. compliant?"]],
            hide_index=True,
            use_container_width=True,
        )


    with col2:
        st.markdown("#### Effective Path Length — Before vs After")
        st.caption(
            "S.U.R.E. target = $L_{\\text{eff}} = 900$ m · $\\bar{f} = 1.0$. "
            "Every unit above 1.0 represents wasted physical effort."
        )
        comparison = pd.DataFrame({
            "Scenario": [
                "Surveyed (baseline)",
                f"After {n_fixes} node fix(es) + Bazaar St at f={bazaar_f}",
                "Full S.U.R.E. compliance (target)",
            ],
            "$L_{eff}$ (m)": [
                f"{L_eff_base:.1f}",
                f"{L_eff_now:.1f}",
                "900.0",
            ],
            "$\\bar{f}$": [
                f"{f_bar_base:.3f}",
                f"{f_bar_now:.3f}",
                "1.000",
            ],
            "vs. S.U.R.E. target": [
                f"+{L_eff_base - 900:.1f} m excess",
                f"+{L_eff_now - 900:.1f} m excess",
                "✅ 0 m excess",
            ],
        })
        st.dataframe(comparison, hide_index=True, use_container_width=True)

        pct_recovered = (L_eff_base - L_eff_now) / (L_eff_base - 900) * 100 \
            if (n_fixes > 0 or bazaar_f < 5) else 0
        if pct_recovered > 0:
            st.success(
                f"This scenario recovers **{pct_recovered:.1f}%** of the excess "
                f"effective path length above the S.U.R.E. target."
            )

    st.markdown("---")

    # -----------------------------------------------------------------------
    # FRICTION RUBRIC
    # -----------------------------------------------------------------------
    st.markdown("#### Friction Rubric")
    rubric = pd.DataFrame({
        "f": [1, 2, 3, 4, 5],
        "Label": ["Gold Standard", "Distracted Walk", "Obstacle Course",
                  "Physical Barrier", "Systemic Failure"],
        "Infrastructure State": [
            "Continuous, unobstructed 3m+ footpath (Tender S.U.R.E. standard)",
            "Minor cracks, unlevelled slabs, low-hanging cables",
            "Broken slabs, rubble, utility excavation",
            "Missing drain cover, high kerb, partial blockage",
            "Footpath ends — transformer, encroachment, construction",
        ],
        "Wheelchair Access": [
            "Full",
            "Partial — discomfort",
            "Severely restricted",
            "Effectively impassable",
            "Fully impassable",
        ],
        "S.U.R.E. compliant?": [
            "✅ Yes — reference standard",
            "⚠️ Marginal",
            "❌ No",
            "❌ No",
            "❌ No",
        ],
    })
    st.dataframe(rubric, hide_index=True, use_container_width=True)
