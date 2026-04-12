import streamlit as st

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Escape the Knot",
    page_icon="🚶",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MODULE IMPORTS
modules = {}

try:
    from simulation import friction_mapper
    modules["Friction Mapper"] = friction_mapper
except ImportError:
    pass

try:
    from simulation import agent_sim
    modules["Time Tax Simulator"] = agent_sim
except Exception as e:
    st.sidebar.error(f"agent_sim failed: {e}")

try:
    from simulation import what_if
    modules["What-If: Lighthouse Pilot"] = what_if
except ImportError:
    pass

try:
    from simulation import policy_brief
    modules["Economic Impact"] = policy_brief
except ImportError:
    pass


# SIDEBAR NAVIGATION
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


# MAIN ROUTING
if page == "Home":
    st.title("Escape the Knot")
    st.markdown("### Quantifying the Infrastructural Tax on Pedestrian Mobility")
    st.markdown("""
    This audit treats the urban environment as a physical system where infrastructure failures act as 
    resistive forces. By measuring these forces, we quantify the 'Time Tax' imposed on the citizens 
    of Yeshwantpur.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("The Scale")
        st.write("**Corridor:** 900m (Yeshwantpur–Constitution Circle)")
        st.write("**Traffic:** 100,000+ Daily Commuters")
        st.write("**Condition:** 90.3% fails Active Mobility standards")

    with col2:
        st.subheader("The Impact")
        st.write("**Effort:** 4.65x higher than standard paths")
        st.write("**Time Lost:** 170 Million minutes annually")
        st.error("**Economic Loss:** ₹14.2 Crore per year")

    with col3:
        st.subheader("The Solution")
        st.write("**Target:** Top 3 Friction Hotspots")
        st.write("**Recovery:** 38% of total lost time")
        st.success("**ROI:** 10:1 Benefit-to-Cost Ratio")

    st.markdown("---")

    # --- THE MATHEMATICAL FRAMEWORK (Detailed Dropdown) ---
    with st.expander("Detailed Technical Framework & Variable Itinerary"):
        st.markdown("#### 1. The Friction Field and Effective Path Length")
        st.markdown("""
        We model the corridor as a spatially varying friction field $f(x, \phi)$. The 'Effective Path Length' 
        represents the actual energetic and mechanical work done by a pedestrian to overcome obstacles.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \approx d\sum_{i=1}^{N} f_i(\phi)")
        st.markdown("""
        **Variables:**
        * $L_{\text{eff}}$: Effective Path Length (The 'perceived' distance in terms of effort).
        * $D$: Physical distance of the corridor (900m).
        * $f(x, \phi)$: Local friction index (1 to 5) at position $x$ for persona $\phi$.
        * $d$: Segment length for discretization (12.5m).
        """)

        st.markdown("#### 2. Power-Law Velocity Model & Time Tax")
        st.markdown("""
        Walking speed is not linearly reduced by obstacles; it follows a power-law decay based on 
        the commuter's sensitivity ($k$) to the environment.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.markdown("""
        **Variables:**
        * $v_{\text{eff}}$: Real-world velocity across a specific segment.
        * $v_0(\phi)$: Natural walking speed of the persona on a perfect footpath.
        * $k(\phi)$: Friction sensitivity exponent (e.g., $k=1.2$ for wheelchairs, $k=0.6$ for adults).
        * $\Delta\tau(\phi)$: Time Tax (Seconds stolen per trip compared to a standard path).
        """)

        st.markdown("#### 3. Aggregated Economic Loss")
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi}")
        st.markdown("""
        **Variables:**
        * $\mathcal{T}_{\text{year}}$: Total annual productivity loss.
        * $M$: Total daily commuter volume (100,000).
        * $W$: Annual working days (250).
        * $w_\phi$: Population weighting for each persona.
        """)

    st.markdown("---")

    # --- MODULE OVERVIEW ---
    st.header("Audit Modules")
    st.markdown("""
    Navigate through the sidebar to explore the specific data layers of this audit:
    """)

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 Friction Mapper")
        st.write("""
        An interactive, geotagged map of the 900m route. 
        - **Bazaar Street (600m):** Discretized as a continuous $f=5$ failure.
        - **Constitution Circle (300m):** 24 specific nodes including open drains and illegal encroachments.
        """)

        st.markdown("#### ⏳ Time Tax Simulator")
        st.write("""
        Persona-based simulations showing how the 'tax' is disproportionately levied on 
        vulnerable groups. Reveals that wheelchair users bear 3x the time loss of able-bodied adults.
        """)

    with m_col2:
        st.markdown("#### 💡 What-If: Lighthouse Pilot")
        st.write("""
        A prioritization tool for urban planners. It ranks every obstacle by its impact on the 
        total time tax, allowing for a 'High Impact, Low Cost' repair schedule.
        """)

        st.markdown("#### 💰 Economic Impact")
        st.write("""
        Translates time loss into INR using RBI wage benchmarks. This module provides the 
        fiscal justification for the 'Lighthouse' infrastructure intervention.
        """)

    st.markdown("---")
    st.info("👈 **Select a module from the sidebar to begin the deep dive.**")

    st.caption(
        "Developed for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "Audit Dates: March 7–8, 2026"
    )

else:
    if page in modules:
        # Ensure the sub-module title is displayed
        st.title(page)
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
