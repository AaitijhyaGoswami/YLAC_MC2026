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
    st.subheader("A Physics-Based Audit of the Yeshwantpur Mobility Knot")
    
    st.markdown("""
    This dashboard quantifies the **infrastructural tax** imposed on pedestrians in Bengaluru. 
    By treating the city as a physical system, we can measure exactly how much energy and time is 
    stolen from citizens by poor infrastructure.
    """)
    st.markdown("---")

    # --- THE METRICS SECTION ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Surveyed Corridor", value="900 Meters")
        st.caption("Yeshwantpur – Constitution Circle")
    with col2:
        st.metric(label="Average Struggle Factor", value="4.65x", delta="Friction Index")
        st.caption("Effort compared to a standard sidewalk")
    with col3:
        st.metric(label="Annual Economic Loss", value="₹14.2 Cr", delta="Productivity Cost")
        st.caption("Estimated for 100k daily users")

    st.markdown("---")

    # --- CORE CONCEPTS ---
    st.header("The Methodology")
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("#### 1. The Friction Field ($f$)")
        st.write("""
        We don't just count potholes; we assign a **Struggle Factor** ($f$) to every meter of the road. 
        - **$f = 1$:** Gold standard (Tender S.U.R.E) footpath. 
        - **$f = 5$:** Complete system failure (walking in traffic).
        """)
        
        st.markdown("#### 2. The Ghost Kilometers ($L_{\\text{eff}}$)")
        st.write("""
        Because of the high friction, a 900m walk *feels* much longer. This is the **Effective Path Length**:
        """)
        st.latex(r"L_{\text{eff}} \approx d\sum_{i=1}^{N} f_i(\phi)")
        st.info("**Result:** In Yeshwantpur, your body does the work of a **4.2km walk** just to cover **900m**.")

    with c2:
        st.markdown("#### 3. The Time Tax ($\\Delta\\tau$)")
        st.write("""
        Bad roads slow you down. We calculate the seconds lost per person based on their 'Sensitivity' to friction ($k$).
        """)
        st.latex(r"\Delta\tau(\phi) = T_{\text{actual}} - T_{\text{ideal}}")
        st.write("""
        A wheelchair user faces a much higher **Time Tax** than an able-bodied adult because their 
        sensitivity to a broken slab is exponentially higher.
        """)

    st.markdown("---")

    # --- THE MODULES BREAKDOWN ---
    st.header("What’s inside the Audit?")
    
    tab1, tab2, tab3 = st.tabs(["The Route Audit", "The Human Cost", "The Solution"])

    with tab1:
        st.markdown("### 📍 Module 1: Friction Mapper")
        st.markdown("""
        The 900m corridor is split into two distinct failure zones:
        * **Bazaar Street (600m):** A total failure zone ($f=5$). No usable footpath exists.
        * **Constitution Circle (300m):** A 'staccato' zone with 24 specific obstacles (open drains, encroachments).
        """)
        st.latex(r"L_{\text{eff}}^{Total} = 3000\text{m} (\text{Bazaar}) + 1187.5\text{m} (\text{Circle}) = 4187.5\text{m}")
        st.write("👉 **Use this module to view the interactive map of all 24 geotagged obstacles.**")

    with tab2:
        st.markdown("### ⏳ Module 2 & 4: Human & Economic Impact")
        st.write("""
        We simulated 100,000 daily commuters across four personas:
        - 🚶 **Adults:** 1.4 m/s speed.
        - ♿ **Wheelchair Users:** Faces 'Geometric Penalties'—must detour into traffic.
        - 👴 **Elderly:** Slower speeds, higher sensitivity to broken ground.
        """)
        st.write("**Economic Bottom Line:** The wasted time on this 900m stretch costs Bengaluru **₹14.2 Crore** in lost productivity every year.")

    with tab3:
        st.markdown("### 💡 Module 3: What-If (The Lighthouse Pilot)")
        st.write("""
        This is our proposal to the government. Using a **Marginal Return Curve**, we found that:
        - Fixing **just the top 3 hotspots** (at a cost of ~₹10 Lakh) recovers **38% of all lost time**.
        """)
        st.success("By focusing on the 'worst first,' we get a Benefit-to-Cost ratio exceeding **10:1**.")

    st.markdown("---")
    st.info("👈 **Select a module from the sidebar to dive into the data.**")
    
    st.caption(
        "Built for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "Audit conducted March 7–8, 2026"
    )

else:
    if page in modules:
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
