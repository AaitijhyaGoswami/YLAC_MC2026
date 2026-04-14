import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# 3D RENDER ENGINE (glTF Support)
# -------------------------------------------------------------------------

def render_3d_model(model_url, label, color):
    """
    Standardized 3D viewer component using Google's <model-viewer>.
    Optimized for .gltf + .bin split configurations.
    """
    html_code = f"""
    <div style="font-family: 'Inter', system-ui, sans-serif; text-align: center;">
        <h4 style="color: {color}; margin-bottom: 12px; font-weight: 500; letter-spacing: 0.5px;">{label}</h4>
        
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        
        <model-viewer src="{model_url}" 
                      style="width: 100%; height: 500px; background-color: #0e1117; border-radius: 12px; border: 1px solid #333;" 
                      auto-rotate 
                      camera-controls 
                      shadow-intensity="2" 
                      exposure="1.2" 
                      environment-image="neutral"
                      interaction-prompt="auto">
            <div slot="progress-bar" style="height: 4px; background-color: {color};"></div>
        </model-viewer>
    </div>
    """
    return components.html(html_code, height=560)

# -------------------------------------------------------------------------
# MAIN MODULE ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.header("📦 3D Spatial Audit: Bazaar Street")
    st.markdown("""
    This interactive audit visualizes the 16m Bazaar Street cross-section. 
    By contrasting the current 'Containment' geometry with the proposed hierarchy, 
    we demonstrate the physical removal of modal friction in the **Friction Mapper**.
    """)
    st.markdown("---")

    # --- 1. SIDE-BY-SIDE 3D VIEWERS ---
    col_f5, col_f1 = st.columns(2)

    # Note: Static serving via .streamlit/config.toml is REQUIRED.
    # Paths point to your .gltf files; associated .bin files must be in the same folder.
    
    with col_f5:
        render_3d_model(
            model_url="app/static/cad_viewer/yeshwantpur.gltf", 
            label="Current: Systemic Failure (f=5)", 
            color="#F44336"
        )
        with st.expander("Spatial Diagnostics (Audit Data)"):
            st.error("**Containment Effect:** 1.6m half-wall/mesh cage traps pedestrians in a shared 3m lane.")
            st.error("**Colonization:** 3m footpaths are 100% occupied by unregulated vendor geometries.")

    with col_f1:
        render_3d_model(
            model_url="app/static/cad_viewer/fixed.gltf", 
            label="Proposed: Gold Standard (f=1)", 
            color="#00D4FF"
        )
        with st.expander("Remediation Strategy (Lighthouse Pilot)"):
            st.success("**Reclaimed Path:** Restoration of a continuous 3m unobstructed concrete walking zone.")
            st.success("**Integrated Ecosystem:** Vending moved to a 1.5m curb-side utility zone.")

    st.markdown("---")

    # --- 2. DETAILED BRIEFING FUNCTIONALITY ---
    st.header("🛠️ Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of 100,000 daily commuters, it anchors policy arguments in a Crore-value productivity loss figure that represents the literal economic cost of systemic infrastructure neglect.")
    st.write("2. **Strategic Investment Prioritization:** The tool identifies the non-linear returns on infrastructure spending. It demonstrates that a targeted 'Lighthouse Pilot'—fixing just the top three nodes—recovers nearly 40% of the total potential economic benefit, allowing municipal planners to achieve maximum impact with minimal capital expenditure.")
    st.write("3. **Equity-Weighted Productivity Valuation:** By utilizing population share weights ($w_\\phi$), the model ensures that the fiscal drain on the city’s most essential workers—delivery partners and daily laborers—is not erased by 'average' walking speeds. It frames universal design as an economic imperative rather than just a social welfare goal.")
    st.write("4. **Standardized Proposal Synthesis:** Every metric and visualization is formatted for direct extraction into DULT or BBMP project approval templates. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' mathematical justification for immediate intervention, moving the conversation from anecdotal complaints to data-driven governance.")

    st.markdown("---")

    # --- 3. TECHNICAL METHODOLOGY (MATH & VARIABLES) ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Variable Definitions")
        st.latex(r"""
            \begin{aligned}
            f_i &: \text{Friction Index of segment } i \text{ (Discrete nodes or Bazaar St)} \\
            v_0(\phi) &: \text{Free-walking speed of persona } \phi \text{ (Standardized m/s)} \\
            k(\phi) &: \text{Sensitivity exponent for persona } \phi \text{ (Rate of velocity decay)} \\
            \Delta\tau(\phi) &: \text{Time Tax (Seconds stolen per trip) for a single persona} \\
            M &: \text{Daily Hub Volume (100,000 commuters at Yeshwantpur hub)} \\
            W &: \text{Annual Cycle (250 standardized working days per year)} \\
            \text{WAGE} &: \text{Economic value of time (RBI Informal rate } \approx \text{ ₹0.83/min)} \\
            \mathcal{L} &: \text{Annual Economic Productivity Loss (Expressed in Crore INR)}
            \end{aligned}
        """)

        st.markdown("#### Traversal & Fiscal Derivation")
        st.latex(r"""
            \begin{aligned}
            \tau_i(\phi) &= \begin{cases} \frac{d \cdot f_i^{k(\phi)}}{v_0(\phi)} & f_i \leq f_{\max} \\ \frac{(d+\delta)\alpha}{v_0(\phi)} & f_i > f_{\max} \end{cases} \\
            \bar{\Delta\tau} &= \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi} \\
            \mathcal{L} &= M \cdot W \cdot \frac{\bar{\Delta\tau}}{60} \cdot \text{WAGE} \cdot 10^{-7}
            \end{aligned}
        """)

        st.markdown("#### Worked Unit Example: The Cost of One Failed Node")
        st.latex(r"""
            \begin{aligned}
            \text{Input: } & v_0 = 1.4 \text{ m/s, } k = 0.6, \text{ } w_A = 0.45, \text{ } f=5 \\
            \tau_{\text{ideal}} &= 12.5 / 1.4 = 8.93\text{s} \\
            v_{\text{eff}} &= 1.4 / 5^{0.6} \approx 0.533\text{ m/s} \\
            \Delta\tau (\phi_A) &= (12.5 / 0.533) - 8.93 \approx 14.52\text{s} \\
            \text{Loss} &= (45,000 \cdot 250 \cdot 0.242\text{ min}) \cdot ₹0.833 \approx ₹22.6\text{ Lakhs/yr}
            \end{aligned}
        """)

    st.markdown("---")

    # --- 4. SPATIAL ALLOCATION TABLE ---
    st.header("📊 Spatial Allocation Table (16m Section)")
    comparison_df = pd.DataFrame({
        "Infrastructure Element": ["Pedestrian Clear Path", "Vending/Utility Zone", "Vehicle Carriageway", "Segregation Barrier"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Encroached)", "10.0 m (Piped)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "7.0 m (Standardized)", "None (Open Hierarchy)"]
    })
    st.table(comparison_df)
