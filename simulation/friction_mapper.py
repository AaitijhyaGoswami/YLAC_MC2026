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
    1: "#4CAF50",  # green
    2: "#FFEB3B",  # yellow
    3: "#FF9800",  # orange
    4: "#F44336",  # red
    5: "#212121",  # near-black
}

F_LABELS = {
    1: "f=1 · Gold Standard",
    2: "f=2 · Distracted Walk",
    3: "f=3 · Obstacle Course",
    4: "f=4 · Physical Barrier",
    5: "f=5 · Systemic Failure",
}

# 600m Bazaar Street stretch bounding box (approximate)
# SW corner, NE corner — used for the rectangle overlay
BAZAAR_ST_BOUNDS = [
    [13.0195, 77.5530],  # SW
    [13.0240, 77.5560],  # NE
]

# Map centre — midpoint of the full survey area
MAP_CENTRE = [13.0195, 77.5560]

# -------------------------------------------------------------------------
# DATA LOADER
# -------------------------------------------------------------------------

@st.cache_data
def load_audit_data() -> pd.DataFrame:
    """Load and validate audit_log.csv."""
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
    Build the Folium map with:
    - Circle markers for each of the 24 geotagged obstacle nodes
    - Shaded rectangle for the continuous 600m f=5 Bazaar Street stretch
    - Fixes shown in green when n_fixes > 0
    """
    m = folium.Map(
        location=MAP_CENTRE,
        zoom_start=16,
        tiles="CartoDB dark_matter",
    )

    # --- 600m Bazaar Street stretch — shaded rectangle ---
    folium.Rectangle(
        bounds=BAZAAR_ST_BOUNDS,
        color="#F44336",
        fill=True,
        fill_color="#F44336",
        fill_opacity=0.15,
        weight=2,
        tooltip="600m Bazaar Street — continuous f=5 (Systemic Failure)",
    ).add_to(m)

    folium.Marker(
        location=[13.0218, 77.5545],
        icon=folium.DivIcon(
            html='<div style="font-size:10px;color:#F44336;font-weight:bold;'
                 'white-space:nowrap">600m · f=5 · Bazaar Street</div>',
            icon_size=(180, 20),
        ),
    ).add_to(m)

    # --- 300m stretch obstacle pins ---
    # Determine which nodes are fixed (sorted descending by f_value)
    f_values = df["f_value"].values.astype(float)
    fix_indices = set(
        df.index[np.argsort(f_values)[::-1][:n_fixes]]
    ) if n_fixes > 0 else set()

    for idx, row in df.iterrows():
        is_fixed = idx in fix_indices
        f = int(row["f_value"])
        color = "#4CAF50" if is_fixed else F_COLORS.get(f, "#212121")
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
      <span style="color:#4CAF50">●</span> f=1 · Gold Standard / Fixed<br>
      <span style="color:#FFEB3B">●</span> f=2 · Distracted Walk<br>
      <span style="color:#FF9800">●</span> f=3 · Obstacle Course<br>
      <span style="color:#F44336">●</span> f=4 · Physical Barrier<br>
      <span style="color:#555;background:#212121;padding:0 3px">●</span> f=5 · Systemic Failure<br>
      <hr style="border-color:#444;margin:5px 0">
      <span style="color:#F44336">▬▬</span> 600m Bazaar St (continuous f=5)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    return m


# -------------------------------------------------------------------------
# FRICTION GRADIENT BAR CHART
# -------------------------------------------------------------------------

def plot_friction_bar(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    """
    Colour-coded bar chart showing f-value per segment across the full 900m.
    Left 24 bars = 300m discrete nodes. Right 48 bars = 600m Bazaar St (f=5).
    Fixed nodes shown in green.
    """
    f_300 = df["f_value"].values.astype(float)

    if n_fixes > 0:
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300_display = f_300.copy()
        f_300_display[fix_idx] = 1.0
    else:
        f_300_display = f_300.copy()

    f_600 = np.full(48, 5.0)
    f_all = np.concatenate([f_300_display, f_600])

    d = 12.5
    x = np.arange(len(f_all)) * d
    colors = [F_COLORS.get(int(min(v, 5)), "#212121") for v in f_all]

    fig, ax = plt.subplots(figsize=(11, 2.5))
    ax.bar(x, f_all, width=d * 0.88, color=colors, align="edge", linewidth=0)

    # Zone divider
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
        "field audit. The shaded rectangle covers the 600m Bazaar Street stretch — "
        "a continuous $f = 5$ failure with no discrete nodes. "
        "Use the slider below to simulate "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) remediation "
        "of the top-ranked hotspots."
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
        "Hotspots fixed (top-N by f-value):",
        min_value=0, max_value=len(df), value=0, step=1,
        help="Sets the top-N highest-friction nodes to f=1 (Tender S.U.R.E. standard)"
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
        "Left 24 bars = 300m discrete nodes · "
        "Right 48 bars = 600m Bazaar Street · "
        "Green = fixed to f=1"
    )
    fig = plot_friction_bar(df, n_fixes)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.markdown("---")

    # Summary stats
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
        dist["Level"] = dist["f"].map({v: l.split(" · ")[1] for v, l in F_LABELS.items()})
        dist["Share"] = (dist["Count"] / len(df) * 100).round(1).astype(str) + "%"
        st.dataframe(
            dist[["f", "Level", "Count", "Share"]],
            hide_index=True,
            use_container_width=True,
        )

    with col2:
        st.markdown("#### Zone Summary")
        st.markdown(f"""
        | Zone | Length | Nodes | Treatment |
        |------|--------|-------|-----------|
        | Constitution Circle stretch | 300m | 24 discrete | Per-node $f$ from audit |
        | Bazaar Street stretch | 600m | — | Continuous $f = 5$ |
        | **Full corridor** | **900m** | **24** | **$\\bar{{f}} = 4.653$** |
        """)

        # Mean friction index
        f_300 = df["f_value"].values.astype(float)
        if n_fixes > 0:
            f_fixed = f_300.copy()
            f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0
        else:
            f_fixed = f_300

        L_eff_300 = 12.5 * f_fixed.sum()
        L_eff_600 = 600 * 5
        L_eff_total = L_eff_300 + L_eff_600
        f_bar = L_eff_total / 900

        st.metric(
            "Mean friction index after fixes",
            f"{f_bar:.3f}",
            delta=f"{f_bar - 4.653:.3f}" if n_fixes > 0 else None,
            delta_color="normal",
        )

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
