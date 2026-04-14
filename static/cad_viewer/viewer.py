import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# 3D RENDER ENGINE (HTML/JS)
# -------------------------------------------------------------------------

def render_3d_model(model_url, label, color):
    """
    Standardized 3D viewer component using Google's <model-viewer>.
    Relative pathing assumes files are in ylac_mc2026/static/cad_viewer/
    """
    html_code = f"""
    <div style="font-family: 'Inter', sans-serif; text-align: center;">
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
# MAIN MODULE ENTRY POINT (Called by app.py)
# -------------------------------------------------------------------------

def app():
    # Note: We don't use st.title() here because app.py handles it
    st.markdown("""
    This interactive audit visualizes the 16m Bazaar Street cross-section. 
    By comparing the current 'Caged' infrastructure with the proposed hierarchy, 
    we demonstrate how spatial reorganization eliminates the modal conflict 
    recorded in the **Friction Mapper**.
    """)
    st.markdown("---")

    # --- 1. SIDE-BY-SIDE 3D VIEWERS ---
    col_f5, col_f1 = st.columns(2)

    # Pathing: With enableStaticServing, ylac_mc2026/static/ is the root (/)
    with col_f5:
        render_3d_model(
            model_url="cad_viewer/yeshu.gltf", 
            label="Current: Systemic Failure (f=5)", 
            color="#F44336"
        )
        with st.expander("Spatial Diagnostics (Current)"):
            st.error("**Piping Effect:** 1.6m barriers (base + mesh) trap pedestrians in the shared 3m lane.")
            st.error("**Encroachment:** 3m footpaths are 100% occupied by unregulated vendor geometries.")

    with col_f1:
        render_3d_model(
            model_url="cad_viewer/f=1.gltf", 
            label="Proposed: Gold Standard (f=1)", 
            color="#00D4FF"
        )
        with st.expander("Remediation Strategy (Redesign)"):
            st.success("**Reclaimed Capacity:** Unobstructed 3m clear path restored for pedestrians.")
            st.success("**Integrated Vending:** Vendors moved to a 1.5m curb-side utility zone.")

    st.markdown("---")

    # --- 2. BRIEFING FUNCTIONALITY (DETAILED) ---
    st.header("🛠️ Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of 100,000 daily commuters, it anchors policy arguments in a Crore-value productivity loss figure that represents the literal economic cost of systemic infrastructure neglect.")
    st.write("2. **Strategic Investment Prioritization:** The tool identifies the non-linear returns on infrastructure spending. It demonstrates that a targeted 'Lighthouse Pilot'—fixing just the top three nodes—recovers nearly 40% of the total potential economic benefit, allowing municipal planners to achieve maximum impact with minimal capital expenditure.")
    st.write("3. **Equity-Weighted Productivity Valuation:** By utilizing population share weights ($w_{\phi}$), the model ensures that the fiscal drain on the city’s most essential workers—delivery partners and daily laborers—is not erased by 'average' walking speeds. It frames universal design as an economic imperative rather than just a social welfare goal.")
    st.write("4. **Standardized Proposal Synthesis:** Every metric and visualization is formatted for direct extraction into DULT or BBMP project approval templates. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' mathematical justification for immediate intervention, moving the conversation from anecdotal complaints to data-driven governance.")

    st.markdown("---")

    # --- 3. TECHNICAL METHODOLOGY ---
    with st.expander("View Technical Methodology and Mathematical Definitions"):
        st.markdown("#### Variable Definitions")
        st.latex(r"""
            \begin{aligned}
            f_i &: \text{Friction Index of segment } i \\
            v_0(\phi) &: \text{Free-walking speed of persona } \phi \text{ (m/s)} \\
            \Delta\tau(\phi) &: \text{Time Tax (Seconds stolen per trip)} \\
            \mathcal{L} &: \text{Annual Economic Productivity Loss (Crore INR)}
            \end{aligned}
        """)

        st.markdown("#### Worked Unit Example: The Cost of One Failed Node")
        st.latex(r"""
            \begin{aligned}
            \text{Input: } & v_0 = 1.4 \text{ m/s, } k = 0.6, \text{ } f=5 \\
            \tau_{\text{ideal}} &= 12.5 / 1.4 = 8.93\text{s} \\
            v_{\text{eff}} &= 1.4 / 5^{0.6} \approx 0.533\text{ m/s} \\
            \Delta\tau (\phi_A) &= (12.5 / 0.533) - 8.93 \approx 14.52\text{s} \\
            \text{Annual Loss} &\approx ₹22.6\text{ Lakhs per node}
            \end{aligned}
        """)

    # --- 4. SPATIAL ALLOCATION COMPARISON ---
    st.header("📊 Spatial Allocation Table (16m Section)")
    comparison_df = pd.DataFrame({
        "Infrastructure Element": ["Pedestrian Clear Path", "Vending/Utility Zone", "Vehicle Carriageway", "Segregation Barrier"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Encroached)", "10.0 m (Piped)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m", "1.5 m (Organized)", "7.0 m (Standardized)", "None (Open Hierarchy)"]
    })
    st.table(comparison_df)
