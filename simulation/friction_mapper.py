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
# INFOGRAPHIC CHARTS
# -------------------------------------------------------------------------

def plot_severity_donut(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    """
    Donut chart of friction distribution with callout annotations.
    Fixed nodes shown as f=1 slices.
    """
    f_vals = df["f_value"].values.astype(float).copy()
    if n_fixes > 0:
        f_vals[np.argsort(f_vals)[::-1][:n_fixes]] = 1.0

    counts = {}
    for f in [1, 2, 3, 4, 5]:
        counts[f] = int((f_vals == f).sum())

    # Only include levels that have nodes
    present = {f: c for f, c in counts.items() if c > 0}
    sizes   = list(present.values())
    labels  = list(present.keys())
    colors  = [F_COLORS[f] for f in labels]
    total   = sum(sizes)

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    wedges, _ = ax.pie(
        sizes,
        colors=colors,
        startangle=90,
        wedgeprops=dict(width=0.52, edgecolor="#1a1a1a", linewidth=2),
        counterclock=False,
    )

    # Centre text — headline stat
    ax.text(0, 0.12, f"{counts.get(5, 0) + counts.get(4, 0)}",
            ha="center", va="center", fontsize=34, fontweight="bold",
            color="white")
    ax.text(0, -0.18, "of 24 nodes", ha="center", va="center",
            fontsize=10, color="#aaaaaa")
    ax.text(0, -0.38, "f ≥ 4 · impassable", ha="center", va="center",
            fontsize=9, color="#FF9800")

    # Callout annotations for each wedge
    for wedge, f_level, count in zip(wedges, labels, sizes):
        pct = count / total * 100
        angle = (wedge.theta2 + wedge.theta1) / 2
        rad   = np.deg2rad(angle)
        r_mid = 0.82   # just outside the donut
        r_tip = 1.12
        r_txt = 1.22

        x_mid = r_mid * np.cos(rad)
        y_mid = r_mid * np.sin(rad)
        x_tip = r_tip * np.cos(rad)
        y_tip = r_tip * np.sin(rad)
        x_txt = r_txt * np.cos(rad)
        y_txt = r_txt * np.sin(rad)

        ax.annotate(
            "",
            xy=(x_tip, y_tip),
            xytext=(x_mid, y_mid),
            arrowprops=dict(arrowstyle="-", color=F_COLORS[f_level],
                            lw=1.2, alpha=0.7),
        )

        ha = "left" if x_txt > 0.05 else ("right" if x_txt < -0.05 else "center")
        ax.text(x_txt, y_txt,
                f"f={f_level}  {count} nodes\n{pct:.0f}%  {F_SHORT[f_level]}",
                ha=ha, va="center", fontsize=7.5,
                color=F_COLORS[f_level],
                linespacing=1.5)

    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.65, 1.65)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Obstacle Severity\n300m stretch · 24 nodes",
                 color="white", fontsize=10, pad=8)
    fig.tight_layout()
    return fig


def plot_leff_comparison(L_eff_base: float, L_eff_now: float,
                          f_bar_base: float, f_bar_now: float,
                          n_fixes: int, bazaar_f: int) -> plt.Figure:
    """
    Horizontal stacked bar comparing current vs scenario vs S.U.R.E. target.
    The bar encodes how much 'excess friction' remains.
    """
    scenarios = [
        ("Surveyed\n(baseline)",    L_eff_base, f_bar_base),
        (f"After {n_fixes} fix(es)\n+ Bazaar f={bazaar_f}", L_eff_now,  f_bar_now),
        ("Full S.U.R.E.\n(target)", 900.0,       1.0),
    ]

    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    bar_h = 0.38
    max_leff = max(s[1] for s in scenarios)

    for i, (label, leff, fbar) in enumerate(scenarios):
        y = i
        # Compliance portion (900m)
        ax.barh(y, 900, height=bar_h, color="#4CAF50", alpha=0.85,
                left=0, linewidth=0)
        # Excess portion
        excess = leff - 900
        if excess > 0:
            ax.barh(y, excess, height=bar_h, color="#F44336", alpha=0.85,
                    left=900, linewidth=0)

        # f-bar badge
        badge_x = leff + 60
        ax.text(badge_x, y, f"f̄ = {fbar:.3f}",
                va="center", ha="left", fontsize=8.5,
                color=F_COLORS[5] if fbar > 2 else (F_COLORS[4] if fbar > 1.5 else "#4CAF50"),
                fontweight="bold")

        # L_eff value inside bar
        ax.text(leff / 2, y, f"L_eff = {leff:.0f}m",
                va="center", ha="center", fontsize=8,
                color="white", fontweight="bold")

    # S.U.R.E. target line
    ax.axvline(900, color="#4CAF50", linewidth=1.5, linestyle="--", alpha=0.7,
               label="S.U.R.E. target (900m)")

    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels([s[0] for s in scenarios], fontsize=8, color="white")
    ax.set_xlabel("Effective path length (m)", fontsize=9, color="white")
    ax.set_xlim(0, max_leff * 1.3)
    ax.tick_params(colors="white", labelsize=8)
    ax.xaxis.label.set_color("white")
    ax.spines[:].set_visible(False)

    # Legend patches
    ax.legend(handles=[
        mpatches.Patch(color="#4CAF50", label="Compliant 900m"),
        mpatches.Patch(color="#F44336", label="Excess friction"),
    ], loc="lower right", fontsize=7.5,
       facecolor="#2a2a2a", labelcolor="white", framealpha=0.85)

    ax.set_title("Effective Path Length vs S.U.R.E. Target",
                 color="white", fontsize=10, pad=6)
    fig.tight_layout()
    return fig


def plot_sure_compliance_bar(f_bar_now: float) -> plt.Figure:
    """
    Single horizontal progress bar showing how close the corridor
    is to full S.U.R.E. compliance (f̄ = 1.0).
    """
    fig, ax = plt.subplots(figsize=(7, 1.2))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")

    # Background track
    ax.barh(0, 5.0, height=0.45, color="#2a2a2a", linewidth=0, left=1.0)
    # Current f̄ fill — colour interpolated red→orange→green
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
    ax.text(f_bar_now, 0.32,
            f" f̄ = {f_bar_now:.3f}",
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
    st.markdown(
        "Interactive map of the 900m Yeshwantpur–Constitution Circle corridor. "
        "Circle markers show the 24 geotagged obstacle nodes from the March 2026 "
        "field audit. The red polyline traces the 600m Bazaar Street stretch — "
        "a continuous $f = 5$ failure. "
        "Use the controls to simulate "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) "
        "remediation scenarios."
    )

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
            "Setting n=1 fixes the single worst obstacle. "
            "n=3 is the Lighthouse Pilot ask. "
            "n=24 models a fully remediated 300m stretch."
        )
    )

    if n_fixes == 0:
        st.sidebar.caption("📍 Showing surveyed conditions — no fixes applied.")
    elif n_fixes <= 3:
        st.sidebar.caption(
            f"🔧 **Lighthouse Pilot scenario** — {n_fixes} node(s) fixed. "
            "Minimum viable intervention argued in the DULT brief."
        )
    elif n_fixes <= 9:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — all f=5 obstacles on the 300m stretch remediated."
        )
    elif n_fixes <= 17:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — all f=4 and f=5 obstacles cleared. "
            "Stretch would be wheelchair-navigable for the first time."
        )
    else:
        st.sidebar.caption(
            f"🔧 {n_fixes} nodes fixed — full 300m stretch approaching S.U.R.E. compliance."
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
            "f=1 models full pipe-and-chamber drain replacement and continuous 3m footpath. "
            "f=2 models surface levelled but utilities still overhead."
        )
    )
    bazaar_f = sure_standards[bazaar_label]

    if bazaar_f < 5:
        st.sidebar.caption(
            f"Bazaar Street modelled at $f={bazaar_f}$ — speculative scenario under "
            "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) intervention."
        )

    # -----------------------------------------------------------------------
    # COMPUTE METRICS
    # -----------------------------------------------------------------------
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0:
        f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_base = 12.5 * f_300.sum()
    L_eff_300_now  = 12.5 * f_fixed.sum()
    L_eff_600_base = 600 * 5.0
    L_eff_600_now  = 600 * float(bazaar_f)
    L_eff_base     = L_eff_300_base + L_eff_600_base
    L_eff_now      = L_eff_300_now  + L_eff_600_now
    f_bar_base     = L_eff_base / 900
    f_bar_now      = L_eff_now  / 900
    n_impassable   = int((f_300 > 3).sum())

    st.markdown("---")

    # -----------------------------------------------------------------------
    # HEADLINE METRICS
    # -----------------------------------------------------------------------
    st.markdown("#### The State of the Corridor")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fails Active Mobility Bill", "90.3%",
                help="90.3% of the 900m stretch does not meet minimum pedestrian standards.")
    col2.metric("Wheelchair inaccessible", "96.0%",
                help="96% of the route has f > f_max for wheelchair users (f_max = 3).")
    col3.metric(
        "Impassable nodes (f ≥ 4)", f"{n_impassable} / 24",
        delta=f"−{n_impassable - int((f_fixed > 3).sum())} after fixes" if n_fixes > 0 else None,
        delta_color="normal",
        help="Nodes rated f=4 or f=5 force pedestrians into vehicular Right-of-Way."
    )
    col4.metric(
        "Effective path multiplier", f"{f_bar_now:.2f}×",
        delta=f"{f_bar_now - f_bar_base:.3f}" if (n_fixes > 0 or bazaar_f < 5) else None,
        delta_color="normal",
        help=f"The corridor makes a 900m walk feel like {f_bar_now:.2f}× that distance."
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
    fig_bar = plot_friction_bar(df, n_fixes, bazaar_f)
    st.pyplot(fig_bar, use_container_width=True)
    plt.close(fig_bar)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # INFOGRAPHIC STATS SECTION
    # -----------------------------------------------------------------------
    st.markdown("#### Corridor Analysis")

    col_donut, col_right = st.columns([1.5, 1.4])

    with col_donut:
        st.caption("Obstacle severity breakdown — 300m stretch")
        fig_donut = plot_severity_donut(df, n_fixes)
        st.pyplot(fig_donut)
        plt.close(fig_donut)

    with col_right:
        st.caption("S.U.R.E. compliance gauge — mean friction index f̄")
        fig_gauge = plot_sure_compliance_bar(f_bar_now)
        st.pyplot(fig_gauge, use_container_width=True)
        plt.close(fig_gauge)

        st.markdown("")
        st.caption("Effective path length — current vs scenario vs target")
        fig_leff = plot_leff_comparison(
            L_eff_base, L_eff_now, f_bar_base, f_bar_now, n_fixes, bazaar_f
        )
        st.pyplot(fig_leff, use_container_width=True)
        plt.close(fig_leff)

        pct_recovered = (L_eff_base - L_eff_now) / (L_eff_base - 900) * 100 \
            if (n_fixes > 0 or bazaar_f < 5) and (L_eff_base - 900) > 0 else 0
        if pct_recovered > 0:
            st.success(
                f"This scenario recovers **{pct_recovered:.1f}%** of the excess "
                "effective path length above the S.U.R.E. target."
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
