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
    st.markdown("##### Yeshwantpur Mobility Knot · Bengaluru · YLAC 2026")
    st.markdown("---")

    st.markdown(
        "A physics-based audit of the 900m Yeshwantpur–Constitution Circle corridor, "
        "quantifying the **Time Tax** imposed on 100,000+ daily commuters by broken "
        "infrastructure — and building the data case for a Tender S.U.R.E. intervention."
    )

    st.info("👈 Select a module from the sidebar to begin.")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fails Active Mobility Bill", "90.3%")
    col2.metric("Wheelchair inaccessible", "96.0%")
    col3.metric("Mean friction index f̄", "4.65")
    col4.metric("Survey date", "Mar 7–8, 2026")

    st.caption(
        "Built for [Bengawalk](https://bengawalk.com) · "
        "[DULT Active Mobility Bill](https://dult.karnataka.gov.in/121/active-mobility-bill/en)"
    )

else:
    if page in modules:
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
