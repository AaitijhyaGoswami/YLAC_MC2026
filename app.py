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
    modules["The Obstacle Map"] = friction_mapper
except ImportError:
    pass

try:
    from simulation import agent_sim
    modules["Who Loses Most Time?"] = agent_sim
except Exception as e:
    st.sidebar.error(f"agent_sim failed: {e}")

try:
    from simulation import what_if
    modules["The 3-Step Fix"] = what_if
except ImportError:
    pass

try:
    from simulation import policy_brief
    modules["The Hidden Cost"] = policy_brief
except ImportError:
    pass


# SIDEBAR NAVIGATION
st.sidebar.title("Escape the Knot")
st.sidebar.caption("A People-First Audit of Yeshwantpur · YLAC 2026")

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
    st.subheader("Why a 10-minute walk in Yeshwantpur feels like a mountain trek.")
    
    st.markdown("---")

    # --- THE HOOK ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Actual Distance", value="900 Meters")
    with col2:
        st.metric(label="How it Feels (Effort)", value="4.2 Kilometers", delta="4.6x Harder")
    with col3:
        st.metric(label="Wheelchair Access", value="4%", delta="-96% Failed", delta_color="inverse")

    st.markdown("""
    ### The "Ghost Kilometers"
    When you walk from the Yeshwantpur Metro to Constitution Circle, you aren't just walking 900 meters. 
    Every broken drain, parked bike on the pavement, and missing footpath acts like a **'Time Tax.'** We used physics to calculate the **Struggle Factor ($f$)**. On a perfect sidewalk, $f = 1$. 
    In Yeshwantpur, the average struggle factor is **4.65**. 
    
    **This means walking here requires nearly 5 times the energy and effort of a standard city walk.**
    """)

    with st.expander("See the Math (For the Nerds 🤓)"):
        st.latex(r"L_{\text{eff}} = \int_0^D f(x)\, dx \approx 4.65 \times D")
        st.write("We treat every obstacle as a 'friction' point. Your 'Effective Path Length' is the total effort you spend fighting the infrastructure.")

    st.markdown("---")
    
    # --- VISUAL CARDS FOR MODULES ---
    st.header("Explore the Data")
    
    m1, m2 = st.columns(2)
    
    with m1:
        st.markdown("### 📍 1. The Obstacle Map")
        st.write("""
        We geotagged every single 'friction point'—from open drains to illegal parking. 
        Explore the map to see exactly where the system fails the pedestrian.
        """)
        if st.button("Open Map"):
            st.info("Select 'The Obstacle Map' in the sidebar.")

    with m2:
        st.markdown("### ⏳ 2. Who Loses Most Time?")
        st.write("""
        A broken sidewalk is an inconvenience for an adult, but a dead-end for a wheelchair user. 
        We simulated different people to see how much **Life Time** is stolen from them daily.
        """)

    m3, m4 = st.columns(2)

    with m3:
        st.markdown("### 💡 3. The 'What-If' Fix")
        st.write("""
        What if we fixed just the 3 worst spots? We show how small, targeted repairs 
        on Bazaar Street can recover **38% of the lost time** for everyone.
        """)

    with m4:
        st.markdown("### 💰 4. The Hidden Cost")
        st.write("""
        Bad footpaths aren't just annoying; they are expensive. We calculated that Yeshwantpur's 
        broken corridor costs the city **₹14.2 Crore every year** in lost productivity.
        """)

    st.markdown("---")
    
    # --- CALL TO ACTION ---
    st.warning("""
    **The Verdict:** 90% of this corridor fails the 'Active Mobility' standards. 
    By fixing just 3 hotspots (Cost: ~₹10 Lakh), we can save the city crores in wasted time.
    """)

    st.caption(
        "Built for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026 · "
        "In support of the DULT Active Mobility Bill"
    )

else:
    if page in modules:
        # Display the module name as a header if not already in the module's app code
        st.title(page) 
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
