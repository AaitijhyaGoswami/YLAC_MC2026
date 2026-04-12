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
    modules["What-If: Lighthouse Prototype"] = what_if
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
    systemic design failures and physical barriers.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 The Scale")
        st.write("The audit covered a high-intensity 900m corridor serving over 100,000 daily commuters. Our data indicates that 90.3% of the route fails to meet national Active Mobility standards, creating a systemic bottleneck at a major transit interchange.")

    with col2:
        st.subheader("📉 The Impact")
        st.write("Poor infrastructure acts as a resistive force field, making the corridor 4.65x more difficult to navigate than a compliant path. This results in 170 million minutes lost annually, equivalent to a ₹14.2 Crore productivity loss.")

    with col3:
        st.subheader("💡 The Solution")
        st.write("The 'Lighthouse' proposal identifies the top 3 high-friction hotspots. Remediating these specific nodes via the S.U.R.E. prototype recovers 38% of the total lost time, delivering a Benefit-to-Cost ratio exceeding 10:1.")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 Why Physics?")
    st.markdown("""
    Urban audits are traditionally qualitative, relying on anecdotal complaints that carry little weight in policy 
    budgeting. By applying principles of classical mechanics, we redefine a 'bad sidewalk' as a measurable 
    **resistive field**. In this framework, a pedestrian is an agent navigating a potential energy landscape where 
    broken drains, encroachments, and missing slabs are physical barriers $\Phi(x)$ that require mechanical work 
    to overcome. This approach allows us to treat human time as a finite economic resource being 'taxed' by 
    infrastructure friction. By providing a mathematically rigorous foundation, we bridge the gap between 
    commuter frustration and governmental decision-making.
    """)

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("📖 View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### 1. The Friction Field and Effective Path Length")
        st.markdown("""
        To quantify the journey's difficulty, we define the **Effective Path Length**, representing the total 
        energetic work required by a pedestrian. This is the integral of the local friction index across 
        the physical distance of the corridor.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \;\approx\; d\sum_{i=1}^{N} f_i(\phi)")
        st.latex(r"""
            \begin{aligned}
            L_{\text{eff}} &: \text{Effective Path Length (The perceived distance in terms of effort)} \\
            D &: \text{Physical surveyed distance (Totaling 900 meters for this corridor)} \\
            f(x, \phi) &: \text{Local Friction Index (Scale: 1 = Gold Standard, 5 = Systemic Failure)} \\
            d &: \text{Discretized segment length used in the physical audit (12.5 meters)} \\
            \phi &: \text{Commuter persona defining specific mobility constraints and parameters}
            \end{aligned}
        """)

        st.markdown("#### 2. Power-Law Velocity and the Time Tax")
        st.markdown("""
        Pedestrian velocity does not decrease linearly with infrastructure failure; it follows a power-law decay. 
        The **Time Tax** is the deviation between actual traversal time and the ideal time required on a 
        compliant corridor where the friction index is unity throughout.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.latex(r"""
            \begin{aligned}
            v_{\text{eff}} &: \text{Actual velocity achieved across a specific physical segment } i \\
            v_0 &: \text{Natural walking speed of persona } \phi \text{ on a zero-friction surface} \\
            k &: \text{Sensitivity exponent (The coefficient of vulnerability for mobility aids)} \\
            \Delta\tau &: \text{The Time Tax (The cumulative seconds of life-time stolen per trip)} \\
            N &: \text{The total number of surveyed segments across the corridor length } D
            \end{aligned}
        """)

        st.markdown("#### 3. Macro-Economic Aggregation")
        st.markdown("""
        The total economic impact is calculated by aggregating the persona-weighted mean Time Tax across the 
        entire commuter population for a standard working year, converted to monetary value using wage benchmarks.
        """)
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi}")
        st.latex(r"""
            \begin{aligned}
            \mathcal{T}_{\text{year}} &: \text{Total annual economic productivity loss expressed in INR} \\
            M &: \text{Total daily commuter volume passing through the Yeshwantpur knot} \\
            W &: \text{Standardized working days per annum (Calibrated to 250 days)} \\
            w_\phi &: \text{Demographic weighting factor based on observed pedestrian volume splits}
            \end{aligned}
        """)

    st.markdown("---")

    # --- MODULE OVERVIEW (Numbered List) ---
    st.header("🛠️ Audit Modules")
    st.markdown("Select a module from the sidebar to explore the individual data layers:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 1. Friction Mapper")
        st.write("1. **Geotagged Database:** An interactive visualization of 24 specific infrastructure failures mapped with sub-meter coordinate precision.")
        st.write("2. **Zonal Analysis:** Differentiates between the Bazaar Street zone (600m total failure) and the Constitution Circle stretch.")
        st.write("3. **Audit Evidence:** Links technical friction indices to photographic logs and timestamps generated during the field audit.")

        st.markdown("#### ⏳ 2. Time Tax Simulator")
        st.write("1. **Agent Simulation:** Executes persona-specific journeys through the friction field to measure real-world traversal times.")
        st.write("2. **Equity Gap Analysis:** Quantifies how infrastructure failure disproportionately taxes the life-time of the elderly and disabled.")
        st.write("3. **Risk Metrics:** Tracks the frequency and duration of 'impassable' nodes that force pedestrians into vehicular lanes.")

    with m_col2:
        st.markdown("#### 🏗️ 3. What-If: Lighthouse Prototype")
        st.write("1. **3D Engineering Cross-Section:** A static 3D model of a redesigned Yeshwantpur segment, built to Tender S.U.R.E. and Active Mobility Bill standards.")
        st.write("2. **Technical Specs:** Features a 3m continuous footpath, flush drainage, and underground utility ducts authored in Zoo.dev's KCL.")
        st.write("3. **Visual Advocacy:** Provides a 'measurable counterpart' to the friction audit—serving as a blueprint for the 20m Lighthouse Pilot intervention.")

        st.markdown("#### 💰 4. Economic Impact")
        st.write("1. **Fiscal Valuation:** Translates lost time into Crore-value figures based on RBI-benchmarked informal and formal wage rates.")
        st.write("2. **Investment CBA:** Demonstrates the massive 10:1 return on investment for small-scale, targeted municipal repairs.")
        st.write("3. **Policy Synthesis:** Generates the quantitative 'bottom-line' data required for DULT and BBMP budget approval templates.")

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
