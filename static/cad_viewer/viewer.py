import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# -------------------------------------------------------------------------
# 3D RENDER ENGINE (glTF + Binary)
# -------------------------------------------------------------------------

def render_3d_model(model_url, label, color):
    """
    Renders the 3D model. 
    Streamlit serves 'static/' at the root, so the path is just 'cad_viewer/...'
    """
    html_code = f"""
    <div style="font-family: 'Inter', sans-serif; text-align: center;">
        <h4 style="color: {color}; margin-bottom: 15px; font-weight: 600;">{label}</h4>
        
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        
        <model-viewer src="{model_url}" 
                      style="width: 100%; height: 500px; background-color: #0e1117; border-radius: 15px; border: 1px solid #333;" 
                      auto-rotate 
                      camera-controls 
                      shadow-intensity="2" 
                      exposure="1.2" 
                      environment-image="neutral">
            <div slot="progress-bar" style="height: 5px; background-color: {color};"></div>
        </model-viewer>
    </div>
    """
    return components.html(html_code, height=580)

# -------------------------------------------------------------------------
# MAIN MODULE ENTRY POINT
# -------------------------------------------------------------------------

def app():
    st.write("### 🏗️ Lighthouse Prototype: Yeshwantpur Corridor")
    st.write("Compare the current containment geometry ($f=5$) with the proposed hierarchy ($f=1$).")
    st.markdown("---")

    col_f5, col_f1 = st.columns(2)

    # UPDATED PATHS: Assumes files are in static/cad_viewer/
    with col_f5:
        render_3d_model(
            model_url="cad_viewer/yeshwantpur.gltf", 
            label="Current Situation (f=5)", 
            color="#FF4B4B"
        )

    with col_f1:
        render_3d_model(
            model_url="cad_viewer/f=1.gltf", 
            label="Proposed Redesign (f=1)", 
            color="#00D4FF"
        )

    st.markdown("---")

    # --- BRIEFING & TABLE ---
    st.header("📊 Spatial Allocation Comparison")
    
    comparison_df = pd.DataFrame({
        "Element": ["Pedestrian Path", "Vending Zone", "Barriers"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Colonized)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "None"]
    })
    st.table(comparison_df)

    with st.expander("View Mathematical Justification"):
        st.latex(r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}")
        st.write("By removing the mesh-wall 'pipe', we increase the effective width for pedestrians.")
