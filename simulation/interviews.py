import streamlit as st
import base64
import os

def display_pdf(file_path):
    """Encodes the PDF into base64 and embeds it within an HTML iframe."""
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Standard embedding for Streamlit
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

def app():
    st.title("Qualitative Evidence: Stakeholder Interviews")
    st.markdown("""
    This module provides the 'human' layer to our physics-based audit. These transcripts 
    document the lived experience of the Yeshwantpur-Mathikere corridor and serve as the 
    primary qualitative evidence for the arguments presented in **Escape the Knot.pdf**.
    """)
    st.markdown("---")

    # Mapping headers to your specific filenames in the root 'interviews' folder
    interview_mapping = [
        ("Interview 01: Street Vendor (Bazaar Street)", "street_vendor.pdf"),[cite: 8]
        ("Interview 02: Restaurant Owner (Constitution Circle)", "rest_owner.pdf"),[cite: 7]
        ("Interview 03: Hotel Owner (Bazaar Circle)", "hotel_owner.pdf"),[cite: 6]
        ("Interview 04: Ticket Collector (Administrative Inquiry)", "tc_ysp.pdf"),[cite: 5]
        ("Interview 05: Kiosk Operator (Main Concourse)", "shop_ypr.pdf"),[cite: 4]
        ("Interview 06: Elderly Pedestrian (Mathikere Resident)", "elderly.pdf"),[cite: 2]
        ("Interview 07: Student at KV IISc (Mathikere Resident)", "student.pdf"),[cite: 3]
        ("Interview 08: PhD Research Scholar (IISc Bengaluru)", "scholar.pdf"),[cite: 11]
        ("Interview 09: Swiggy Delivery Executive (Mathikere - IISc)", "delivery.pdf"),[cite: 9]
        ("Interview 10: Auto-Rickshaw Driver (Yeshwantpur Stand)", "auto.pdf")[cite: 10]
    ]

    # Path relative to the root where the app is run
    base_folder = "interviews"

    for title, filename in interview_mapping:
        st.header(title)
        full_path = os.path.join(base_folder, filename)
        
        if os.path.exists(full_path):
            display_pdf(full_path)
        else:
            st.error(f"Transcript not found: {filename} in folder '{base_folder}'")
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
