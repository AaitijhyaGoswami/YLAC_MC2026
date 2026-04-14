import streamlit as st
import pandas as pd
import os

def app():
    st.write("### 📸 Spatial Audit: Visualizing the Yeshwantpur Fix")
    st.markdown("""
    While 3D models provide depth, these high-fidelity renders show the 
    **S.U.R.E. Standard** transformation of the 16m Bazaar Street section.
    """)
    st.markdown("---")

    # --- IMAGE COMPARISON ---
    col_current, col_fixed = st.columns(2)

    # Note: Using absolute path based on the file location
    path = os.path.dirname(__file__)

    with col_current:
        st.subheader("Current (f=5)")
        st.image(f"cad_viewer/f=5.png", caption="Systemic Failure: Wall & Mesh Containment")
        with st.expander("Diagnostics"):
            st.error("Pedestrians piped into traffic due to 1.6m high barriers.")

    with col_fixed:
        st.subheader("Proposed (f=1)")
        st.image(f"cad_viewer/f=1.png", caption="Gold Standard: 3m Reclaimed Path")
        with st.expander("Remediation"):
            st.success("Unobstructed flow restored; vending integrated into utility zone.")

    st.markdown("---")

    # --- SPATIAL ALLOCATION TABLE ---
    st.header("📊 Spatial Allocation Table")
    comparison_df = pd.DataFrame({
        "Element": ["Pedestrian Path", "Vending Zone", "Barriers"],
        "Current ($f=5$)": ["0.0 m", "3.0 m (Encroached)", "1.6m Wall/Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "None"]
    })
    st.table(comparison_df)

    # --- MATH JUSTIFICATION ---
    with st.expander("View Mathematical Justification"):
        st.latex(r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}")
        st.write("Removing the 'piping' barriers restores the effective width and drops the Friction Index.")
