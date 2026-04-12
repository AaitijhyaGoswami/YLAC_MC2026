import streamlit as st

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Escape the Knot | Yeshwantpur",
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
st.sidebar.title("🚶 Escape the Knot")
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
    st.title("🚶 Escape the Knot")
    st.markdown("### A Physics-Based Audit of the Yeshwantpur Mobility Knot")
    
    st.markdown("""
    This project quantifies the **infrastructural tax** imposed on pedestrians at the Yeshwantpur intermodal hub. 
    By treating the urban environment as a physical system—where obstacles like broken drains and 
    encroachments act as potential energy barriers—we can measure the 'Time Tax' stolen from every commuter.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 The Scale")
        st.write("The audit covered the 900m corridor between Yeshwantpur and Constitution Circle, an area serving over 100,000 daily commuters. We found that 90.3% of this stretch fails to meet Active Mobility standards.")

    with col2:
        st.subheader("📉 The Impact")
        st.write("Due to severe infrastructure friction, the corridor imposes 4.65x the effort of a standard path. This results in 170 million minutes lost annually, costing the city ₹14.2 Crore in productivity.")

    with col3:
        st.subheader("💡 The Solution")
        st.write("Our 'Lighthouse' proposal targets the top 3 hotspots. Repairing these specific points recovers 38% of the total lost time with a Benefit-to-Cost ratio exceeding 10:1.")

    st.markdown("---")

    # --- THE MATHEMATICAL FRAMEWORK (Textbook Style) ---
    with st.expander("📖 View Technical Methodology and Equation Definitions"):
        st.markdown("#### 1. The Friction Field and Effective Path Length")
        st.markdown("""
        To quantify the difficulty of a journey, we define the **Effective Path Length**, which represents the total 
        energetic work performed by a pedestrian. This is calculated by integrating the spatially varying friction 
        field along the total distance of the corridor.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \approx d\sum_{i=1}^{N} f_i(\phi)")
        st.markdown("""
        In this formulation, $L_{\text{eff}}$ is the effective length felt by the commuter and $D$ is the physical distance 
        of 900 meters. The term $f(x, \phi)$ represents the local friction index—ranging from 1 for ideal paths to 5 for 
        complete failures—for a specific commuter persona $\phi$, while $d$ denotes the segment length of 12.5 meters 
        used during our discretized field audit.
        """)

        st.markdown("#### 2. Power-Law Velocity and the Time Tax")
        st.markdown("""
        Pedestrian speed is not linearly affected by obstacles; rather, it follows a decay model where the 
        **Time Tax** is the difference between the actual traversal time and the ideal time on a compliant footpath.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.markdown("""
        Here, $v_{\text{eff}}$ is the actual velocity achieved across a segment and $v_0$ is the natural walking speed of the 
        persona. The exponent $k$ represents the friction sensitivity, which is higher for vulnerable groups like wheelchair 
        users, and $\Delta\tau$ is the resulting Time Tax, or the cumulative seconds lost per trip.
        """)

        st.markdown("#### 3. Macro-Economic Aggregation")
        st.markdown("""
        The total economic impact is derived by aggregating the persona-weighted mean Time Tax across the entire 
        commuter population for a standard working year.
        """)
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi}")
        st.markdown("""
        In this expression, $\mathcal{T}_{\text{year}}$ represents the annual economic loss, $M$ is the daily commuter 
        volume of 100,000, $W$ represents 250 working days, and $w_\phi$ is the weight assigned to each persona 
        based on population demographics.
        """)

    st.markdown("---")

    # --- MODULE OVERVIEW (Pointwise) ---
    st.header("🛠️ Audit Modules")
    st.markdown("Select a module from the sidebar to explore the data in detail:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 1. Friction Mapper")
        st.write("1. **Geotagged Database:** Provides a map of 24 specific infrastructure failures with GPS coordinates.")
        st.write("2. **Zonal Distinction:** Identifies the 600m Bazaar Street failure zone vs. the staccato obstacles of Constitution Circle.")
        st.write("3. **Evidence Export:** Generates photographic and technical logs suitable for policy submissions.")

        st.markdown("#### ⏳ 2. Time Tax Simulator")
        st.write("1. **Agent Simulation:** Models the movement of four distinct personas through the friction field.")
        st.write("2. **Equity Analysis:** Highlights the disproportionate time burden carried by wheelchair users and the elderly.")
        st.write("3. **Detour Mapping:** Tracks when users are forced to leave the footpath and enter the vehicular right-of-way.")

    with m_col2:
        st.markdown("#### 💡 3. What-If: Lighthouse Pilot")
        st.write("1. **Fix Prioritization:** Ranks every obstacle by how much total time it would recover if repaired.")
        st.write("2. **Impact Curve:** Visualizes the diminishing returns of repairs to help planners find the 'sweet spot' for intervention.")
        st.write("3. **Pilot Strategy:** Proves that fixing just 3 major hotspots can solve nearly 40% of the bottleneck.")

        st.markdown("#### 💰 4. Economic Impact")
        st.write("1. **Productivity Valuation:** Converts time loss into monetary figures using RBI-benchmarked wage rates.")
        st.write("2. **CBA Tool:** Calculates the Benefit-to-Cost ratio for different infrastructure investment scenarios.")
        st.write("3. **Policy Briefing:** Synthesizes all data into a one-page summary for government stakeholders.")

    st.markdown("---")
    st.info("👈 **Please select a module from the sidebar to begin the data exploration.**")

    st.caption(
        "Developed for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "Audit Dates: March 7–8, 2026"
    )

else:
    if page in modules:
        st.title(page)
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
