import streamlit as st
import pandas as pd
import os

def app():
    st.markdown("""
    The final version of the **Lighthouse Prototype** will be a physical representation of every urban cross-section that clearly demonstrates the severe contrast between the failure of a system and the ideal conditions to remedy that failure. Through the measurement of how closely the current "Containment" Model (via restrictive barriers and spatial colonization) can be compared to a S.U.R.E. Standard Hierarchy, the module converts abstract complaints about infrastructure into a structured engineering analysis. In addition, it provides a physical proof of concept for removing modal friction from the roadway and illustrates how, by modifying just a portion of an existing street segment, one can put back in place the essential purpose of the street; to safely and efficiently move people.

    In addition to its visual effect on pedestrians, the prototype provides a detailed specification of the granular redistribution of space needed to establish modal equilibrium, including a **continuous 3.0 m "Clear Path"** and an integrated **1.5 m Utility Zone**. By supporting both informal economies and repair/utilities, pedestrian traffic flow will no longer be deleteriously impacted; instead, they will be part of a more organized ecosystem. This module establishes the technical basis for DULT or BBMP project approvals and thereby supports local investments based on data-driven rationales that emphasize restored mobility rates and high benefit-cost ratios over reactive maintenance, filling the void for effective advocacy for and synthesis of policy.
    """)

    st.header("What the Problem Is")
    
    colx, coly, colz = st.columns(3)

    with colx:
        st.image(f"cad_viewer/bazaar1.jpg", use_container_width=True)
        st.caption("In all the images taken along the 600 m stretch of Bazaar Street, it is evident that there has been a system-wide encroachment of the footways originally meant for pedestrian commutes over several years. The authorities have set up wall-and-mesh barricades, limiting vehicular travel space, as an easy fix alternative to removing the encroachment. Several of the vendors who have set up stalls on the footpath for many years were unaware that they were encroaching on areas meant for pedestrian traffic.")

    with coly:
        st.image(f"cad_viewer/bazaar2.jpg", use_container_width=True)

    with colz:
        st.image(f"cad_viewer/bazaar3.jpg", use_container_width=True)

    st.markdown("---")

    st.header("What We Propose")

    # --- 1. SPATIAL VISUALIZATION ---
    col_current, col_fixed = st.columns(2)

    with col_current:
        st.subheader("Current Condition")
        # Path kept exactly as requested
        st.image(f"cad_viewer/top_f=5.jpeg")
        st.image(f"cad_viewer/f=5.png", caption="Systemic Failure: Wall & Mesh Containment", use_container_width=True)
        
        with st.expander("Spatial Diagnostics (Audit Log)"):
            st.error("**The Piping Effect:** 10 m high barriers (base wall + mesh) create a high-pressure friction corridor.")
            st.error("**Colonization:** 3 m existing footpaths are 100% occupied; pedestrians are physically 'piped' into vehicular traffic.")

    with col_fixed:
        st.subheader("After Proposed Changes")
        # Path kept exactly as requested
        st.image(f"cad_viewer/top_f=1.jpeg")
        st.image(f"cad_viewer/f=1.png", caption="Gold Standard: 3m Reclaimed Path", use_container_width=True)
        
        with st.expander("Remediation Strategy (Redesign)"):
            st.success("**Reclaimed Clear Path:** Restoration of a continuous 3m unobstructed concrete walking zone.")
            st.success("**Integrated Ecosystem:** Vending shifted to a 1.5m curb-side 'Utility Zone' with organized stalls.")

    st.markdown("---")

    # --- 2. POLICY & ADVOCACY POINTERS ---
    # --- 2. DETAILED BRIEFING FUNCTIONALITY ---
    st.header("Prototype Functionality")
    
    st.markdown(r"""
    * **Geometric Contrast & Barrier Removal Analysis:** The visualizer provides a high-fidelity 'Before vs. After' delta between a containment-based geometry and an open-flow hierarchy. The redesign demonstrates that removing this caging is the primary step for eliminating the piping effect, where pedestrians are currently trapped in a narrow, high-pressure corridor.

    * **Unobstructed Capacity Restoration (3.0m Clear Path):** The prototype visualizes the restoration of a continuous 3.0m clear path, which is the gold standard for high-density transit hubs like Yeshwantpur. This allows all personas to maintain their natural free-walking speed ($v_0$) without the velocity decay caused by dodging obstacles.

    * **Economic Integration & Utility Zone Synergy:** A core feature of the Lighthouse Prototype is the **1.5m Curb-Side Utility Zone**. Rather than the current 'Colonization' model, where vendors occupy 100% of the footpath, the redesign integrates vending into a dedicated strip. This preserves the local informal economy while ensuring that vending geometries do not bleed into the pedestrian stream.

    * **DPR-Ready Scalability & Policy Synthesis:** Every spatial element presented here, from the flush drainage covers to the standardized kerb heights, is formatted for immediate extraction into DULT or BBMP project approval templates. By showcasing a 'Streets of Hope' baseline, the module provides policymakers with the necessary evidence to justify a **10:1 Benefit-Cost Ratio** proposal.
    """)

    st.markdown("---")

    # --- 3. SPATIAL ALLOCATION TABLE ---
    st.header("Spatial Allocation Comparison")
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
        "Current Spec": [
            "0.0 m (Colonized by vendors)",
            "3.0 m (Unorganized/Encroached)",
            "1 m High Wall",
            "Open/Broken Drains",
            "4.0 m central region for 3/4 wheelers and 3 m + 3 m side paths on both sides for 2 wheelers (Amorphous/Unmarked)",
            "2.2 m (Dirt/Obstacles)",
            "16.0 m"
        ],
        "Proposed Spec": [
            "3.0 m (RCC Paver/Concrete)",
            "2.5 m (Granite/Cobble finish)",
            "150 mm High Mountable Kerb",
            "Flush Covers (Integrated in Path)",
            "10.0 m with Markings and Zebra Crossings (Standard 2-Lane Asphalt)",
            "4.2 m (Multi-use: Park/Vending)",
            "21.0 m"
        ],
        "Rationale": [
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

