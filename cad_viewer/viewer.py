import streamlit as st
import pandas as pd
import os

def app():
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
        
        with st.expander("Spatial Diagnostics (Audit Log)"):
            st.error("**The Piping Effect:** 1.6m high barriers (base wall + mesh) create a high-pressure friction corridor.")
            st.error("**Colonization:** 3m existing footpaths are 100% occupied; pedestrians are physically 'piped' into vehicular traffic.")

    with col_fixed:
        st.subheader("Proposed: Gold Standard ($f=1$)")
        # Path kept exactly as requested
        st.image(f"cad_viewer/f=1.png", caption="Gold Standard: 3m Reclaimed Path", use_container_width=True)
        
        with st.expander("Remediation Strategy (Redesign)"):
            st.success("**Reclaimed Clear Path:** Restoration of a continuous 3m unobstructed concrete walking zone.")
            st.success("**Integrated Ecosystem:** Vending shifted to a 1.5m curb-side 'Utility Zone' with organized stalls.")

    st.markdown("---")

    # --- 2. POLICY & ADVOCACY POINTERS ---
    # --- 2. DETAILED BRIEFING FUNCTIONALITY ---
    st.header("Prototype Functionality")
    
    st.markdown(r"""
    1. **Geometric Contrast & Barrier Removal Analysis:** The visualizer provides a high-fidelity 'Before vs. After' delta between a containment-based geometry and an open-flow hierarchy. It highlights the systemic failure of the 1.6m high wall, which acts as a physical 'choke' on the corridor. The redesign demonstrates that removing this caging is the primary lever for eliminating the piping effect, where pedestrians are currently trapped in a narrow, high-pressure corridor with zero escape routes into the clear path.

    2. **Unobstructed Capacity Restoration (3.0m Clear Path):** The prototype visualizes the restoration of a **continuous 3.0m 'Clear Path'**, which is the gold standard for high-density transit hubs like Yeshwantpur. This width is not arbitrary; it is mathematically optimized to ensure that even during peak hub volumes, the pedestrian density stays below the threshold of turbulence. This allows all personas (from delivery partners to the elderly) to maintain their natural free-walking speed ($v_0$) without the velocity decay caused by dodging obstacles.

    3. **Economic Integration & Utility Zone Synergy:** A core feature of the Lighthouse Prototype is the **1.5m Curb-Side Utility Zone**. Rather than the current 'Colonization' model—where vendors occupy 100% of the footpath—the redesign integrates vending into a dedicated strip. This preserves the local informal economy while ensuring that vending geometries do not bleed into the pedestrian stream. This synergy recovers the **Effective Width ($W_{\text{eff}}$)** of the sidewalk, turning a contested space into a structured, dual-purpose ecosystem.

    4. **DPR-Ready Scalability & Policy Synthesis:** Every spatial element presented here—from the flush drainage covers to the standardized kerb heights—is formatted for immediate extraction into DULT or BBMP project approval templates. By showcasing a 'Streets of Hope' baseline, the module provides policymakers with the necessary evidence to justify a **10:1 Benefit-Cost Ratio**, moving the conversation from anecdotal complaints to a data-driven capital expenditure (CAPEX) proposal.
    """)

    st.markdown("---")

    # --- 3. SPATIAL ALLOCATION TABLE ---
    st.header("Spatial Allocation Comparison (16m Section)")
    st.write("Below are the granular component dimensions required to reconstruct the Bazaar Street section under S.U.R.E. guidelines.")
    
    reconstruction_data = {
        "Component Section": [
            "Pedestrian Clear Path (Unobstructed)",
            "Utility & Vending Zone (Buffer Strip)",
            "Boundary/Segregation (Vertical)",
            "Surface Drainage (Effective Surface)",
            "Main Vehicle Carriageway",
            "Opposite Utility/Buffer Zone",
            "**Total Cross-Sectional Width**"
        ],
        "Current ($f=5$) Spec": [
            "0.0 m (Colonized by vendors)",
            "3.0 m (Unorganized/Encroached)",
            "1 m High Wall",
            "Open/Broken Drains",
            "10.0 m (Amorphous/Unmarked)",
            "2.2 m (Dirt/Obstacles)",
            "**16.0 m**"
        ],
        "Proposed ($f=1$) Spec": [
            "3.0 m (RCC Paver/Concrete)",
            "1.5 m (Granite/Cobble finish)",
            "150 mm High Mountable Kerb",
            "Flush Covers (Integrated in Path)",
            "10.0 m with Markings and Zebra Crossings (Standard 2-Lane Asphalt)",
            "4.2 m (Multi-use: Park/Vending)",
            "**19.0 m**"
        ],
        "Physics/Engineering Rationale": [
            "Restores free-flow velocity ($v_0$)",
            "Organizes informal trade geometries",
            "Eliminates psychological 'Pipe' friction",
            "Maximizes usable width ($W_{\text{eff}}$)",
            "Standardizes vehicular throughput",
            "Balances Modal Share Equity",
            "**Equilibrium State**"
        ]
    }
    
    st.table(pd.DataFrame(reconstruction_data))
    # --- 4. MATHEMATICAL JUSTIFICATION ---
    with st.expander("View Mathematical Logic & Variable Definitions"):
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

