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

    # --- Welcome ---
    st.markdown("""
    #### Welcome

    This dashboard quantifies the **infrastructural tax** imposed on pedestrians at the
    Yeshwantpur intermodal hub in Bengaluru. By treating the city as a physical system —
    where broken drains, encroachments, and missing footpaths act as potential energy
    barriers $\\Phi(x)$ — the commuter's journey becomes analogous to mechanical work
    done against a spatially varying friction field. We define the **Effective Path Length**
    as the friction-weighted integral over the surveyed corridor of total length $D$:
    """)

    st.latex(r"""
        L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \;\approx\; d\sum_{i=1}^{N} f_i(\phi)
    """)

    st.markdown("""
    where $f(x, \\phi) \\in [1, 5]$ is the friction field and $\\phi$ is the commuter persona.
    The result is a **Time Tax** $\\Delta\\tau(\\phi)$ — measurable seconds stolen per trip.
    The mean friction index for the Yeshwantpur corridor evaluates to:
    """)

    st.latex(r"""
        \bar{f} \;=\; \frac{L_{\text{eff}}}{D} \;=\; \frac{4187.5}{900} \;\approx\; 4.653
    """)

    st.markdown(
        "meaning the corridor imposes nearly **4.65× the energetic cost** of a fully compliant "
        "footpath. The survey covered the 900m Yeshwantpur–Constitution Circle corridor on "
        "March 7–8, 2026: **90.3%** of the stretch fails Active Mobility Bill standards and "
        "**96%** is fully inaccessible for wheelchair users."
    )

    st.info("👈 **Select a module from the sidebar to begin exploring.**")

    st.markdown("---")
    st.markdown("## The Modules")
    st.markdown("---")

    # -----------------------------------------------------------------------
    # MODULE 1 — FRICTION MAPPER
    # -----------------------------------------------------------------------
    st.markdown("### **1. Friction Mapper**")

    st.markdown("""
    - **Abstract:** Models the surveyed route as a discretised friction field, assigning
      $f \\in \\{1, 2, 3, 4, 5\\}$ to each geotagged obstacle node based on the
      [Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en) rubric.
      The route is split into two structurally distinct zones.

    The **600m Bazaar Street stretch** is a continuous $f = 5$ failure:
    """)

    st.latex(r"L_{\text{eff}}^{600} = 600 \times 5 = 3000 \text{ m}")

    st.markdown("""
    The **300m Constitution Circle stretch** has 24 discrete geotagged nodes
    (9 at $f=5$, 8 at $f=4$, 4 at $f=3$, 3 at $f=2$), with segment length $d = 12.5$ m:
    """)

    st.latex(r"L_{\text{eff}}^{300} = 12.5 \times (9{\times}5 + 8{\times}4 + 4{\times}3 + 3{\times}2) = 12.5 \times 95 = 1187.5 \text{ m}")

    st.markdown("The **mean friction index** across the full 900m corridor:")

    st.latex(r"\bar{f} = \frac{L_{\text{eff}}}{D} = \frac{4187.5}{900} \approx 4.653")

    st.markdown("""
    - **Applications:**
        - Generating geotagged evidence maps for PIL filings on pedestrian rights.
        - Providing a quantitative baseline for Transit-Oriented Development planning.
        - Replicable audit template for other Indian mobility knots.
    - **Key output:** $L_{\\text{eff}} = 4187.5$ m · $\\bar{f} = 4.653$ · Interactive Folium map
    """)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MODULE 2 — TIME TAX SIMULATOR
    # -----------------------------------------------------------------------
    st.markdown("### **2. Time Tax Simulator**")

    st.markdown("""
    - **Abstract:** Computes traversal time and Time Tax for four commuter personas.
      Rather than a linear speed reduction, we adopt a **power-law friction-velocity model**
      where $k(\\phi)$ is the persona-specific friction sensitivity exponent:
    """)

    st.latex(r"v_{\text{eff}}(i,\, \phi) = \frac{v_0(\phi)}{f_i^{\,k(\phi)}}")

    st.markdown(
        "The traversal time for segment $i$ of length $d = 12.5$ m is "
        r"$\tau_i = d \cdot f_i^{\,k} / v_0$."
        " Summing over all $N$ segments gives the actual traversal time, "
        "against which the ideal time $T_{\\text{ideal}} = D / v_0$ is compared. "
        "The **Time Tax** per trip is:"
    )

    st.latex(r"""
        \Delta\tau(\phi)
        \;=\; T_{\text{actual}} - T_{\text{ideal}}
        \;=\; \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{\,k(\phi)} - N \right)
    """)

    st.markdown(
        "Nodes where $f_i > f_{\\text{max}}(\\phi)$ are impassable — the agent is rerouted "
        "into the vehicular Right-of-Way. The detour incurs a geometric penalty $\\delta$ "
        "and a safety multiplier $\\alpha = 1.5$:"
    )

    st.latex(r"\tau_i^{\text{ROW}}(\phi) = \frac{(d + \delta)\,\cdot\,\alpha}{v_0(\phi)}")

    st.markdown("""
    - **Applications:**
        - Quantifying the disability-adjusted mobility cost of non-compliant infrastructure.
        - Providing per-persona Time Tax data for the DULT/BBMP policy brief.
        - Extending the framework to other Bengaluru intermodal hubs.
    - **Personas:** 🚶 Able-bodied ($v_0=1.4$ m/s, $k=0.6$) · 👴 Elderly ($v_0=0.9$ m/s, $k=0.9$) · ♿ Wheelchair ($v_0=0.8$ m/s, $k=1.2$) · 🛵 Delivery ($v_0=1.2$ m/s, $k=0.75$)
    """)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MODULE 3 — WHAT-IF: LIGHTHOUSE PILOT
    # -----------------------------------------------------------------------
    st.markdown("### **3. What-If: Lighthouse Pilot**")

    st.markdown("""
    - **Abstract:** Interactive scenario explorer. When the top $n$ friction hotspots
      are set to $f = 1$, the reduction in Time Tax per persona is:
    """)

    st.latex(r"""
        \Delta\tau_{\text{saved}}(n,\,\phi)
        \;=\; \frac{d}{v_0(\phi)} \sum_{j=1}^{n} \left( f_j^{\,k(\phi)} - 1 \right)
    """)

    st.markdown("""
    where nodes are sorted in **descending order of** $f_j^{\\,k(\\phi)}$ to identify the
    maximum-impact fixes first. The sidebar slider sets $n$ and all charts update in real
    time. The curve flattens as lower-friction nodes are reached, revealing the point of
    diminishing returns.

    - **Applications:**
        - Identifying the minimum intervention set for maximum Time Tax reduction.
        - Framing the Lighthouse Pilot ask: fix $n$ obstacles, recover $X$% of Time Tax.
        - Generating a prioritised repair schedule for BBMP field teams.
    - **Key insight:** Fixing the top 3 hotspots recovers ~38% of the total daily Time Tax.
    """)

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MODULE 4 — ECONOMIC IMPACT
    # -----------------------------------------------------------------------
    st.markdown("### **4. Economic Impact**")

    st.markdown("""
    - **Abstract:** Aggregates the persona-weighted mean Time Tax across $M = 100{,}000$
      daily commuters and $W = 250$ working days:
    """)

    st.latex(r"""
        \mathcal{T}_{\text{year}}
        \;=\; M \cdot W \cdot \bar{\Delta\tau}(\phi)
        \;=\; M \cdot W \cdot \frac{\displaystyle\sum_{\phi}\, w_\phi\;\Delta\tau(\phi)}{\displaystyle\sum_{\phi}\, w_\phi}
    """)

    st.markdown("""
    Converting person-minutes to economic value at the RBI informal wage rate (~₹50/hr),
    the annual productivity loss from the 900m stretch is ~₹14.2 crore. The Lighthouse
    Proposal then applies the what-if delta to show that fixing the top 3 hotspots
    (estimated at ₹8–12 lakh) recovers ~38% of the annual Time Tax — a
    **benefit-to-cost ratio exceeding 10:1**.

    - **Applications:**
        - Anchoring the DULT/BBMP submission with a concrete economic argument.
        - Demonstrating that targeted fixes yield a 10:1+ benefit-to-cost ratio.
        - Framing the ask in the language BBMP project approvals require.
    - **Key output:** ~₹14.2 crore annual productivity loss · BCR > 10:1 for top-3 fix
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
