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

def build_map(df: pd.DataFrame, n_fixes: int = 0) -> folium.Map:
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
        color=F_COLORS[5],
        weight=5,
        opacity=0.85,
        tooltip="600m Bazaar Street — continuous f=5 · Systemic Failure",
    ).add_to(m)

    # Start/end markers for the 600m stretch
    folium.CircleMarker(
        location=ROUTE_600M[0],
        radius=5,
        color="white",
        fill=True,
        fill_color=F_COLORS[5],
        fill_opacity=1.0,
        tooltip="600m stretch — south end",
    ).add_to(m)
    folium.CircleMarker(
        location=ROUTE_600M[-1],
        radius=5,
        color="white",
        fill=True,
        fill_color=F_COLORS[5],
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

def plot_friction_bar(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    """
    Colour-coded bar chart across the full 900m.
    Left 24 bars = 300m discrete nodes. Right 48 bars = 600m Bazaar St (f=5).
    """
    f_300 = df["f_value"].values.astype(float)

    if n_fixes > 0:
        f_display = f_300.copy()
        f_display[np.argsort(f_display)[::-1][:n_fixes]] = 1.0
    else:
        f_display = f_300.copy()

    f_600 = np.full(48, 5.0)
    f_all = np.concatenate([f_display, f_600])

    d = 12.5
    x = np.arange(len(f_all)) * d
    colors = [F_COLORS.get(int(min(v, 5)), F_COLORS[5]) for v in f_all]

    fig, ax = plt.subplots(figsize=(11, 2.5))
    ax.bar(x, f_all, width=d * 0.88, color=colors, align="edge", linewidth=0)

    ax.axvline(300, color="#aaaaaa", linewidth=1.2, linestyle="--", alpha=0.6)
    ax.text(150, 5.35, "300m · discrete nodes",
            ha="center", fontsize=7.5, color="#aaaaaa")
    ax.text(600, 5.35, "600m · Bazaar Street (continuous f=5)",
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
        "Use the slider to simulate "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
        "remediation of the top-ranked hotspots."
    )
    st.markdown("---")

    # Load data
    try:
        df = load_audit_data()
    except FileNotFoundError:
        st.error("data/audit_log.csv not found. Please add the file and restart.")
        return
    except AssertionError as e:
        st.error(f"audit_log.csv schema error: {e}")
        return

    # Hotspot fix slider
    n_fixes = st.slider(
        "Hotspots fixed to Tender S.U.R.E. standard (top-N by f-value):",
        min_value=0, max_value=len(df), value=0, step=1,
    )

    st.markdown("---")

    # Map
    m = build_map(df, n_fixes)
    st_folium(m, width=None, height=520, returned_objects=[])

    st.markdown("---")

    # Friction gradient bar
    st.markdown("#### Friction Gradient — Full 900m Route")
    st.caption(
        "Each bar = one 12.5m segment · "
        "Left 24 = 300m discrete nodes · "
        "Right 48 = 600m Bazaar Street · "
        "Grey = fixed to f=1"
    )
    fig = plot_friction_bar(df, n_fixes)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Obstacle Distribution — 300m Stretch")
        dist = (
            df["f_value"]
            .value_counts()
            .sort_index()
            .reset_index()
            .rename(columns={"f_value": "f", "count": "Count"})
        )
        dist["Level"] = dist["f"].map(
            {v: l.split(" · ")[1] for v, l in F_LABELS.items()}
        )
        dist["Share"] = (dist["Count"] / len(df) * 100).round(1).astype(str) + "%"
        st.dataframe(
            dist[["f", "Level", "Count", "Share"]],
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.markdown("#### Live Friction Index")

        f_300 = df["f_value"].values.astype(float)
        if n_fixes > 0:
            f_fixed = f_300.copy()
            f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0
        else:
            f_fixed = f_300

        L_eff_300 = 12.5 * f_fixed.sum()
        L_eff_600 = 600 * 5.0
        L_eff_total = L_eff_300 + L_eff_600
        f_bar = L_eff_total / 900

        st.metric(
            "Mean friction index f̄",
            f"{f_bar:.3f}",
            delta=f"{f_bar - 4.653:.3f}" if n_fixes > 0 else None,
            delta_color="normal",
        )
        st.markdown(f"""
        | | Current | Baseline |
        |--|---------|---------|
        | $L_{{\\text{{eff}}}}$ (300m) | {L_eff_300:.1f} m | 1187.5 m |
        | $L_{{\\text{{eff}}}}$ (600m) | 3000.0 m | 3000.0 m |
        | $L_{{\\text{{eff}}}}$ total | {L_eff_total:.1f} m | 4187.5 m |
        | $\\bar{{f}}$ | {f_bar:.3f} | 4.653 |
        """)

    st.markdown("---")

    # Friction rubric
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
    })
    st.dataframe(rubric, hide_index=True, use_container_width=True)
