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
import copy
import yaml
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import osmnx as ox
    import networkx as nx
    HAVE_OSM = True
except ImportError:
    HAVE_OSM = False

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

MAP_CENTRE      = [13.0215, 77.5555]
STATION_EXIT    = (13.02383, 77.55187)
CONSTITUTION_CL = (13.02007, 77.55546)

PERSONA_COLORS = {
    "able_bodied": "#2196F3",
    "elderly":     "#FF9800",
    "wheelchair":  "#9C27B0",
    "delivery":    "#F44336",
}
PERSONA_LABELS = {
    "able_bodied": "Able-bodied Adult",
    "elderly":     "Elderly Commuter",
    "wheelchair":  "Wheelchair User",
    "delivery":    "Delivery Partner",
}

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
# LAYER 1: OSMnx NETWORK ROUTING
# -------------------------------------------------------------------------

@st.cache_data(show_spinner="Downloading pedestrian street graph…")
def load_osm_graph():
    centre = (
        (STATION_EXIT[0] + CONSTITUTION_CL[0]) / 2,
        (STATION_EXIT[1] + CONSTITUTION_CL[1]) / 2,
    )
    return ox.graph_from_point(centre, dist=650, network_type="walk", retain_all=True)


def build_friction_graph(G, audit_df: pd.DataFrame, bazaar_f: int):
    import copy
    G         = copy.deepcopy(G)   # work on a copy so the cached raw graph stays clean
    audit_pts = audit_df[["lat", "lon", "f_value"]].values

    def nearest_f(mid_lat, mid_lon):
        dlat = np.radians(audit_pts[:, 0] - mid_lat)
        dlon = np.radians(audit_pts[:, 1] - mid_lon)
        a = (np.sin(dlat / 2) ** 2
             + np.cos(np.radians(mid_lat))
             * np.cos(np.radians(audit_pts[:, 0]))
             * np.sin(dlon / 2) ** 2)
        dist = 6371000 * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return int(audit_pts[np.argmin(dist), 2])

    for u, v, k, data in G.edges(keys=True, data=True):
        nu, nv  = G.nodes[u], G.nodes[v]
        mid_lat = (nu["y"] + nv["y"]) / 2
        mid_lon = (nu["x"] + nv["x"]) / 2
        f       = nearest_f(mid_lat, mid_lon)
        G[u][v][k]["f_value"] = f
    return G


def persona_edge_cost(G, persona: dict, bazaar_f: int):
    v0    = persona["v0"]
    k     = persona["k"]
    f_max = persona["f_max"]
    alpha = persona["alpha"]
    delta = persona["delta"]

    for u, v, kk, data in G.edges(keys=True, data=True):
        length = data.get("length", 10.0)
        f      = data.get("f_value", bazaar_f)
        if f > f_max:
            cost = ((length + delta) * alpha) / v0
        else:
            cost = length * (f ** k) / v0
        G[u][v][kk]["persona_cost"] = cost
    return G


def compute_route(G, origin, dest, weight):
    o = ox.distance.nearest_nodes(G, origin[1], origin[0])
    d = ox.distance.nearest_nodes(G, dest[1],   dest[0])
    try:
        path = nx.shortest_path(G, o, d, weight=weight)
        cost = nx.shortest_path_length(G, o, d, weight=weight)
        return path, cost
    except nx.NetworkXNoPath:
        return None, None


def path_to_coords(G, path):
    return [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]


# MAP BUILDER
def build_map(df: pd.DataFrame, n_fixes: int = 0, bazaar_f: int = 5,
              route_coords=None, route_color="#4CAF50",
              route_popup_html: str = "") -> folium.Map:
    m = folium.Map(location=MAP_CENTRE, zoom_start=15, tiles="CartoDB dark_matter")

    b_popup_html = f"""
        <div style="font-family: sans-serif; font-size: 12px; width: 200px; background: #111; color: #eee; border-radius: 4px; padding: 8px;">
            <b style="color: #F44336; font-size: 13px;">Bazaar Street Zone</b><br>
            <span style="font-size: 10px; color: #aaa;">600m continuous failure stretch</span>
            <hr style="margin: 5px 0; border-color: #333;">
            <b>Type:</b> Systemic Failure Area<br>
            <b>Modelled f:</b> {bazaar_f}<br>
            <hr style="margin: 5px 0; border-color: #333;">
            <span style="font-size: 10px; color: #777;">Footway fully colonised. Pedestrians enter vehicular ROW.</span>
        </div>
    """
    
    folium.PolyLine(
        locations=ROUTE_600M,
        color=F_COLORS.get(bazaar_f, F_COLORS[5]),
        weight=6, 
        opacity=0.85,
        tooltip="Bazaar St: Click for Data",
        popup=folium.Popup(b_popup_html, max_width=250)
    ).add_to(m)

    f_values = df["f_value"].values.astype(float)
    fix_indices = set(df.index[np.argsort(f_values)[::-1][:n_fixes]]) if n_fixes > 0 else set()

    for idx, row in df.iterrows():
        is_fixed = idx in fix_indices
        f = int(row["f_value"])
        color = F_COLORS[1] if is_fixed else F_COLORS.get(f, F_COLORS[5])
        status = "REMEDIATED" if is_fixed else F_SHORT.get(f)
        
        n_popup_html = f"""
            <div style="font-family: sans-serif; font-size: 12px; width: 200px; background: #111; color: #eee; border-radius: 4px; padding: 8px;">
                <b style="color: {color}; font-size: 13px;">Node ID: {int(row['id'])}</b><br>
                <span style="font-size: 10px; color: #aaa;">{F_SHORT.get(f, "Unknown")}</span>
                <hr style="margin: 5px 0; border-color: #333;">
                <b>Friction:</b> f={f}<br>
                <b>Status:</b> {status}<br>
                <b>GPS:</b> {row['lat']:.5f}, {row['lon']:.5f}<br>
                <hr style="margin: 5px 0; border-color: #333;">
                <span style="font-size: 10px; color: #777;">Potential energy barrier identified via physical audit.</span>
            </div>
        """

        folium.CircleMarker(
            location=(row["lat"], row["lon"]), 
            radius=9, 
            color="white", 
            weight=1, 
            fill=True, 
            fill_color=color, 
            fill_opacity=0.95,
            tooltip=f"Node {int(row['id'])} · f={f}",
            popup=folium.Popup(n_popup_html, max_width=300)
        ).add_to(m)

    if route_coords:
        _route_popup = folium.Popup(route_popup_html, max_width=300) if route_popup_html else None
        _pl = folium.PolyLine(
            route_coords,
            color=route_color,
            weight=4,
            opacity=0.9,
            tooltip="OSM Route: Click for Persona Breakdown"
        )
        if _route_popup:
            _pl.add_child(_route_popup)
        _pl.add_to(m)
        folium.Marker(
            STATION_EXIT,
            tooltip="Yeshwantpur Railway Station exit",
            icon=folium.Icon(color="green", icon="train", prefix="fa")
        ).add_to(m)
        folium.Marker(
            CONSTITUTION_CL,
            tooltip="Constitution Circle / Metro entry",
            icon=folium.Icon(color="blue", icon="subway", prefix="fa")
        ).add_to(m)

    return m


# -------------------------------------------------------------------------
# VISUALIZATION FUNCTIONS
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
    ax.set_xlim(0, 900)
    ax.set_ylim(0, 5.7)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_facecolor("#1a1a1a")
    fig.patch.set_facecolor("#1a1a1a")
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    fig.tight_layout()
    return fig

def plot_severity_pie(df: pd.DataFrame, n_fixes: int = 0) -> plt.Figure:
    f_vals = df["f_value"].values.astype(float).copy()
    if n_fixes > 0:
        f_vals[np.argsort(f_vals)[::-1][:n_fixes]] = 1.0
    counts = {f: int((f_vals == f).sum()) for f in [1, 2, 3, 4, 5]}
    present = {f: c for f, c in counts.items() if c > 0}
    sizes, labels, colors = list(present.values()), [F_SHORT[f] for f in present.keys()], [F_COLORS[f] for f in present.keys()]
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor("#1a1a1a")
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.0f%%', startangle=90, textprops={'color':"white", 'fontsize': 8}, counterclock=False)
    ax.set_title("Obstacle Severity Breakdown (300m)", color="white", fontsize=10)
    fig.tight_layout()
    return fig

def plot_leff_comparison(L_eff_base: float, L_eff_now: float, f_bar_base: float, f_bar_now: float, n_fixes: int, bazaar_f: int) -> plt.Figure:
    scenarios = [("Surveyed Baseline", L_eff_base, f_bar_base), ("Modified Scenario", L_eff_now,  f_bar_now), ("S.U.R.E. Target", 900.0, 1.0)]
    fig, ax = plt.subplots(figsize=(8, 2.8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#1a1a1a")
    bar_h = 0.38
    max_leff = max(L_eff_base, L_eff_now)
    for i, (label, leff, fbar) in enumerate(scenarios):
        ax.barh(i, 900, height=bar_h, color="#4CAF50", alpha=0.85, left=0)
        excess = leff - 900
        if excess > 0:
            ax.barh(i, excess, height=bar_h, color="#F44336", alpha=0.85, left=900)
        ax.text(leff + (max_leff * 0.05), i, f"f̄ = {fbar:.3f}", va="center", ha="left", fontsize=8.5, color="white", fontweight="bold")
        ax.text(leff / 2, i, f"L_eff = {leff:.0f}m", va="center", ha="center", fontsize=8, color="white", fontweight="bold")
    ax.axvline(900, color="#4CAF50", linewidth=1.5, linestyle="--", alpha=0.7)
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels([s[0] for s in scenarios], fontsize=8.5, color="white")
    ax.set_xlim(0, max_leff * 1.3)
    ax.tick_params(colors="white", labelsize=8)
    ax.spines[:].set_visible(False)
    ax.set_title("Effective Path Length Comparison", color="white", fontsize=10)
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
        ax.axvline(f, color="#555", linewidth=0.8, ymin=0.1, ymax=0.9)
        ax.text(f, -0.38, str(f), ha="center", fontsize=7.5, color="#aaaaaa")
    ax.axvline(f_bar_now, color="white", linewidth=2.0)
    ax.text(f_bar_now, 0.32, f" f̄ = {f_bar_now:.3f}", va="bottom", ha="left" if f_bar_now < 4 else "right", fontsize=9, color="white", fontweight="bold")
    ax.text(1.0, 0.32, "S.U.R.E. →", va="bottom", ha="left", fontsize=7, color="#4CAF50")
    ax.set_xlim(0.8, 5.4)
    ax.set_ylim(-0.5, 0.6)
    ax.axis("off")
    fig.tight_layout(pad=0.3)
    return fig


# -------------------------------------------------------------------------
# MAIN APP ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.markdown("""
    The **Friction Mapper** module represents a paradigm shift in urban auditing, from subjective complaints to a rigorous physics-based diagnostic of the 900m Yeshwantpur corridor. This module systematically geotags and measures infrastructure failures, from broken pavements and open drains to systemic encroachments, to provide a discrete **Friction Index (f)** for the urban environment. The pedestrian journey is considered as a traversal through a resistive field, enabling accurate modeling of the **Time Tax** and physical energy expenditure imposed on commuters due to design neglect.

    And for city officials and policy makers, this data enables infrastructure maintenance to be a strategic investment rather than a reactive cost. The module models the effects of particular remediation efforts and shows how targeted repairs directly lower urban resistance, recover lost economic productivity, and meet universal accessibility standards. The methodology offers a scalable blueprint for auditing high-intensity transit hubs across the city, ensuring the right to a seamless, dignified commute is rooted in hard evidence and predictive engineering.
    """)

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
            "Footpath ends: transformer, encroachment, construction",
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
    st.dataframe(rubric, hide_index=True, width='stretch')

    # --- TECHNICAL MATH SECTION ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Fundamental Equations")
        st.markdown("Corridor quality is defined by the **Mean Friction Index**, representing the average struggle factor across the total surveyed distance.")
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

        st.markdown("#### Detailed Baseline Calculation")
        st.markdown("""
        To arrive at the baseline difficulty multiplier of **4.653**, we aggregate the audit data from two structurally 
        distinct zones of the Yeshwantpur corridor.
        """)
        
        st.markdown("**The 300m Constitution Circle Zone**")
        st.markdown("This stretch contains 24 discrete geotagged nodes. The sum of friction values is as follows:")
        st.latex(r"\sum f_i = (9 \times f_5) + (8 \times f_4) + (4 \times f_3) + (3 \times f_2) = 45 + 32 + 12 + 6 = 95")
        st.latex(r"L_{\text{eff}}^{300} = 95 \times 12.5\text{m} = 1187.5\text{m}")

        st.markdown("**The 600m Bazaar Street Zone**")
        st.markdown("This stretch is modeled as a continuous systemic failure ($f=5$) as audited in March 2026.")
        st.latex(r"L_{\text{eff}}^{600} = 600\text{m} \times 5 = 3000\text{m}")

        st.markdown("**Final Aggregation**")
        st.markdown("Combining both zones yields the total effective effort distance and the mean index.")
        st.latex(r"L_{\text{eff}}^{Total} = 1187.5\text{m} + 3000\text{m} = 4187.5\text{m}")
        st.latex(r"\bar{f} = \frac{4187.5}{900} \approx 4.653")

        if HAVE_OSM:
            st.markdown("#### Layer 1: Friction-Weighted Network Routing")
            st.markdown("""
Each OSM edge is tagged with the f-value of the nearest audit node.
The traversal cost on each edge uses the same power-law model as the Time Tax Simulator,
so routing costs are directly comparable to the per-segment times shown in the agent-based simulation.
            """)
            st.markdown("**Edge traversal time (seconds):**")
            st.latex(r"""
\tau_e(\phi) =
\begin{cases}
\dfrac{\text{length}(e) \cdot f_e^{\,k(\phi)}}{v_0(\phi)} & f_e \leq f_{\max}(\phi) \\[10pt]
\dfrac{\bigl(\text{length}(e) + \delta(\phi)\bigr) \cdot \alpha}{v_0(\phi)} & f_e > f_{\max}(\phi)
\end{cases}
            """)
            st.latex(r"""
\begin{aligned}
\text{length}(e) &: \text{Physical length of OSM edge } e \text{ (metres)} \\
f_e &: \text{f-value of nearest audit node to edge midpoint} \\
k(\phi) &: \text{Friction sensitivity exponent for persona } \phi \\
v_0(\phi) &: \text{Free-walking speed of persona } \phi \text{ (m/s)} \\
f_{\max}(\phi) &: \text{Impassability threshold (above this, ROW detour is triggered)} \\
\delta(\phi) &: \text{Detour distance penalty for persona } \phi \text{ (metres)} \\
\alpha &: \text{Safety speed penalty multiplier in vehicular ROW} = 1.5
\end{aligned}
            """)
            st.markdown("**Total route cost for persona** $\\phi$:")
            st.latex(r"T_{\text{route}}(\phi) = \sum_{e \in \text{path}} \tau_e(\phi)")
            st.markdown("**Why all personas follow the same geometric path:**")
            st.markdown("""
Dijkstra's algorithm minimises $T_{\\text{route}}(\\phi)$ over the real OSM graph.
The Yeshwantpur–Bazaar Street corridor has no bypass street shorter than the
break-even threshold below, so the optimal path is topologically identical for
all personas; only the cost of traversing it differs.
            """)
            st.markdown("**Bypass break-even threshold**: a bypass at $f=2$ only beats the main corridor at $f=5$ if:")
            st.latex(r"\text{length}_{\text{bypass}} < \frac{v_0(\phi) \cdot \tau_{\text{main}}}{2^{k(\phi)}}")
            st.markdown("Per persona, for a 120 m main-corridor segment:")

            _bp_data = {
                "Able-bodied": (1.4, 0.60, 4, 8.0),
                "Elderly":     (0.9, 0.90, 3, 10.0),
                "Wheelchair":  (0.8, 1.20, 3, 15.0),
                "Delivery":    (1.2, 0.75, 4, 8.0),
            }
            import pandas as _pd, numpy as _np
            _rows = []
            for _name, (_v0, _k, _fmax, _delta) in _bp_data.items():
                _alpha = 1.5
                _length = 120.0
                if 5 > _fmax:
                    _main = ((_length + _delta) * _alpha) / _v0
                else:
                    _main = _length * (5 ** _k) / _v0
                _breakeven = _main * _v0 / (2 ** _k)
                _rows.append({"Persona": _name, "Main cost at f=5 (s)": round(_main, 1),
                               "Bypass wins if shorter than (m)": round(_breakeven, 1)})
            st.dataframe(_pd.DataFrame(_rows), hide_index=True, width='stretch')

    try:
        df = load_audit_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    # --- SIDEBAR CONTROLS ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Friction Mapper Controls")
    n_fixes = st.sidebar.slider("Nodes brought to Tender S.U.R.E. standard (f=1):", 0, len(df), 0,
                               help="Simulates the fixing of each of the obstacles which make the footways most inaccessible")
    
    st.sidebar.markdown("**600m Bazaar Street stretch**")
    sure_standards = {
        "Current — f=5 (Systemic Failure)": 5,
        "Serious barrier — f=4 (Physical Barrier)": 4,
        "Moderate repair — f=3 (Obstacle Course)": 3,
        "Minor repair — f=2 (Distracted Walk)": 2,
        "Full S.U.R.E. compliance — f=1": 1,
    }
    bazaar_label = st.sidebar.selectbox("Model Bazaar Street as:", list(sure_standards.keys()),
                                       help="Simulates gradual fixing of the Bazaar Street stretch by authorities")
    bazaar_f = sure_standards[bazaar_label]

    # Layer 1 sidebar controls (only shown when OSMnx is installed)
    show_route   = False
    route_coords = None
    route_color  = "#4CAF50"
    if HAVE_OSM:
        st.sidebar.markdown("### Network Routing")
        show_route = st.sidebar.checkbox(
            "Show friction-optimal route",
            value=False,
            help="Downloads the real OSM pedestrian graph and overlays the friction-weighted shortest path. Requires internet connection."
        )
        if show_route:
            route_persona = st.sidebar.selectbox(
                "Route colour — persona:",
                options=list(PERSONA_LABELS.keys()),
                format_func=lambda k: PERSONA_LABELS[k]
            )
            route_color = PERSONA_COLORS[route_persona]

    # --- COMPUTATION ---
    f_300 = df["f_value"].values.astype(float)
    f_fixed = f_300.copy()
    if n_fixes > 0: f_fixed[np.argsort(f_fixed)[::-1][:n_fixes]] = 1.0

    L_eff_300_base = 12.5 * f_300.sum()
    L_eff_now = (12.5 * f_fixed.sum()) + (600 * bazaar_f)
    L_eff_base = L_eff_300_base + (600 * 5)
    f_bar_base, f_bar_now = L_eff_base / 900, L_eff_now / 900

    # Layer 1: compute route + per-persona popup if requested
    route_popup_html = ""
    if show_route and HAVE_OSM:
        try:
            with st.spinner("Building friction-weighted street graph…"):
                G_raw     = load_osm_graph()
                _personas = yaml.safe_load(open(os.path.join("data", "personas.yaml")))
                _p        = _personas.get(route_persona, list(_personas.values())[0])
                G_tagged  = build_friction_graph(G_raw, df, bazaar_f)

                # Route on selected persona
                G_costed  = persona_edge_cost(G_tagged, _p, bazaar_f)
                path, _   = compute_route(G_costed, STATION_EXIT, CONSTITUTION_CL, weight="persona_cost")
                if path:
                    route_coords = path_to_coords(G_costed, path)

                    # Compute cost for ALL personas so popup shows full comparison
                    _rows = ""
                    for _pk, _pp in _personas.items():
                        _Gc = persona_edge_cost(copy.deepcopy(G_tagged), _pp, bazaar_f)
                        _, _cost_s = compute_route(_Gc, STATION_EXIT, CONSTITUTION_CL, weight="persona_cost")
                        _cost_s = _cost_s if _cost_s else 0
                        _ideal_s = sum(
                            d.get("length", 10.0) / _pp["v0"]
                            for _, _, d in _Gc.edges(data=True)
                            if d.get("f_value", 3) == 1
                        )
                        # ideal = straight corridor at f=1
                        _ideal_s = 900.0 / _pp["v0"]
                        _cost_s  = _cost_s if _cost_s is not None else _ideal_s
                        _tax_s   = max(0.0, _cost_s - _ideal_s)
                        # Count impassable edges along the routed path
                        _path_p, _ = compute_route(_Gc, STATION_EXIT, CONSTITUTION_CL, weight="persona_cost")
                        _detours = sum(
                            1 for u, v in zip((_path_p or []), (_path_p or [])[1:])
                            if _Gc[u][v][0].get("f_value", 3) > _pp["f_max"]
                        )
                        _is_sel  = _pk == route_persona
                        _bold    = "font-weight:bold; background:#1a1a2e;" if _is_sel else ""
                        _rows += (
                            f'<tr style="{_bold}">' +
                            f'<td style="padding:3px 8px; color:{PERSONA_COLORS.get(_pk,"#fff")}">{_pp["label"]}</td>' +
                            f'<td style="padding:3px 8px; text-align:right">{_cost_s/60:.1f} min</td>' +
                            f'<td style="padding:3px 8px; text-align:right; color:#F44336">+{_tax_s/60:.1f} min</td>' +
                            f'<td style="padding:3px 8px; text-align:right; color:#FF9800">{_detours}</td>' +
                            "</tr>"
                        )

                    route_popup_html = (
                        '<div style="font-family:sans-serif;font-size:12px;width:260px;background:#111;color:#eee;border-radius:4px;padding:8px;">' +
                        '<b style="color:#4CAF50;font-size:13px;">OSM Pedestrian Route</b><br>' +
                        '<span style="color:#aaa;font-size:10px">Station Exit → Constitution Circle · 900m corridor</span>' +
                        '<hr style="margin:6px 0;border-color:#333">' +
                        '<b style="font-size:11px;color:#aaa">Per-Persona Traversal Cost</b>' +
                        '<table style="width:100%;border-collapse:collapse;margin-top:4px">' +
                        '<tr style="color:#777;font-size:10px">' +
                        '<th style="text-align:left;padding:2px 8px">Persona</th>' +
                        '<th style="text-align:right;padding:2px 8px">Time</th>' +
                        '<th style="text-align:right;padding:2px 8px">Time Tax</th>' +
                        '<th style="text-align:right;padding:2px 8px">Detours</th>' +
                        '</tr>' +
                        _rows +
                        '</table>' +
                        '<hr style="margin:6px 0;border-color:#333">' +
                        '<span style="font-size:9px;color:#777">Highlighted = selected persona · Detours = ROW segments forced by impassable nodes</span>' +
                        '</div>'
                    )
                else:
                    st.warning("No routable path found in the OSM graph for this corridor.")
        except Exception as e:
            st.warning(f"Could not load OSM graph: {e}. Check your internet connection.")

    # --- HEADLINE METRICS ---
    st.markdown("---")
    
    st.markdown("#### The State of the Corridor")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fails Active Mobility Bill", "90.3%",
                help="90.3% of the 900m stretch does not meet minimum pedestrian standards.")
    col2.metric("Wheelchair inaccessible", "96.0%",
                help="96% of the route has $f > f_{max}$ for wheelchair users ($f_{max} = 3$).")
    col3.metric("Impassable Nodes ($f ≥ 4$)", f"{int((f_fixed > 3).sum())} / 24",
               help="Nodes rated f=4 or f=5 force pedestrians into vehicular Right-of-Way.")
    col4.metric("Difficulty Multiplier", f"{f_bar_now:.2f}x",
               help=f"The corridor makes a 900m walk feel like {f_bar_now:.2f}× that distance.")

    if show_route and route_coords:
        st.markdown("#### Per-Persona Route Cost")
        if show_route and HAVE_OSM:
            try:
                _personas_disp = yaml.safe_load(open(os.path.join("data", "personas.yaml")))
                _Gbase = build_friction_graph(load_osm_graph(), df, bazaar_f)
                _pcols = st.columns(len(_personas_disp))
                for _col, (_pk, _pp) in zip(_pcols, _personas_disp.items()):
                    _Gc2  = persona_edge_cost(copy.deepcopy(_Gbase), _pp, bazaar_f)
                    _, _c = compute_route(_Gc2, STATION_EXIT, CONSTITUTION_CL, weight="persona_cost")
                    _ideal = 900.0 / _pp["v0"]
                    _tax   = max(0.0, (_c or 0) - _ideal)
                    _col.metric(
                        _pp["label"],
                        f"{(_c or 0)/60:.1f} min",
                        delta=f"+{_tax/60:.1f} min tax",
                        delta_color="inverse"
                    )
            except Exception:
                pass

    # --- MAP & GRADIENT ---
    st_folium(build_map(df, n_fixes, bazaar_f, route_coords, route_color, route_popup_html), width=None, height=520, returned_objects=[])
    st.markdown("#### Friction Gradient: Full 900m Route")
    st.pyplot(plot_friction_bar(df, n_fixes, bazaar_f), width='stretch')
    st.markdown("---")

    # --- CORRIDOR ANALYSIS ---
    st.markdown("#### Corridor Analysis")
    col_left, col_right = st.columns(2)
    with col_left:
        st.pyplot(plot_severity_pie(df, n_fixes), width='stretch')
    with col_right:
        st.caption("S.U.R.E. Compliance Gauge")
        st.pyplot(plot_sure_compliance_bar(f_bar_now), width='stretch')
        st.pyplot(plot_leff_comparison(L_eff_base, L_eff_now, f_bar_base, f_bar_now, n_fixes, bazaar_f), width='stretch')

    # --- POINTWISE DESCRIPTION ---
    st.markdown("---")
    st.header("Mapper Functionality")
    st.write("* **Spatial Evidence Mapping:** Every marker on the interactive map corresponds to a physical infrastructure failure recorded and geotagged during the field audit. This converts anecdotal walking frustrations into a precise, coordinate-based database.")
    st.write("* **Standardized Severity Coding:** The color-coded logic is directly aligned with the Active Mobility Bill and DULT rubrics. By assigning a Friction Value $f$, the mapper provides an objective diagnostic of segment compliance.")
    st.write("* **Dynamic Remediation Simulation:** The interface acts as a predictive tool. By adjusting the sidebar controls, users can simulate the 'repair' of specific hotspots to observe the real-time drop in the Mean Friction Index.")
    st.write("* **Strategic Policy Framework:** This module provides the high-fidelity technical baseline required for government project approval. It serves as the primary data used to justify the fiscal investment for Lighthouse Pilot repairs.")
    if HAVE_OSM:
        st.write("* **Friction-Optimal Routing (Layer 1):** Overlays the real OSM pedestrian graph and computes the path minimising total friction cost — making visible exactly where infrastructure forces sub-optimal detours.")

if __name__ == "__main__":
    app()
