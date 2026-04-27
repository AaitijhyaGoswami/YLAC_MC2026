import streamlit as st

# PAGE CONFIGURATION
st.set_page_config(
    page_title="Escape The Knot | Yeshwantapura",
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
except ImportError:
    pass

try:
    from simulation import economic_impact
    modules["Economic Impact"] = economic_impact
except ImportError:
    pass

# Inside your main app.py
try:
    # We now point Python to look inside the static folder
    from cad_viewer import viewer 
    modules["What-If: Lighthouse Prototype"] = viewer
except ImportError:
    pass

# SIDEBAR NAVIGATION
st.sidebar.title("Advocacy Modules")
st.sidebar.caption("Yeshwantpur Mobility Audit 2026")

options = ["Home"] + list(modules.keys())
page = st.sidebar.radio("Navigate:", options)

st.sidebar.markdown("---")
st.sidebar.caption("Project Team:")
st.sidebar.info(
    "**Aaitijhya Goswami**  \n*Indian Institute of Science, Bengaluru*\n\n"
    "**Prajwal Kagalgomb**  \n*Indian Institute of Management, Bengaluru*"
)


# MAIN ROUTING
if page == "Home":
    st.title("🚶 Escape The Knot")
    st.markdown("### A Physics-Based Audit of the Yeshwantpur-Mathikere Region")

    st.header("Why Do This?")
    
    st.markdown("""
    This project comes out of the need to connect the high-level urban policy with the lived experience of the commuters who traverse the Yeshwantpur-Mathikere nexus every day. While policy frameworks provide a strong theoretical base for urban reform, they are frequently too abstract and too distant from the very citizens they are meant to serve. This module is a stakeholder-first translation tool. It uses a physics-based diagnostic. It goes beyond the heavy legalese of policy documents to show exactly how a reclaimed clear recovers lost minutes, restores human dignity, and pumps economic value back into the lives of delivery partners, students and elderly residents alike.
    
    The policies that define the reference standards for our evaluations are:
    
    * **[Active Mobility Bill (2022)](https://dult.karnataka.gov.in/121/active-mobility-bill/en)**
    * **[Tender S.U.R.E. (Sustainable Urban Road Engineering)](https://www.janausp.org/portfolio/tender-sure)**
    * **[IRC:103-2022 (Indian Roads Congress)](https://www.anjleeagarwal.co.in/books/IRC-103-2022.pdf)**
    * **[Harmonised Guidelines and Space Standards (2021)](https://niua.in/intranet/sites/default/files/2262.pdf)**
    * **[DULT Urban Street Design Guidelines](https://dult.karnataka.gov.in/89/policies-and-guidelines/en)**

    This audit anchors academic rigor in the lived experience of the street, providing an engineering blueprint for Modal Equilibrium. It turns the “Streets of Hope” vision from a legislative dream into a data-based demand for swift remediation.
    """)
    
    st.markdown("---")

    # --- UPFRONT: SCALE, IMPACT, SOLUTION ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Why Yeshwantpur of All Places?")
        st.write("Established in 1881 by the Maharaja of Mysuru, the Yeshwantpur Railway Station and the adjacent Bazaar Street are among the oldest areas in the city, which developed on an infrastructure that lacked consideration for accessible pedestrian travel and equitable distribution of vehicular traffic. Unplanned, systemic encroachments over several decades further worsened the situation.")
        st.subheader("📊 The Scale")
        st.write("The audit covered a high-intensity 900 m corridor serving over 100,000 daily commuters. Our data indicates that **90.3%** of the pedestrian route fails to meet national Active Mobility standards, with about **96%** of it being inaccessible to persons with disabilities. This systemic failure is no longer just a minor inconvenience; it is the denial of access to a section of the population at one of the busiest railway stations in South India.")

    with col2:
        st.subheader("📉 The Impact")
        st.write("Poor infrastructure acts as a resistive force field, making the corridor 4.65x more difficult to navigate than a compliant path, i.e. the 900 m pedestrian route feels like a 4.5 km commute due to the obstacles. This results in 170 million minutes lost annually, equivalent to a productivity loss of ₹14.2 Crore for physically fit individuals alone.")
        st.subheader("💡 The Solution")
        st.write("The 'Lighthouse' proposal identifies the top 3 high-friction hotspots. Remediating these specific nodes via the S.U.R.E. prototype recovers 38% of the total lost time, delivering a Benefit-to-Cost Ratio (BCR) exceeding 10:1. The only piece missing is the initiative and response of the local authorities to the public grievances, as corroborated by stakeholder interviews.")

    st.markdown("---")
    st.header("What We Saw")

    cola, colb, colc = st.columns(3)

# 3. Add images to columns
    with cola:
      st.image("data/survey1.jpg", use_container_width=True)
      st.caption("A carpentry shop encroaching on the area meant for pedestrian commute. The obstacle may make it difficult for individuals in wheelchairs or visually impaired individuals to commute.")
      st.image("data/survey2.jpg", use_container_width=True)
      st.caption("Loose wires from underground power lines and street lamps, and broken/removed sewage covers, make the pathways almost impossible to navigate for individuals with disabilities and can be fatal during rainy weather.")
      st.image("data/survey3.jpg", use_container_width=True)

    with colb:
      st.image("data/survey5.jpg", use_container_width=True)
      st.caption("Garbage dumps, wrongly placed streetlamps, and encroachment by street vendors make the footpaths almost inaccessible to persons with disabilities.")
      st.image("data/survey6.jpg", use_container_width=True)

    with colc:
      st.image("data/survey7.jpg", use_container_width=True)
      st.image("data/survey8.jpg", use_container_width=True)
      st.image("data/survey9.jpg", use_container_width=True)

    st.markdown("---")

    # --- MOTIVATION PARAGRAPH ---
    st.header("Why We Planned to Do")
    st.markdown("""
    When we complain about bad footpaths, it is often dismissed as a minor inconvenience. However, for a 
    commuter, a broken drain or an encroachment is a physical barrier that demands extra energy and steals 
    precious time. We use physics because it provides an objective way to measure this struggle. 

    By treating a pedestrian as an 'agent' moving through a 'force field' of obstacles, we can calculate exactly 
    how much extra work your body has to do. Whether you are an engineer or a daily commuter, you know that 
    walking through a crowd or over debris is exhausting. Our mathematical framework simply captures that 
    exhaustion and turns it into hard data that the government can use to justify repairs.
    """)

    # --- THE MATHEMATICAL FRAMEWORK ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### The Effective Path Length: Measuring the 'Felt' Distance")
        st.markdown("""
        If a road is smooth, a 900m walk feels like 900m. But if the road is filled with obstacles, your body 
        spends so much energy navigating them that the walk 'feels' much longer. We call this the **Effective 
        Path Length**. It is calculated by summing up the difficulty (friction) of every small segment of the road.
        """)
        st.latex(r"L_{\text{eff}}(\phi) = \int_0^D f(x, \phi)\, dx \;\approx\; d\sum_{i=1}^{N} f_i(\phi)")
        st.latex(r"""
            \begin{aligned}
            L_{\text{eff}} &: \text{Effective Path Length (the 'felt' distance in terms of physical effort)} \\
            \phi &: \text{The Commuter Persona (adjusts difficulty based on specific mobility needs)} \\
            D &: \text{The total physical distance of the corridor measured on a map (900 meters)} \\
            f(x, \phi) &: \text{The Local Friction Index at position } x \text{ (1 = Perfect, 5 = Impassable)} \\
            dx &: \text{An infinitesimal change in position along the corridor length} \\
            d &: \text{The fixed length of each audited block (12.5 meters in our study)} \\
            i &: \text{The index representing each specific segment from the first to the last} \\
            N &: \text{The total number of 12.5m segments surveyed (72 segments for 900m)} \\
            f_i(\phi) &: \text{The specific friction value recorded for the } i\text{-th segment}
            \end{aligned}
        """)

        st.markdown("#### Power-Law Velocity and the Time Tax")
        st.markdown("""
        Bad roads don't just slow you down; they penalize you. We use a 'Power-Law' to show that as the road 
        gets worse, your speed drops exponentially. The **Time Tax** is the total amount of life-minutes the 
        infrastructure 'steals' from you compared to a perfect, unobstructed walk.
        """)
        st.latex(r"v_{\text{eff}}(i, \phi) = \frac{v_0(\phi)}{f_i^{k(\phi)}} \implies \Delta\tau(\phi) = \frac{d}{v_0(\phi)} \left( \sum_{i=1}^{N} f_i^{k(\phi)} - N \right)")
        st.latex(r"""
            \begin{aligned}
            v_{\text{eff}} &: \text{Actual velocity achieved by persona } \phi \text{ across segment } i \\
            v_0 &: \text{The 'Ideal' speed of a persona on a perfect, standard-compliant footpath} \\
            k &: \text{Friction Sensitivity (how much the persona's speed is impacted by broken ground)} \\
            \Delta\tau &: \text{The Time Tax (the cumulative seconds of life-time stolen per trip)} \\
            f_i^{k} &: \text{The local friction raised to the sensitivity power of the commuter} \\
            \sum_{i=1}^{N} &: \text{The sum of all travel times across every individual segment } i
            \end{aligned}
        """)

        st.markdown("#### Macro-Economic Aggregation")
        st.markdown("""
        When 100,000 people lose a few minutes every day, those minutes add up to years of lost life. We 
        calculate the total economic value of this wasted time by looking at the average daily wage in 
        Bengaluru. This proves that a 'walking problem' is actually a 'money problem' for the city.
        """)
        st.latex(r"\mathcal{T}_{\text{year}} = M \cdot W \cdot \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi} \cdot \text{WAGE}")
        st.latex(r"""
            \begin{aligned}
            \mathcal{T}_{\text{year}} &: \text{Total annual economic productivity loss for the city in INR} \\
            M &: \text{The total number of people who walk this path every day (100,000)} \\
            W &: \text{Standardized working days per year (250 days)} \\
            w_\phi &: \text{The percentage weight of each persona in the total pedestrian population} \\
            \Delta\tau(\phi) &: \text{The calculated Time Tax for that specific group of people (in mins)} \\
            \sum w_\phi &: \text{The sum of all population weights (ensuring the average is balanced)} \\
            \text{WAGE} &: \text{Economic value of time (RBI Informal Rate } \approx \text{ ₹0.83/min)}
            \end{aligned}
        """)

    st.markdown("---")

    # --- MODULE OVERVIEW (Numbered List) ---
    st.header("Audit Modules")
    st.markdown("The app contains the following modules for users to visualise the current state of the route and simulate how it would approximately look after fixes:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown("#### 📍 Friction Mapper")
        st.write("* **Geotagged Database:** An interactive map of 24 specific infrastructure failures with precise coordinates.")
        st.write("* **Zonal Analysis:** Differentiates the 600m Bazaar Street failure zone from the Constitution Circle stretch.")
        st.write("* **Evidence Export:** Links technical friction indices to photographic logs and timestamps from the audit.")

        st.markdown("#### ⏳ Time Tax Simulator")
        st.write("* **Human Journeys:** Runs persona-specific simulations to show how individuals move through the audit zone.")
        st.write("* **Equity Gap:** Quantifies the disproportionate burden placed on the elderly and disabled by broken ground.")
        st.write("* **Danger Tracking:** Calculates the risk when pedestrians are forced into the road to avoid obstacles.")

    with m_col2:
        st.markdown("#### 🏗️ What-If: Lighthouse Prototype")
        st.write("* **3D Engineering View:** A static 3D cross-section of a 20-30m segment redesigned to Tender S.U.R.E. standards.")
        st.write("* **Streets of Hope:** Visualizes a 3m wide clear path, flush drainage, and kerb ramps, shown as different perspective shots of the CAD design.")
        st.write("* **Blueprint Spec:** Provides a measurable visual for policymakers to understand exactly what a 'fix' looks like.")

        st.markdown("#### 💰 Economic Impact")
        st.write("* **Monetary Valuation:** Converts lost seconds into Crore-value figures based on benchmarked wage rates.")
        st.write("* **Spending Strategy:** Demonstrates the 10:1 return on investment for targeted municipal repairs.")
        st.write("* **Policy Ready:** Synthesizes data into the specific formats required for government budget approval.")

    st.info("👈 **Please select a module from the sidebar to begin. Every second counts!**")

    st.caption(
        "Developed for [Bengawalk](https://bengawalk.com) · YLAC Mobility Champions 2026"
    )

else:
    if page in modules:
        st.title(page)
        modules[page].app()
    else:
        st.title(page)
        st.info("This module is under development. Check back soon.")
