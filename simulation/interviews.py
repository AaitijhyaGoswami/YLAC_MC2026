import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
import os

def render_interview(filename, title):
    """Helper to display a specific interview PDF using the viewer library."""
    base_folder = "interviews"
    full_path = os.path.join(base_folder, filename)
    
    with st.expander(f"View {title}"):
        if os.path.exists(full_path):
            # The library handles binary reading and base64 internally
            pdf_viewer(input=full_path, width=700)
            
            # Providing a native download button for accessibility
            with open(full_path, "rb") as f:
                st.download_button(
                    label=f"Download {filename}",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
        else:
            st.error(f"File not found: {filename} in directory '{base_folder}'")

def app():
    st.title("Qualitative Evidence: Stakeholder Interviews")
    st.markdown("""
    This section archives the human narratives of the Yeshwantpur-Mathikere corridor. 
    Select a stakeholder to view their bilingual or English transcript as recorded 
    during the 2026 mobility audit.
    """)
    st.markdown("---")

    # Mapping files directly to their audited roles
    render_interview("street_vendor.pdf", "Interview 01: Street Vendor (Bazaar Street)")[cite: 8]
    render_interview("rest_owner.pdf", "Interview 02: Restaurant Owner (Constitution Circle)")[cite: 7]
    render_interview("hotel_owner.pdf", "Interview 03: Hotel Owner (Bazaar Circle)")[cite: 6]
    render_interview("tc_ysp.pdf", "Interview 04: Ticket Collector (Administrative Inquiry)")[cite: 5]
    render_interview("shop_ypr.pdf", "Interview 05: Kiosk Operator (Main Concourse)")[cite: 4]
    render_interview("elderly.pdf", "Interview 06: Elderly Pedestrian (Mathikere Resident)")[cite: 2]
    render_interview("student.pdf", "Interview 07: Student (KV IISc Resident)")[cite: 3]
    render_interview("scholar.pdf", "Interview 08: PhD Research Scholar (IISc Bengaluru)")[cite: 11]
    render_interview("delivery.pdf", "Interview 09: Swiggy Delivery Executive (Mathikere - IISc)")[cite: 9]
    render_interview("auto.pdf", "Interview 10: Auto-Rickshaw Driver (Yeshwantpur Stand)")[cite: 10]
