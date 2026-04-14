import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# 3D RENDER ENGINE (glTF / .glif Support)
# -------------------------------------------------------------------------

def render_3d_model(model_url, label, color):
    """
    Injects a high-performance 3D viewer using Google's <model-viewer>.
    Optimized for .glif (JSON) + .bin (Binary) split configurations.
    """
    html_code = f"""
    <div style="font-family: 'Inter', system-ui, sans-serif; text-align: center;">
        <h4 style="color: {color}; margin-bottom: 15px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{label}</h4>
        
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        
        <model-viewer src="{model_url}" 
                      style="width: 100%; height: 500px; background-color: #0e1117; border-radius: 15px; border: 2px solid #262730;" 
                      auto-rotate 
                      camera-controls 
                      shadow-intensity="2" 
                      exposure="1.2" 
                      environment-image="neutral"
                      interaction-prompt="auto">
            <div slot="progress-bar" style="height: 5px; background-color: {color};"></div>
        </model-viewer>
    </div>
    """
    return components.html(html_code, height=580)

# -------------------------------------------------------------------------
# MAIN MODULE ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.header("📦 3D Spatial Audit: Bazaar Street Corridor")
    st.write(
        "This interactive module visualizes the 16m cross-section of Bazaar Street. "
        "By contrasting the current 'containment' geometry with our proposed hierarchy, "
        "we demonstrate the physical removal of modal friction."
    )
    st.markdown("---")

    # --- 1. SIDE-BY-SIDE 3D COMPARISON ---
    col_f5, col_f1 = st.columns(2)

    # NOTE: Relative paths work via Streamlit's Static Serving.
    # yeshwantpur.glif (+ .bin) -> Current State
    # fixed.glif (+ .bin) -> Proposed State
    
    with col_f5:
        render_3d_model(
            model_url="app/static/cad_viewer/yeshwantpur.glif", 
            label="Current: Systemic Failure (f=5)", 
            color="#FF4B4B"
        )
        with st.expander("Spatial Diagnostics (Audit Log)"):
            st.error("**Piping Effect:** The 1.6m half-wall/mesh barrier traps pedestrians in a high-pressure shared lane.")
            st.error("**Footpath Colonization:** 3m existing footpaths are 100% occupied by unregulated vendor structures.")

    with col_f1:
        render_3d_model(
            model_url="app/static/cad_viewer/fixed.glif", 
            label="Proposed: Gold Standard (f=1)", 
            color="#00D4FF"
        )
        with st.expander("Remediation Strategy (Lighthouse Pilot)"):
            st.success("**Reclaimed Clear Path:** Restoration of a continuous 3m unobstructed concrete walking zone.")
            st.success("**Integrated Ecosystem:** Vending shifted to a 1.5m curb-side utility zone with organized stalls.")

    st.markdown("---")

    # --- 2. DETAILED BRIEFING FUNCTIONALITY ---
    st.header("🛠️ Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of 100,000 daily commuters, it anchors policy arguments in a Crore-value productivity loss figure that represents the literal economic cost of systemic infrastructure neglect.")
    st.write("2. **Strategic Investment Prioritization:** The tool identifies the non-linear returns on infrastructure spending. It demonstrates that a targeted 'Lighthouse Pilot'—fixing just the top three nodes—recovers nearly 40% of the total potential economic benefit, allowing municipal planners to achieve maximum impact with minimal capital expenditure.")
    st.write("3. **Equity-Weighted Productivity Valuation:** By utilizing population share weights ($w_{\phi}$), the model ensures that the fiscal drain on the city’s most essential workers—delivery partners and daily laborers—is not erased by 'average' walking speeds. It frames universal design as an economic imperative rather than just a social welfare goal.")
    st.write("4. **Standardized Proposal Synthesis:** Every metric and visualization is formatted for direct extraction into DULT or BBMP project approval templates. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' mathematical justification for immediate intervention, moving the conversation from anecdotal complaints to data-driven governance.")

    st.markdown("---")

    # --- 3. SPATIAL ALLOCATION TABLE & PHYSICS ---
    st.header("📊 Spatial Allocation Comparison (16m Section)")
    
    comparison_df = pd.DataFrame({
        "Infrastructure Element": ["Pedestrian Clear Path", "Vending/Utility Zone", "Vehicle Carriageway", "Segregation Method"],
        "Current ($f=5$)": ["0.0 m (None)", "3.0 m (Colonized)", "10.0 m (Piped)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "7.0 m (Standardized)", "None (Open Hierarchy)"]
    })
    st.table(comparison_df)

    st.markdown("---")
    st.markdown("#### Physics of Spatial Resistance")
    st.latex(r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}")
    st.write(
        "In the current state, the half-wall/mesh cage imposes a psychological buffer zone that further reduces "
        "effective width. By removing these barriers, we restore the corridor's flow capacity, directly "
        "lowering the Friction Index."
    )
