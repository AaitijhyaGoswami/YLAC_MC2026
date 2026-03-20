import streamlit as st

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
# MODULE IMPORTS
# -------------------------------------------------------------------------
modules = {}

try:
    from simulations import friction_mapper
    modules["Friction Mapper"] = friction_mapper
except ImportError:
    pass

try:
    from simulations import agent_sim
    modules["Time Tax Simulator"] = agent_sim
except ImportError:
    pass

try:
    from simulations import what_if
    modules["What-If: Lighthouse Pilot"] = what_if
except ImportError:
    pass

try:
    from simulations import economic_impact
    modules["Economic Impact"] = economic_impact
except ImportError:
    pass

# -------------------------------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------------------------------
st.sidebar.title("Escape the Knot")
st.sidebar.caption("Yeshwantpur Mobility Audit · YLAC 2026")

options = ["Home"] + list(modules.keys())
page = st.sidebar.radio("Navigate:", options)

st.sidebar.markdown("---")
st.sidebar.caption("Project Team:")
st.sidebar.info(
    "**Aaitijhya Goswami**\n*Simulation & Modelling*\n\n"
    "**Prajwal Kagalgomb**\n*Data & Advocacy*"
)

# -------------------------------------------------------------------------
# MAIN ROUTING
# -------------------------------------------------------------------------
if page == "Home":
    st.title("Escape the Knot")
    st.markdown("### Physics-Based Pedestrian Audit of the Yeshwantpur Mobility Knot")
    st.markdown("---")

    st.markdown("""
    #### Welcome

    This dashboard quantifies the **infrastructural tax** imposed on pedestrians at the
    Yeshwantpur intermodal hub in Bengaluru. By treating the city as a physical system —
    where broken drains, encroachments, and missing footpaths act as friction barriers —
    we compute the **Effective Path Length** and **Time Tax** for different commuter
    personas, and build a data-backed case for a
    [Tender S.U.R.E.](https://www.janausp.org/portfolio/tender-sure) Lighthouse Pilot.

    The survey covered the 900m Yeshwantpur–Constitution Circle corridor on March 7–8, 2026:
    **90.3%** of the stretch fails Active Mobility Bill standards and **96%** is fully
    inaccessible for wheelchair users.
    """)

    st.info("👈 **Select a module from the sidebar to begin exploring.**")

    st.markdown("## The Modules")
    st.markdown("---")

    # 1. Friction Mapper
    st.markdown("""
    ### **1. Friction Mapper**
    - **Abstract:** Models the surveyed route as a discretised friction field, assigning
      `f ∈ {1, 2, 3, 4, 5}` to each geotagged obstacle node based on the
      [Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en) rubric.
      The 600m Bazaar Street stretch is treated as a continuous `f = 5` block; the 300m
      Constitution Circle stretch has 24 discrete geotagged nodes. Rendered as an
      interactive Folium map with colour-coded pins and a route polyline overlay.
    - **Applications:**
        - Generating geotagged evidence maps for PIL filings on pedestrian rights.
        - Providing a quantitative baseline for Transit-Oriented Development planning.
        - Replicable audit template for other Indian mobility knots.
    - **Key output:** `L_eff = 4187.5 m` · `f̄ = 4.653` · Interactive Folium map
    """)

    # 2. Time Tax Simulator
    st.markdown("""
    ### **2. Time Tax Simulator**
    - **Abstract:** Computes traversal time and Time Tax for four commuter personas using
      a power-law friction-velocity model: `v_eff = v₀ / f^k`. The exponent `k(φ)` captures
      persona-specific friction sensitivity — a wheelchair user loses speed super-linearly
      compared to an able-bodied adult. Impassable nodes (`f > f_max`) trigger a vehicular
      ROW detour with penalty `α = 1.5`. The Time Tax `Δτ = T_actual − T_ideal` is
      displayed per persona alongside a per-segment traversal breakdown.
    - **Applications:**
        - Quantifying the disability-adjusted mobility cost of non-compliant infrastructure.
        - Providing per-persona Time Tax data for the DULT/BBMP policy brief.
        - Extending the framework to other Bengaluru intermodal hubs.
    - **Personas:** 🚶 Able-bodied adult · 👴 Elderly commuter · ♿ Wheelchair user · 🛵 Delivery partner
    """)

    # 3. What-If: Lighthouse Pilot
    st.markdown("""
    ### **3. What-If: Lighthouse Pilot**
    - **Abstract:** Interactive scenario explorer driven by the what-if formula:
      `Δτ_saved(n, φ) = (d/v₀) · Σⱼ (f_j^k − 1)`, where nodes are ranked by descending
      friction impact. The sidebar slider sets N — the number of top-ranked hotspots fixed
      to `f = 1` — and all charts update in real time. Shows the marginal Time Tax recovered
      with each additional repair, making the case that a small number of targeted fixes
      delivers outsized benefit.
    - **Applications:**
        - Identifying the minimum intervention set for maximum Time Tax reduction.
        - Framing the Lighthouse Pilot ask for DULT: fix N obstacles, recover X% of Time Tax.
        - Generating a prioritised repair schedule for BBMP field teams.
    - **Key insight:** Fixing the top 3 hotspots recovers ~38% of the total daily Time Tax.
    """)

    # 4. Economic Impact
    st.markdown("""
    ### **4. Economic Impact**
    - **Abstract:** Aggregates the persona-weighted Time Tax across `M = 100,000` daily
      commuters and `W = 250` working days: `𝒯_year = M · W · Δτ̄(φ)`. Converts to
      economic value at the RBI informal wage rate (~₹50/hr). Reports annual person-minutes
      lost, monetary loss in crore, and a benefit-to-cost ratio for the Lighthouse Pilot
      intervention.
    - **Applications:**
        - Anchoring the DULT/BBMP submission with a concrete economic argument.
        - Demonstrating that fixing top-N hotspots yields a 10:1+ benefit-to-cost ratio.
        - Framing the ask in the language BBMP project approvals require.
    - **Key output:** ~₹14.2 crore annual productivity loss from the 900m stretch alone.
    """)

    st.markdown("---")
    st.caption(
        "Built for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "[DULT Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en)"
    )

else:
    if page in modules:
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
