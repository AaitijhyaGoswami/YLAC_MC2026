import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# 3D RENDER ENGINE (HTML/JS)
# -------------------------------------------------------------------------

def render_3d_model(model_url, label, color):
    """
    Standardized 3D viewer component using Google's <model-viewer>.
    Optimized for rotatable, interactive binary GLB files.
    """
    html_code = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center;">
        <h4 style="color: {color}; margin-bottom: 12px; font-weight: 500; letter-spacing: 0.5px;">{label}</h4>
        
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        
        <model-viewer src="{model_url}" 
                      style="width: 100%; height: 500px; background-color: #111111; border-radius: 12px; border: 1px solid #333;" 
                      auto-rotate 
                      camera-controls 
                      shadow-intensity="2" 
                      exposure="1.2" 
                      environment-image="neutral"
                      interaction-prompt="auto"
                      ar>
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
    This interactive audit visualizes the 16m cross-section of the Bazaar Street stretch. 
    Observe how the removal of the **half-wall / half-mesh** caging and the reclamation 
    of footpath space eliminates the modal conflict recorded in the **Friction Mapper**.
    """)
    st.markdown("---")

    # --- 1. SIDE-BY-SIDE 3D VIEWER ---
    col_f5, col_f1 = st.columns(2)

    # Note: Ensure .streamlit/config.toml has enableStaticServing = true
    with col_f5:
        render_3d_model(
            model_url="app/static/cad_viewer/current_f5.glb", 
            label="Current: Systemic Failure (f=5)", 
            color="#F44336"
        )
        with st.expander("Spatial Diagnostics (Current)"):
            st.error("**Piping Effect:** The 1.6m high barriers (base + mesh) trap pedestrians in the shared 3m lane.")
            st.error("**Total Encroachment:** Footpaths are 100% colonized by vendor stalls.")

    with col_f1:
        render_3d_model(
            model_url="app/static/cad_viewer/yeshwantpur_section.glb", 
            label="Proposed: Gold Standard (f=1)", 
            color="#4CAF50"
        )
        with st.expander("Remediation Strategy (Redesign)"):
            st.success("**Reclaimed Capacity:** Unobstructed 3m clear path restored for pedestrians.")
            st.success("**Integrated Ecosystem:** Vending moved to a 1.5m curb-side utility zone.")

    st.markdown("---")

    # --- 2. BRIEFING FUNCTIONALITY (DETAILED) ---
    st.header("🛠️ Briefing Functionality")
    st.write("1. **Macro-Economic Aggregation:** This module converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of 100,000 daily commuters, it anchors policy arguments in a Crore-value productivity loss figure that represents the literal economic cost of systemic infrastructure neglect.")
    st.write("2. **Strategic Investment Prioritization:** The tool identifies the non-linear returns on infrastructure spending. It demonstrates that a targeted 'Lighthouse Pilot'—fixing just the top three nodes—recovers nearly 40% of the total potential economic benefit, allowing municipal planners to achieve maximum impact with minimal capital expenditure.")
    st.write("3. **Equity-Weighted Productivity Valuation:** By utilizing population share weights ($w_\\phi$), the model ensures that the fiscal drain on the city’s most essential workers—delivery partners and daily laborers—is not erased by 'average' walking speeds. It frames universal design as an economic imperative rather than just a social welfare goal.")
    st.write("4. **Standardized Proposal Synthesis:** Every metric and visualization is formatted for direct extraction into DULT or BBMP project approval templates. The 10:1 Benefit-Cost Ratio provides a 'bulletproof' mathematical justification for immediate intervention, moving the conversation from anecdotal complaints to data-driven governance.")

    st.markdown("---")

    # --- 3. SPATIAL ALLOCATION COMPARISON ---
    st.header("📊 Spatial Allocation Comparison (16m)")
    
    comparison_df = pd.DataFrame({
        "Infrastructure Element": ["Pedestrian Clear Path", "Vending/Utility Zone", "Vehicle Carriageway", "Segregation Barrier"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Colonized)", "10.0 m (Piped)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "7.0 m (Unified)", "None (Open Hierarchy)"]
    })
    st.table(comparison_df)

    # Physics note
    st.write("**Physics Note on Spatial Resistance:**")
    st.latex(r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}")
    st.write("""
        The half-wall and caging impose a psychological buffer zone that further reduces effective width ($W_{\text{eff}}$), 
        forcing pedestrians into vehicular space. Remediation restores this width, lowering the Friction Index.
    """)
