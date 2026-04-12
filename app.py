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
        st.write("The audit covered a 900m stretch used by 100,000+ people daily. We found that 90% of the path is effectively broken, forcing people to navigate a 'mobility knot' that prioritizes vehicles over human beings.")

    with col2:
        st.subheader("📉 The Impact")
        st.write("Walking here is 4.65x harder than it should be. This isn't just an annoyance—it's a massive drain on the city, wasting 170 million minutes of human life and ₹14.2 Crore in productivity every single year.")

    with col3:
        st.subheader("💡 The Solution")
        st.write("We don't need to fix everything at once. By applying a 'Lighthouse' design to just the 3 worst spots, we can recover nearly 40% of all that lost time, making the most of every rupee spent on repairs.")

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("🧠 Why are we using Physics to study a street?")
    st.markdown("""
    Usually, when we complain about bad footpaths, officials see it as a matter of 'comfort' or 'convenience.' But for a 
    person walking to the metro, a broken drain is more than an inconvenience—it is a physical barrier that demands 
    extra energy and steals time. We use the laws of physics because they are objective. By treating a pedestrian 
    as an 'agent' moving through a 'force field' of obstacles, we turn vague frustrations into hard numbers. 
    Whether you are an engineer or a daily commuter, you know that walking through a crowd or over debris is 
    physically exhausting. Our math simply captures that exhaustion so the government can no longer ignore it.
    """)

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("📖 View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### 1. The Effective Path Length: How long the walk 'feels'")
        st.markdown("""
        If you walk 10 meters on a clean floor, it takes very little effort. If you walk 10 meters through knee-deep 
        water, your body works much harder. Even though the map says the distance is the same, the 'Effective Distance' 
        is much longer. We calculate this by looking at the 'Friction' or struggle caused by every meter of the road.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \;\approx\; d\sum_{i=1}^{N} f_i(\phi)")
        
        st.latex(r"L_{\text{eff}} : \text{Effective Path Length—the 'felt' distance of the walk in terms of physical effort}")
        st.latex(r"D : \text{The physical distance measured on a map (900 meters for this corridor)}")
        st.latex(r"f(x, \phi) : \text{The Local Friction Index—how much a specific spot struggles against the walker}")
        st.latex(r"d : \text{The length of each small block we audited (12.5 meters)}")
        st.latex(r"\phi : \text{The Persona—adjusts the difficulty based on whether the walker is an adult or in a wheelchair}")

        st.markdown("#### 2. The Time Tax: Why some people are slowed down more than others")
        st.markdown("""
        A small crack in the pavement might not slow down a young adult, but it could completely stop a person 
        in a wheelchair. This 'Sensitivity' to bad roads is what we call the Power-Law. The 'Time Tax' is the 
        total amount of time that the infrastructure 'steals' from your day compared to a perfect, smooth path.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        
        st.latex(r"v_{\text{eff}} : \text{Your actual walking speed when faced with obstacles and broken ground}")
        st.latex(r"v_0 : \text{Your ideal walking speed if the footpath was perfect and unobstructed}")
        st.latex(r"k : \text{Friction Sensitivity—how much a broken road hurts your specific speed}")
        st.latex(r"\Delta\tau : \text{The Time Tax—the extra seconds or minutes you are forced to waste on every trip}")

        st.markdown("#### 3. Economic Loss: The cost of stolen time")
        st.markdown("""
        When 100,000 people lose a few minutes every day, those minutes add up to years of lost life. We 
        calculate the total economic value of this wasted time by looking at the average daily wage in the 
        city. This turns a 'walking problem' into a 'money problem' that the government can understand.
        """)
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi}")
        
        st.latex(r"\mathcal{T}_{\text{year}} : \text{The total annual cost to the city's economy in lost productivity}")
        st.latex(r"M : \text{The total number of people who walk this path every day (100,000)}")
        st.latex(r"W : \text{The number of working days in a year (standardized to 250 days)}")
        st.latex(r"w_\phi : \text{The percentage of each type of person—like delivery partners or students—in the crowd}")

    st.markdown("---")

    # --- MODULE OVERVIEW (Numbered List) ---
    st.header("🛠️ Audit Modules")
    st.markdown("Select a module from the sidebar to explore the data for yourself:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 1. Friction Mapper")
        st.write("1. **Interactive Evidence:** See the map of 24 specific spots where the road fails, complete with GPS locations.")
        st.write("2. **Zonal Breakdown:** Understand the difference between the complete failure of Bazaar Street and the obstacles at Constitution Circle.")
        st.write("3. **Field Data:** View the actual technical ratings and photographic evidence we gathered during our two-day audit.")

        st.markdown("#### ⏳ 2. Time Tax Simulator")
        st.write("1. **Human Journey:** Watch a simulation of different people—from students to the elderly—moving through the audit zone.")
        st.write("2. **The Inequity Gap:** See exactly how much more 'Time Tax' is paid by a wheelchair user compared to an able-bodied person.")
        st.write("3. **Danger Zones:** See where the sidewalk is so bad that people are forced to walk in front of moving cars.")

    with m_col2:
        st.markdown("#### 🏗️ 3. What-If: Lighthouse Prototype")
        st.write("1. **3D Engineering View:** A high-quality 3D cross-section of what a 'Tender S.U.R.E.' compliant road actually looks like.")
        st.write("2. **The Blueprint:** Features a 3m wide clear path, underground utility ducts, and smooth ramps for everyone to use.")
        st.write("3. **The Proof:** A visual demonstration that fixing even 20 meters of road correctly can change the experience for everyone.")

        st.markdown("#### 💰 4. Economic Impact")
        st.write("1. **The Money Map:** See how wasted minutes turn into a ₹14.2 Crore loss for our local economy.")
        st.write("2. **Smart Spending:** Compare the small cost of fixing hotspots against the massive financial return for the city.")
        st.write("3. **Policy Ready:** All data is formatted to help government officials make quick, data-driven budget decisions.")

    st.markdown("---")
    st.info("👈 **Select a module from the sidebar to begin. Every second counts!**")

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
