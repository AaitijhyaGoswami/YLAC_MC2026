import streamlit as st
import pandas as pd
import os

def app():
    # --- EXECUTIVE HEADER ---
    st.write("## 🏗️ Lighthouse Prototype: Yeshwantpur-Mathikere Nexus")
    st.markdown("""
    **Objective:** This module provides a high-fidelity visual and mathematical audit of the 16m Bazaar Street 
    cross-section. It contrasts the current 'Containment' model with the **S.U.R.E. Standard** hierarchy.
    """)
    st.info("💡 **Advocacy Goal:** Use this module to demonstrate that removing barriers is an economic recovery strategy, not just a beautification project.")
    st.markdown("---")

    # --- 1. SPATIAL VISUALIZATION ---
    col_current, col_fixed = st.columns(2)

    with col_current:
        st.subheader("Current: Systemic Failure ($f=5$)")
        # Path kept exactly as requested
        st.image(f"cad_viewer/f=5.png", caption="Systemic Failure: Wall & Mesh Containment", use_container_width=True)
        
        with st.expander("🚨 Spatial Diagnostics (Audit Log)"):
            st.error("**The Piping Effect:** 1.6m high barriers (base wall + mesh) create a high-pressure friction corridor.")
            st.error("**Colonization:** 3m existing footpaths are 100% occupied; pedestrians are physically 'piped' into vehicular traffic.")

    with col_fixed:
        st.subheader("Proposed: Gold Standard ($f=1$)")
        # Path kept exactly as requested
        st.image(f"cad_viewer/f=1.png", caption="Gold Standard: 3m Reclaimed Path", use_container_width=True)
        
        with st.expander("✅ Remediation Strategy (Redesign)"):
            st.success("**Reclaimed Clear Path:** Restoration of a continuous 3m unobstructed concrete walking zone.")
            st.success("**Integrated Ecosystem:** Vending shifted to a 1.5m curb-side 'Utility Zone' with organized stalls.")

    st.markdown("---")

    # --- 2. POLICY & ADVOCACY POINTERS ---
    st.header("🛠️ Briefing Functionality")
    
    st.markdown(r"""
    1. **Macro-Economic Aggregation:** This design converts abstract 'pedestrian struggle' into a high-fidelity fiscal baseline. By scaling persona-weighted time loss against a hub volume of **100,000 daily commuters**, we anchor the argument in a **Crore-value productivity gain**.
    
    2. **Strategic Investment Prioritization:** The 'Lighthouse' approach identifies non-linear returns on spending. Remediation of this specific high-friction node (Bazaar St) recovers nearly **38% of the total potential economic benefit** of the entire corridor.
    
    3. **Equity-Weighted Productivity Valuation:** Using population share weights ($w_\phi$), the model ensures the fiscal drain on the city’s essential workers—delivery partners and daily laborers—is central to the design. Universal Design is presented as an economic imperative.
    
    4. **Standardized Proposal Synthesis:** Every metric is formatted for direct extraction into DULT or BBMP project approval templates. The **10:1 Benefit-Cost Ratio** provides the mathematical justification for immediate intervention.
    """)

    st.markdown("---")

    # --- 3. SPATIAL ALLOCATION TABLE ---
    st.header("📊 Spatial Allocation Comparison (16m Section)")
    
    comparison_df = pd.DataFrame({
        "Infrastructure Element": ["Pedestrian Clear Path", "Vending/Utility Zone", "Vehicle Carriageway", "Segregation Barrier"],
        "Current ($f=5$)": ["0.0 m (None)", "3.0 m (Encroached)", "10.0 m (Piped)", "800mm Wall + 800mm Mesh"],
        "Proposed ($f=1$)": ["3.0 m (Clear)", "1.5 m (Integrated)", "7.0 m (Standardized)", "None (Open Hierarchy)"]
    })
    st.table(comparison_df)

    # --- 4. MATHEMATICAL JUSTIFICATION ---
    with st.expander("🔬 View Physics Logic & Variable Definitions"):
        st.markdown("#### The Physics of Spatial Resistance")
        st.latex(r"W_{\text{eff}} = W_{\text{total}} - W_{\text{obstacles}} - W_{\text{buffer}}")
        st.write("""
            The half-wall and mesh cage impose a psychological 'Buffer Zone' ($W_{\text{buffer}}$) that further reduces 
            effective width. Pedestrians avoid walking close to the jagged mesh, effectively narrowing the 3m lane 
            even further. Remediation restores this width and eliminates the resistive force.
        """)
        
        st.markdown("#### Velocity Decay Function")
        st.latex(r"v_{\text{eff}} = \frac{v_0}{f^k}")
        st.write("""
            By moving from $f=5$ to $f=1$, we restore the pedestrian velocity ($v_{\text{eff}}$) to the free-flow 
            standard ($v_0$), eliminating the Time Tax recorded in the simulator.
        """)

    st.markdown("---")
    st.caption("Developed for YLAC Mobility Champions 2026 | Yeshwantpur Nexus Audit")
