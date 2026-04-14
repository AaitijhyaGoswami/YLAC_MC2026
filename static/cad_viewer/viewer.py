import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

# --- 3D RENDER ENGINE ---
def render_3d_model(model_url, label, color):
    """
    Standardized 3D viewer component.
    NOTE: Using relative paths that assume files are in the 'static/' directory.
    """
    html_code = f"""
    <div style="font-family: 'Inter', sans-serif; text-align: center;">
        <h4 style="color: {color}; margin-bottom: 12px; font-weight: 500;">{label}</h4>
        <script type="module" src="https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js"></script>
        <model-viewer src="{model_url}" 
                      style="width: 100%; height: 500px; background-color: #0e1117; border-radius: 12px;" 
                      auto-rotate camera-controls shadow-intensity="2" exposure="1.2">
        </model-viewer>
    </div>
    """
    return components.html(html_code, height=560)

def app():
    st.header("📦 3D Spatial Audit: Bazaar Street")
    st.write("Visualizing the 16m cross-section to contrast Systemic Failure with Gold Standard designs.")
    st.markdown("---")

    col_f5, col_f1 = st.columns(2)

    # UPDATED PATHS: Assumes files are in static/cad_viewer/
    with col_f5:
        render_3d_model(
            model_url="cad_viewer/yeshwantpur.gltf", 
            label="Current: Systemic Failure (f=5)", 
            color="#F44336"
        )

    with col_f1:
        render_3d_model(
            model_url="cad_viewer/fixed.gltf", 
            label="Proposed: Gold Standard (f=1)", 
            color="#00D4FF"
        )

    st.markdown("---")

    # --- BRIEFING POINTERS ---
    st.header("🛠️ Briefing Functionality")
    st.write(r"1. **Macro-Economic Aggregation:** Converts 'pedestrian struggle' into fiscal metrics by scaling persona-weighted time loss.")
    st.write(r"2. **Strategic Investment:** Shows that fixing top-N nodes recovers ~40% of the total potential economic benefit.")
    
    # --- MATH SECTION (Using Raw Strings to prevent SyntaxWarnings) ---
    with st.expander("View Technical Methodology"):
        st.latex(r"""
            \begin{aligned}
            \bar{\Delta\tau} &= \frac{\sum w_\phi \Delta\tau(\phi)}{\sum w_\phi} \\
            \mathcal{L} &= M \cdot W \cdot \frac{\bar{\Delta\tau}}{60} \cdot \text{WAGE} \cdot 10^{-7}
            \end{aligned}
        """)

    # --- COMPARISON TABLE ---
    st.table(pd.DataFrame({
        "Element": ["Clear Path", "Vending Zone", "Barrier"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Encroached)", "Wall + Mesh"],
        "Proposed ($f=1$)": ["3.0 m", "1.5 m (Integrated)", "None"]
    }))
