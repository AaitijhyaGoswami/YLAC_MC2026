import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import folium
from streamlit_folium import st_folium

# -------------------------------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="Escape the Knot",
    page_icon="🚶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------
# SURVEY DATA
# Hardcoded from the March 7-8 2026 field audit.
# Replace with pd.read_csv("data/audit_log.csv") once the file exists.
#
# Structure:
#   300m Constitution Circle stretch — 24 discrete geotagged obstacles
#   600m Bazaar Street stretch       — continuous f=5 (no discrete nodes)
# -------------------------------------------------------------------------

# 24 geotagged obstacle nodes on the 300m stretch
# (lat, lon, f_value, description)
OBSTACLES_300 = [
    # f=5 nodes (9)
    (13.0227, 77.5551, 5, "Transformer block — footpath ends, ROW entry forced"),
    (13.0224, 77.5549, 5, "Permanent encroachment — vendor stall on footpath"),
    (13.0221, 77.5547, 5, "Construction debris — path fully blocked"),
    (13.0218, 77.5545, 5, "Permanent encroachment — footpath ends at shop"),
    (13.0215, 77.5543, 5, "Open box drain — no cover, full width of footpath"),
    (13.0212, 77.5541, 5, "Encroachment — bike parking on footpath"),
    (13.0209, 77.5539, 5, "Utility pole cluster — impassable for wheelchair"),
    (13.0206, 77.5537, 5, "Footpath ends at building setback"),
    (13.0203, 77.5535, 5, "Transformer — footpath fully occupied"),
    # f=4 nodes (8)
    (13.0228, 77.5552, 4, "Missing drain cover — high step to avoid"),
    (13.0225, 77.5550, 4, "High kerb discontinuity — forces road crossing"),
    (13.0222, 77.5548, 4, "Large rubble heap — path width reduced to <0.3m"),
    (13.0219, 77.5546, 4, "Parked auto-rickshaw on footpath"),
    (13.0216, 77.5544, 4, "Exposed drain — partial cover missing"),
    (13.0213, 77.5542, 4, "Utility excavation trench across footpath"),
    (13.0210, 77.5540, 4, "High kerb without ramp — inaccessible for wheelchair"),
    (13.0207, 77.5538, 4, "Street furniture blocking path width"),
    # f=3 nodes (4)
    (13.0229, 77.5553, 3, "Broken slab — jump discontinuity, ~15cm drop"),
    (13.0226, 77.5551, 3, "Loose paving — unstable underfoot"),
    (13.0223, 77.5549, 3, "Rubble from recent utility digging"),
    (13.0220, 77.5547, 3, "Uneven surface — low-hanging cable overhead"),
    # f=2 nodes (3)
    (13.0230, 77.5554, 2, "Unlevelled maintenance hole slab"),
    (13.0217, 77.5545, 2, "Minor crack — requires attention"),
    (13.0211, 77.5540, 2, "Sloped discontinuity at driveway cut"),
]

# Route polyline: SWR exit → Constitution Circle (300m) → Bazaar St terminus (600m)
# Simplified representative coordinates
ROUTE_COORDS = [
    (13.0195, 77.5530),  # SWR exit / start of 300m stretch
    (13.0200, 77.5533),
    (13.0207, 77.5537),
    (13.0215, 77.5543),
    (13.0222, 77.5548),
    (13.0230, 77.5554),  # Constitution Circle — end of 300m, start of 600m
    (13.0238, 77.5559),
    (13.0246, 77.5565),
    (13.0255, 77.5572),
    (13.0264, 77.5579),
    (13.0272, 77.5585),  # Mid-Bazaar Street
    (13.0281, 77.5592),
    (13.0290, 77.5599),
    (13.0298, 77.5605),  # Yeshwantpur Railway Station end
]

ZONE_BOUNDARY = (13.0230, 77.5554)  # Constitution Circle

# -------------------------------------------------------------------------
# PERSONA DEFINITIONS
# v0     : free-walking speed (m/s)
# k      : friction sensitivity exponent in v_eff = v0 / f^k
# f_max  : impassability threshold; nodes above this → ROW detour
# alpha  : ROW velocity penalty multiplier (shared across all personas)
# delta  : mean detour length per impassable node (m)
# weight : population share weight for aggregate calculations
# -------------------------------------------------------------------------
PERSONAS = {
    "🚶 Able-bodied adult": {
        "v0": 1.4, "k": 0.6, "f_max": 5,
        "alpha": 1.5, "delta": 8.0, "weight": 0.45,
        "color": "#2196F3",
        "desc": "v₀ = 1.4 m/s · k = 0.6 · f_max = 5",
    },
    "👴 Elderly commuter": {
        "v0": 0.9, "k": 0.9, "f_max": 4,
        "alpha": 1.5, "delta": 10.0, "weight": 0.20,
        "color": "#FF9800",
        "desc": "v₀ = 0.9 m/s · k = 0.9 · f_max = 4",
    },
    "♿ Wheelchair user": {
        "v0": 0.8, "k": 1.2, "f_max": 3,
        "alpha": 1.5, "delta": 15.0, "weight": 0.10,
        "color": "#9C27B0",
        "desc": "v₀ = 0.8 m/s · k = 1.2 · f_max = 3 → ROW detour",
    },
    "🛵 Delivery partner": {
        "v0": 1.2, "k": 0.75, "f_max": 4,
        "alpha": 1.5, "delta": 8.0, "weight": 0.25,
        "color": "#F44336",
        "desc": "v₀ = 1.2 m/s · k = 0.75 · f_max = 4",
    },
}

# -------------------------------------------------------------------------
# FRICTION COLOUR MAP
# -------------------------------------------------------------------------
F_COLORS = {
    1: "#4CAF50",   # green
    2: "#FFEB3B",   # yellow
    3: "#FF9800",   # orange
    4: "#F44336",   # red
    5: "#212121",   # near-black
}
F_LABELS = {
    1: "f=1 · Gold Standard",
    2: "f=2 · Distracted Walk",
    3: "f=3 · Obstacle Course",
    4: "f=4 · Physical Barrier",
    5: "f=5 · Systemic Failure",
}

# -------------------------------------------------------------------------
# SIMULATION CORE
# Implements the math from the README exactly.
# -------------------------------------------------------------------------

def build_segment_array(n_fixes: int = 0) -> np.ndarray:
    """
    Build the full f-value array for the 900m route.

    300m stretch: 24 discrete obstacle nodes, d = 12.5m each.
    600m stretch: continuous f=5, represented as 48 segments of 12.5m each.

    n_fixes: number of top-impact nodes in the 300m stretch to set to f=1
             (sorted descending by f to maximise impact).
    Returns array of f-values, length 72 (24 + 48).
    """
    f_300 = np.array([obs[2] for obs in OBSTACLES_300], dtype=float)

    if n_fixes > 0:
        # Sort indices by f descending; set the top n_fixes to 1
        fix_idx = np.argsort(f_300)[::-1][:n_fixes]
        f_300[fix_idx] = 1.0

    f_600 = np.full(48, 5.0)
    return np.concatenate([f_300, f_600])


def run_simulation(persona_key: str, n_fixes: int = 0) -> dict:
    """
    Compute traversal time, Time Tax, and per-segment breakdown for one persona.

    Returns a dict with:
        T_actual   : total actual traversal time (s)
        T_ideal    : ideal traversal time at f=1 throughout (s)
        delta_tau  : Time Tax per trip (s)
        tau_i      : per-segment traversal times (array, s)
        f_array    : f-values used (after fixes applied)
        n_detours  : number of impassable segments rerouted to ROW
        d          : segment length (m)
    """
    p = PERSONAS[persona_key]
    v0, k, f_max, alpha, delta_m = p["v0"], p["k"], p["f_max"], p["alpha"], p["delta"]

    d = 12.5  # metres per segment (300/24 = 600/48 = 12.5)
    f_array = build_segment_array(n_fixes)
    N = len(f_array)

    tau_i = np.empty(N)
    n_detours = 0

    for i, fi in enumerate(f_array):
        if fi > f_max:
            # Impassable — reroute to ROW
            tau_i[i] = (d + delta_m) * alpha / v0
            n_detours += 1
        else:
            # Power-law velocity: v_eff = v0 / f^k
            v_eff = v0 / (fi ** k)
            tau_i[i] = d / v_eff

    T_actual = tau_i.sum()
    T_ideal = (N * d) / v0
    delta_tau = T_actual - T_ideal

    return {
        "T_actual": T_actual,
        "T_ideal": T_ideal,
        "delta_tau": delta_tau,
        "tau_i": tau_i,
        "f_array": f_array,
        "n_detours": n_detours,
        "d": d,
    }


def aggregate_time_tax(n_fixes: int = 0) -> float:
    """Persona-weighted mean Time Tax per trip (seconds)."""
    total_weight = sum(p["weight"] for p in PERSONAS.values())
    weighted_sum = sum(
        run_simulation(key, n_fixes)["delta_tau"] * p["weight"]
        for key, p in PERSONAS.items()
    )
    return weighted_sum / total_weight


def economic_loss(mean_delta_tau_s: float, M: int = 100_000, W: int = 250) -> dict:
    """
    Convert mean Time Tax to annual economic loss.
    Wage rate: ₹50/hr for informal workers (RBI implicit rate).
    """
    annual_person_minutes = M * W * (mean_delta_tau_s / 60)
    wage_per_minute = 50 / 60  # ₹/min
    annual_loss_rs = annual_person_minutes * wage_per_minute
    return {
        "annual_person_minutes": annual_person_minutes,
        "annual_loss_rs": annual_loss_rs,
        "annual_loss_crore": annual_loss_rs / 1e7,
    }


def what_if_saved(persona_key: str, n_fixes: int) -> float:
    """
    Time Tax reduction for persona when top-n_fixes hotspots set to f=1.
    Δτ_saved = Δτ(0 fixes) − Δτ(n fixes)
    """
    base = run_simulation(persona_key, n_fixes=0)["delta_tau"]
    fixed = run_simulation(persona_key, n_fixes=n_fixes)["delta_tau"]
    return base - fixed


# -------------------------------------------------------------------------
# PLOT HELPERS
# -------------------------------------------------------------------------

def plot_friction_bar(f_array: np.ndarray, persona_key: str) -> plt.Figure:
    """Colour-coded per-segment friction bar across the 900m route."""
    d = 12.5
    x = np.arange(len(f_array)) * d
    colors = [F_COLORS.get(int(min(f, 5)), "#212121") for f in f_array]

    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.bar(x, f_array, width=d * 0.9, color=colors, align="edge", linewidth=0)
    ax.axvline(300, color="white", linewidth=2, linestyle="--", alpha=0.8)
    ax.text(150, 5.25, "300m — discrete nodes", ha="center", fontsize=8,
            color="#aaaaaa")
    ax.text(600, 5.25, "600m — continuous f=5 (Bazaar St)", ha="center",
            fontsize=8, color="#aaaaaa")
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 5.6)
    ax.set_xlabel("Distance along route (m)", fontsize=9)
    ax.set_ylabel("Friction f", fontsize=9)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)

    legend_patches = [
        mpatches.Patch(color=F_COLORS[f], label=F_LABELS[f])
        for f in sorted(F_COLORS)
    ]
    ax.legend(handles=legend_patches, loc="upper left", fontsize=7,
              facecolor="#2a2a2a", labelcolor="white", framealpha=0.8,
              ncol=5)
    fig.tight_layout()
    return fig


def plot_time_tax_comparison(persona_key: str, n_fixes: int) -> plt.Figure:
    """Bar chart: T_ideal vs T_actual (current and fixed)."""
    result_current = run_simulation(persona_key, n_fixes=0)
    result_fixed = run_simulation(persona_key, n_fixes=n_fixes)

    labels = ["Ideal\n(f=1 throughout)", "Current\n(surveyed)", f"After fixing\ntop {n_fixes} hotspots"]
    values = [
        result_current["T_ideal"] / 60,
        result_current["T_actual"] / 60,
        result_fixed["T_actual"] / 60,
    ]
    colors = ["#4CAF50", "#F44336", "#FF9800"]

    fig, ax = plt.subplots(figsize=(5.5, 3.8))
    bars = ax.bar(labels, values, color=colors, width=0.55, linewidth=0)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.05,
                f"{val:.1f} min", ha="center", va="bottom",
                fontsize=9, color="white", fontweight="bold")
    ax.set_ylabel("Traversal time (min)", fontsize=9)
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_all_personas_tax(n_fixes: int) -> plt.Figure:
    """Horizontal bar chart of Time Tax per persona, current vs fixed."""
    persona_names = list(PERSONAS.keys())
    current_taxes = [run_simulation(k, 0)["delta_tau"] / 60 for k in persona_names]
    fixed_taxes = [run_simulation(k, n_fixes)["delta_tau"] / 60 for k in persona_names]

    y = np.arange(len(persona_names))
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.barh(y + 0.2, current_taxes, height=0.35, color="#F44336", label="Current")
    ax.barh(y - 0.2, fixed_taxes, height=0.35, color="#FF9800", label=f"After {n_fixes} fixes")

    ax.set_yticks(y)
    ax.set_yticklabels(persona_names, fontsize=9)
    ax.set_xlabel("Time Tax per trip (min)", fontsize=9)
    ax.legend(fontsize=8, facecolor="#2a2a2a", labelcolor="white")
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def plot_savings_curve(persona_key: str) -> plt.Figure:
    """Marginal Time Tax saved as n_fixes increases from 0 to 24."""
    n_range = range(0, 25)
    savings = [what_if_saved(persona_key, n) / 60 for n in n_range]

    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(n_range, savings, color=PERSONAS[persona_key]["color"],
            linewidth=2.5, marker="o", markersize=4)
    ax.set_xlabel("Number of hotspots fixed (top-N)", fontsize=9)
    ax.set_ylabel("Time Tax saved (min)", fontsize=9)
    ax.set_xticks(range(0, 25, 3))
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig


def build_folium_map(n_fixes: int = 0) -> folium.Map:
    """
    Folium map with:
    - Route polyline (colour-coded by zone)
    - Obstacle pins (colour-coded by f-value, with fixes shown in green)
    - Zone boundary marker
    """
    m = folium.Map(
        location=[13.0240, 77.5562],
        zoom_start=15,
        tiles="CartoDB dark_matter",
    )

    # Route polyline — 300m stretch in amber, 600m stretch in red
    boundary_idx = 6  # index in ROUTE_COORDS where Bazaar St begins
    folium.PolyLine(
        ROUTE_COORDS[:boundary_idx + 1],
        color="#FF9800", weight=4, opacity=0.85,
        tooltip="300m Constitution Circle stretch"
    ).add_to(m)
    folium.PolyLine(
        ROUTE_COORDS[boundary_idx:],
        color="#F44336", weight=4, opacity=0.85,
        tooltip="600m Bazaar Street — continuous f=5"
    ).add_to(m)

    # Zone boundary
    folium.Marker(
        ZONE_BOUNDARY,
        icon=folium.DivIcon(
            html='<div style="font-size:10px;color:white;background:#333;'
                 'padding:2px 5px;border-radius:3px;white-space:nowrap">'
                 'Constitution Circle</div>',
            icon_size=(130, 20),
        ),
        tooltip="Constitution Circle — zone boundary"
    ).add_to(m)

    # Obstacle pins
    f_values = np.array([obs[2] for obs in OBSTACLES_300], dtype=float)
    if n_fixes > 0:
        fix_idx = np.argsort(f_values)[::-1][:n_fixes]
    else:
        fix_idx = np.array([], dtype=int)

    for i, (lat, lon, f, desc) in enumerate(OBSTACLES_300):
        is_fixed = i in fix_idx
        color = "#4CAF50" if is_fixed else F_COLORS.get(f, "#212121")
        label = "FIXED" if is_fixed else F_LABELS.get(f, f"f={f}")
        folium.CircleMarker(
            location=(lat, lon),
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.9,
            tooltip=f"[{label}] {desc}",
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="position:fixed;bottom:20px;left:20px;z-index:9999;
         background:#1a1a1a;padding:10px 14px;border-radius:8px;
         border:1px solid #444;font-family:monospace;font-size:12px;color:white">
      <b>Friction Level</b><br>
      <span style="color:#4CAF50">●</span> f=1 Gold Standard / Fixed<br>
      <span style="color:#FFEB3B">●</span> f=2 Distracted Walk<br>
      <span style="color:#FF9800">●</span> f=3 Obstacle Course<br>
      <span style="color:#F44336">●</span> f=4 Physical Barrier<br>
      <span style="color:#212121;background:#555;padding:0 2px">●</span> f=5 Systemic Failure<br>
      <hr style="border-color:#444;margin:5px 0">
      <span style="color:#FF9800">━━</span> 300m stretch<br>
      <span style="color:#F44336">━━</span> 600m Bazaar St (f=5)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m


# -------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------------------------------
st.sidebar.title("🚶 Escape the Knot")
st.sidebar.caption("Yeshwantpur Mobility Audit · YLAC 2026")

pages = [
    "Home",
    "Friction Mapper",
    "Time Tax Simulator",
    "What-If: Lighthouse Pilot",
    "Economic Impact",
]
page = st.sidebar.radio("Navigate:", pages)

st.sidebar.markdown("---")

# Global controls (used by simulator pages)
st.sidebar.markdown("**Simulation Controls**")

selected_persona = st.sidebar.selectbox(
    "Commuter persona:",
    list(PERSONAS.keys()),
)

n_fixes = st.sidebar.slider(
    "Hotspots fixed (top-N by impact):",
    min_value=0, max_value=24, value=0, step=1,
)

st.sidebar.markdown("---")
st.sidebar.caption(
    "**Aaitijhya Goswami** · Simulation & Modelling\n\n"
    "**Prajwal Kagalgomb** · Data & Advocacy\n\n"
    "Partner: [Bengawalk](https://bengawalk.com)"
)


# =========================================================================
# PAGE: HOME
# =========================================================================
if page == "Home":
    st.title("Escape the Knot")
    st.markdown("##### Pedestrian Mobility Audit & Agent-Based Simulation · Yeshwantpur, Bengaluru")
    st.markdown("---")

    st.markdown(
        "A physics-driven audit of the 900m Yeshwantpur–Constitution Circle corridor, "
        "quantifying the **infrastructural tax** imposed on 100,000+ daily commuters "
        "through broken drains, encroachments, and missing footpaths. "
        "Each obstacle is assigned a friction value `f ∈ {1–5}` and the route's "
        "effective path length is computed as "
        r"$L_{eff} = \int_0^D f(x,\phi)\,dx$. "
        "The result is a **Time Tax** — and a data-backed case for a "
        "[Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) Lighthouse Pilot."
    )

    st.info("👈 Select a module from the sidebar to begin.")

    st.markdown("---")
    st.markdown("**Survey · March 7–8, 2026 · 900m corridor**")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fails Active Mobility Bill", "90.3%")
    col2.metric("Inaccessible for wheelchairs", "96.0%")
    col3.metric("Mean friction index f̄", "4.65")
    col4.metric("Effective path multiplier", "4.65×")

    st.markdown("---")

    st.markdown(
        "| Module | What it does |\n"
        "|--------|-------------|\n"
        "| 🗺️ **Friction Mapper** | Interactive map · colour-coded obstacle pins · zone friction bar |\n"
        "| ⏱️ **Time Tax Simulator** | Per-persona traversal time · power-law velocity model · segment breakdown |\n"
        "| 💡 **What-If: Lighthouse Pilot** | Slide N hotspot fixes · marginal savings curve · fix schedule |\n"
        "| 💰 **Economic Impact** | Annual person-minutes lost · ₹ crore loss · benefit-cost ratio |\n"
    )

    st.markdown("---")
    st.caption(
        "Built for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "[DULT Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en)"
    )


# =========================================================================
# PAGE: FRICTION MAPPER
# =========================================================================
elif page == "Friction Mapper":
    st.title("Spatial Friction Mapper")
    st.markdown(
        "Interactive map of the 900m Yeshwantpur corridor with colour-coded "
        "friction pins. Use the **Hotspots fixed** slider in the sidebar to see "
        "how the map changes when top-impact nodes are remediated."
    )
    st.markdown("---")

    # Map
    m = build_folium_map(n_fixes)
    st_folium(m, width=None, height=520)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Route Zones")
        st.markdown("""
        | Zone | Length | Friction |
        |------|--------|---------|
        | Constitution Circle stretch | 300m | 24 discrete nodes |
        | Bazaar Street stretch | 600m | Continuous f=5 |
        | **Full corridor** | **900m** | **f̄ = 4.653** |
        """)

    with col2:
        st.markdown("#### Obstacle Distribution (300m stretch)")
        dist_data = pd.DataFrame({
            "Level": ["f=5 · Systemic Failure", "f=4 · Physical Barrier",
                      "f=3 · Obstacle Course", "f=2 · Distracted Walk"],
            "Count": [9, 8, 4, 3],
            "Share": ["37.5%", "33.3%", "16.7%", "12.5%"],
        })
        st.dataframe(dist_data, hide_index=True, use_container_width=True)

    # Friction gradient bar
    st.markdown("---")
    st.markdown("#### Friction Gradient — Full 900m Route")
    st.caption(
        "Each bar = one 12.5m segment. Left 24 bars = 300m discrete stretch. "
        "Right 48 bars = 600m Bazaar Street (all f=5). "
        "Green bars = fixed hotspots."
    )
    f_array = build_segment_array(n_fixes)
    fig = plot_friction_bar(f_array, selected_persona)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # Friction rubric table
    st.markdown("---")
    st.markdown("#### Friction Rubric (Active Mobility Bill)")
    rubric = pd.DataFrame({
        "f": [1, 2, 3, 4, 5],
        "Label": ["Gold Standard", "Distracted Walk", "Obstacle Course",
                  "Physical Barrier", "Systemic Failure"],
        "Infrastructure State": [
            "Continuous, unobstructed 3m+ footpath",
            "Minor cracks, unlevelled slabs, low cables",
            "Broken slabs, rubble, utility excavation",
            "Missing drain cover, high kerb, partial blockage",
            "Footpath ends — transformer, encroachment, construction",
        ],
        "Speed Impact": ["v = v₀", "v ≈ 0.85v₀", "v ≈ 0.50v₀", "v ≈ 0.25v₀", "v → 0 (ROW)"],
        "Wheelchair Access": ["Full", "Partial", "Severely restricted",
                              "Effectively impassable", "Fully impassable"],
    })
    st.dataframe(rubric, hide_index=True, use_container_width=True)


# =========================================================================
# PAGE: TIME TAX SIMULATOR
# =========================================================================
elif page == "Time Tax Simulator":
    st.title("Agent-Based Time Tax Simulator")
    st.markdown(
        f"Simulating: **{selected_persona}** · "
        f"{PERSONAS[selected_persona]['desc']}"
    )
    st.markdown("---")

    result = run_simulation(selected_persona, n_fixes)
    p = PERSONAS[selected_persona]

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ideal traversal time", f"{result['T_ideal']/60:.1f} min")
    col2.metric(
        "Actual traversal time",
        f"{result['T_actual']/60:.1f} min",
        delta=f"+{result['delta_tau']/60:.1f} min",
        delta_color="inverse",
    )
    col3.metric("Time Tax Δτ", f"{result['delta_tau']:.0f} s")
    col4.metric("ROW detours", f"{result['n_detours']} segments")

    st.markdown("---")

    col_left, col_right = st.columns([1.1, 1])

    with col_left:
        st.markdown("#### Traversal Time Comparison")
        st.caption(
            "Ideal = fully compliant f=1 route. "
            f"Current = surveyed Yeshwantpur conditions. "
            f"After fixes = top {n_fixes} hotspots set to f=1."
        )
        fig = plot_time_tax_comparison(selected_persona, n_fixes)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with col_right:
        st.markdown("#### Friction Gradient (this persona)")
        fig2 = plot_friction_bar(result["f_array"], selected_persona)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

    # Physics breakdown
    st.markdown("---")
    st.markdown("#### Physics Breakdown")

    with st.expander("Show derivation and segment-level data"):
        st.markdown(f"""
        **Power-law velocity model:**
        $$v_{{eff}}(i, \\phi) = \\frac{{v_0}}{{f_i^k}} = \\frac{{{p['v0']}}}{{f_i^{{{p['k']}}}}}$$

        **Traversal time per segment** (d = 12.5m):
        $$\\tau_i = \\frac{{d \\cdot f_i^k}}{{v_0}}$$

        **For impassable nodes** (f > f_max = {p['f_max']}), ROW detour:
        $$\\tau_i^{{ROW}} = \\frac{{(d + \\delta) \\cdot \\alpha}}{{v_0}}
        = \\frac{{(12.5 + {p['delta']}) \\times {p['alpha']}}}{{{p['v0']}}}
        = {(12.5 + p['delta']) * p['alpha'] / p['v0']:.1f} \\text{{ s}}$$

        **Time Tax:**
        $$\\Delta\\tau = T_{{actual}} - T_{{ideal}}
        = {result['T_actual']:.1f} - {result['T_ideal']:.1f}
        = {result['delta_tau']:.1f} \\text{{ s}}$$
        """)

        # Per-segment table (first 24 nodes only for readability)
        seg_df = pd.DataFrame({
            "Segment": range(1, len(result["f_array"]) + 1),
            "Zone": ["300m stretch"] * 24 + ["600m Bazaar St"] * 48,
            "f value": result["f_array"],
            "Impassable": result["f_array"] > p["f_max"],
            "τᵢ (s)": np.round(result["tau_i"], 2),
        })
        st.dataframe(seg_df, use_container_width=True, height=280)


# =========================================================================
# PAGE: WHAT-IF LIGHTHOUSE PILOT
# =========================================================================
elif page == "What-If: Lighthouse Pilot":
    st.title("What-If: Lighthouse Pilot")
    st.markdown(
        "How much Time Tax is recovered by fixing the top-N friction hotspots? "
        "The slider in the sidebar controls N. Nodes are ranked by "
        f"`f_j^k` for the selected persona (**{selected_persona}**)."
    )
    st.markdown("---")

    saved = what_if_saved(selected_persona, n_fixes)
    base_tax = run_simulation(selected_persona, 0)["delta_tau"]
    pct_saved = (saved / base_tax * 100) if base_tax > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Time Tax saved per trip", f"{saved:.0f} s")
    col2.metric("Percentage recovered", f"{pct_saved:.1f}%")
    col3.metric("Hotspots fixed", f"{n_fixes} / 24")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Time Tax per Persona — Current vs Fixed")
        fig = plot_all_personas_tax(n_fixes)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

    with col_right:
        st.markdown(f"#### Marginal Savings Curve — {selected_persona}")
        st.caption(
            "Each point shows cumulative Time Tax saved when fixing that many "
            "top-ranked hotspots. The curve flattens as lower-f nodes are reached."
        )
        fig2 = plot_savings_curve(selected_persona)
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)

    st.markdown("---")
    st.markdown("#### Top-N Hotspot Fix Schedule")
    st.caption("Sorted by descending impact (f value). 'Fixed' = set to f=1 in simulation.")

    f_values = np.array([obs[2] for obs in OBSTACLES_300], dtype=float)
    sorted_idx = np.argsort(f_values)[::-1]

    fix_table = []
    for rank, idx in enumerate(sorted_idx, 1):
        lat, lon, f, desc = OBSTACLES_300[idx]
        fix_table.append({
            "Rank": rank,
            "f": int(f),
            "Level": F_LABELS[f].split(" · ")[1],
            "Description": desc,
            "Fixed in sim": "✅" if rank <= n_fixes else "—",
        })

    st.dataframe(
        pd.DataFrame(fix_table),
        hide_index=True,
        use_container_width=True,
        height=320,
    )

    # What-if formula display
    st.markdown("---")
    with st.expander("Show what-if formula"):
        p = PERSONAS[selected_persona]
        st.markdown(f"""
        Nodes are sorted descending by $f_j^{{k(\\phi)}}$ where $k = {p['k']}$.
        For the top $n$ nodes:

        $$\\Delta\\tau_{{saved}}(n, \\phi) = \\frac{{d}}{{v_0(\\phi)}}
        \\sum_{{j=1}}^{{n}} \\left( f_j^{{\\,k(\\phi)}} - 1 \\right)
        = \\frac{{12.5}}{{{p['v0']}}}
        \\sum_{{j=1}}^{{n}} \\left( f_j^{{{p['k']}}} - 1 \\right)$$

        For n = {n_fixes}: **Δτ_saved = {saved:.1f} s ({pct_saved:.1f}% of base Time Tax)**
        """)


# =========================================================================
# PAGE: ECONOMIC IMPACT
# =========================================================================
elif page == "Economic Impact":
    st.title("Economic Impact")
    st.markdown(
        "Annual aggregate Time Tax across **M = 100,000** daily commuters "
        "and **W = 250** working days, converted to economic value at the "
        "RBI informal wage rate (~₹50/hr)."
    )
    st.markdown("---")

    M = 100_000
    W = 250

    mean_tax_current = aggregate_time_tax(0)
    mean_tax_fixed = aggregate_time_tax(n_fixes)

    econ_current = economic_loss(mean_tax_current, M, W)
    econ_fixed = economic_loss(mean_tax_fixed, M, W)

    # Top-level metrics
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Annual person-minutes lost",
        f"{econ_current['annual_person_minutes']/1e6:.1f} M",
        help="M × W × mean Δτ / 60"
    )
    col2.metric(
        "Annual economic loss",
        f"₹{econ_current['annual_loss_crore']:.1f} Cr",
        help="Person-minutes × ₹50/hr wage rate"
    )
    col3.metric(
        f"Recovered by fixing top {n_fixes}",
        f"₹{(econ_current['annual_loss_crore'] - econ_fixed['annual_loss_crore']):.2f} Cr",
        delta=f"-{((econ_current['annual_loss_crore'] - econ_fixed['annual_loss_crore']) / econ_current['annual_loss_crore'] * 100):.1f}%",
        delta_color="normal",
    )

    st.markdown("---")

    # Per-persona breakdown table
    st.markdown("#### Per-Persona Time Tax & Annual Loss")
    rows = []
    for key, p in PERSONAS.items():
        r_curr = run_simulation(key, 0)
        r_fix = run_simulation(key, n_fixes)
        e_curr = economic_loss(r_curr["delta_tau"], M, W)
        e_fix = economic_loss(r_fix["delta_tau"], M, W)
        rows.append({
            "Persona": key,
            "Population weight": f"{p['weight']*100:.0f}%",
            "Δτ current (s)": f"{r_curr['delta_tau']:.0f}",
            "Δτ after fixes (s)": f"{r_fix['delta_tau']:.0f}",
            "Annual loss — current (₹ Cr)": f"{e_curr['annual_loss_crore']:.2f}",
            "Annual loss — fixed (₹ Cr)": f"{e_fix['annual_loss_crore']:.2f}",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.markdown("---")

    # Benefit-cost framing
    st.markdown("#### Lighthouse Pilot — Benefit-Cost Argument")
    fix_cost_lakh_low, fix_cost_lakh_high = 8, 12
    annual_recovered_crore = econ_current["annual_loss_crore"] - econ_fixed["annual_loss_crore"]
    annual_recovered_lakh = annual_recovered_crore * 100
    bcr_low = annual_recovered_lakh / fix_cost_lakh_high
    bcr_high = annual_recovered_lakh / fix_cost_lakh_low

    st.markdown(f"""
    Fixing the top **{n_fixes} hotspots** (drain covers, slab repair) is estimated at
    **₹{fix_cost_lakh_low}–{fix_cost_lakh_high} lakh** per the Lighthouse Pilot scope.

    Annual economic value recovered: **₹{annual_recovered_crore:.2f} Cr** (~₹{annual_recovered_lakh:.0f} lakh)

    **Benefit-to-cost ratio: {bcr_low:.1f}:1 – {bcr_high:.1f}:1**

    This framing is calibrated to BBMP project approval language, which requires
    both a cost estimate and a quantified beneficiary impact.
    """)

    st.markdown("---")

    # Aggregation formula display
    with st.expander("Show aggregation formulae"):
        st.markdown(f"""
        **Persona-weighted mean Time Tax** (seconds per trip):
        $$\\bar{{\\Delta\\tau}} = \\frac{{\\sum_{{\\phi \\in \\Phi}} w_\\phi \\cdot \\Delta\\tau(\\phi)}}
        {{\\sum_{{\\phi}} w_\\phi}} = {mean_tax_current:.1f} \\text{{ s (current)}}
        \\quad / \\quad {mean_tax_fixed:.1f} \\text{{ s (after {n_fixes} fixes)}}$$

        **Annual aggregate Time Tax:**
        $$\\mathcal{{T}}_{{year}} = M \\cdot W \\cdot \\bar{{\\Delta\\tau}}
        = {M:,} \\times {W} \\times {mean_tax_current:.1f}
        = {M * W * mean_tax_current / 60:,.0f} \\text{{ person-minutes}}$$

        **Economic value** at ₹50/hr:
        $$\\text{{Loss}} = \\mathcal{{T}}_{{year}} \\times \\frac{{50}}{{60}}
        = \\text{{₹}}{econ_current['annual_loss_rs']:,.0f}
        \\approx \\text{{₹}}{econ_current['annual_loss_crore']:.1f} \\text{{ Cr}}$$
        """)
