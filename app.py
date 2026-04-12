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
    By treating the urban environment as a physical system, we measure the 'Time Tax' stolen from every commuter by 
    systemic design failures.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 The Scale")
        st.write("The audit covered a 900m high-traffic corridor serving over 100,000 daily commuters. Our data shows that 90.3% of the route fails to meet basic mobility standards, creating a massive bottleneck at one of Bengaluru's most critical transit interchanges.")

    with col2:
        st.subheader("📉 The Impact")
        st.write("Poor infrastructure acts as a resistive force, making the corridor 4.65x harder to navigate than a standard path. This results in 170 million minutes lost annually, translating to a ₹14.2 Crore productivity loss for the city.")

    with col3:
        st.subheader("💡 The Solution")
        st.write("Our 'Lighthouse' proposal identifies the top 3 high-friction hotspots. Repairing these specific nodes recovers 38% of the total lost time, offering a Benefit-to-Cost ratio of 10:1 for municipal investment.")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 Why Physics?")
    st.markdown("""
    Traditional urban audits often rely on subjective complaints which are easily dismissed in policy discussions. 
    By applying the principles of classical mechanics, we transform a 'bad sidewalk' into a quantifiable **resistive field**. 
    In this model, a pedestrian is an agent moving through a potential landscape. Broken slabs, encroachments, and 
    open drains are not just inconveniences; they are energy barriers that require physical work to overcome. 
    By treating time as a finite resource being 'taxed' by these barriers, we bridge the gap between human 
    frustration and economic data, providing the government with a mathematically rigorous justification for 
    immediate infrastructure repair.
    """)

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("📖 View Technical Methodology and Variables"):
        st.markdown("#### 1. The Friction Field and Effective Path Length")
        st.markdown("""
        The difficulty of a journey is defined by the **Effective Path Length**, representing the total 
        energetic work performed. We integrate the local friction index along the corridor's physical distance.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \approx d\sum_{i=1}^{N} f_i(\phi)")
        st.markdown("""
        **L_eff** is the effective length or 'felt distance' of the journey.  
        **D** represents the physical map distance of 900 meters.  
        **f(x, phi)** is the local friction index, ranging from 1 for ideal paths to 5 for complete failures, adjusted for the commuter persona.  
        **d** is the segment length of 12.5 meters used for the discretized field audit.
        """)

        st.markdown("#### 2. Power-Law Velocity and the Time Tax")
        st.markdown("""
        Pedestrian speed decays exponentially as friction increases. The **Time Tax** is the difference 
        between the actual time forced by the terrain and the ideal time on a standard footpath.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.markdown("""
        **v_eff** is the actual velocity achieved across a specific segment.  
        **v_0** represents the natural walking speed of the persona on an unobstructed surface.  
        **k** is the friction sensitivity exponent, which increases for vulnerable groups like wheelchair users.  
        **Δτ** is the resulting Time Tax, representing the cumulative seconds stolen per trip.
        """)

        st.markdown("#### 3. Macro-Economic Aggregation")
        st.markdown("""
        The total economic impact is calculated by aggregating the weighted mean Time Tax across the 
        entire commuter population for a standard working year.
        """)
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi}")
        st.markdown("""
        **T_year** is the total annual economic productivity loss for the city.  
        **M** is the daily commuter volume of 100,000 individuals.  
        **W** represents the 250 working days in a year.  
        **w_phi** is the population weighting for each specific commuter persona.
        """)

    st.markdown("---")

    # --- MODULE OVERVIEW ---
    st.header("🛠️ Audit Modules")
    st.markdown("Use the sidebar to explore the individual data layers of the Yeshwantpur Audit:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 1. Friction Mapper")
        st.write("1. **Geotagged Database:** An interactive map of 24 specific failures with precise coordinates.")
        st.write("2. **Zonal Analysis:** Differentiates the Bazaar Street zone from the Constitution Circle stretch.")
        st.write("3. **Field Evidence:** Links technical friction ratings to photographic timestamps from the audit.")

        st.markdown("#### ⏳ 2. Time Tax Simulator")
        st.write("1. **Agent Simulation:** Runs persona-specific journeys through the audited friction field.")
        st.write("2. **Equity Gap:** Quantifies the disproportionate burden placed on the elderly and disabled.")
        st.write("3. **Detour Metrics:** Calculates the safety risk when pedestrians are forced into vehicular lanes.")

    with m_col2:
        st.markdown("#### 💡 3. What-If: Lighthouse Pilot")
        st.write("1. **Prioritization Engine:** Identifies which obstacles provide the most 'time recovery' per rupee.")
        st.write("2. **Scenario Planning:** Allows users to simulate how different levels of repair impact the city.")
        st.write("3. **Targeted Fixes:** Proves that repairing the top 3 hotspots solves 38% of the entire bottleneck.")

        st.markdown("#### 💰 4. Economic Impact")
        st.write("1. **Monetary Valuation:** Converts lost seconds into Crore-value figures based on RBI wage rates.")
        st.write("2. **CBA Analysis:** Demonstrates the massive return on investment for small municipal repairs.")
        st.write("3. **Policy Brief:** Synthesizes the data into the specific language required for government approval.")

    st.markdown("---")
    st.info("👈 **Please select a module from the sidebar to begin exploring the data.**")

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
