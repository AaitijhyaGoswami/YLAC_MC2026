import streamlit as st
import base64
import os

def display_pdf(file_path):
    """Bulletproof PDF display using base64 and an embed tag with a download fallback."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Using <embed> instead of <iframe> for better cross-browser PDF rendering
        pdf_display = f"""
        <embed
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="1000"
            type="application/pdf"
        >
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Fallback link in case the browser blocks the embed
        st.markdown(
            f'<div style="text-align: right;"><a href="data:application/pdf;base64,{base64_pdf}" download="{os.path.basename(file_path)}" style="color: #4CAF50; text-decoration: none; font-size: 0.8em;">📥 Download Transcript PDF</a></div>', 
            unsafe_allow_html=True
        )
    else:
        st.error(f"Critical Error: File '{os.path.basename(file_path)}' not found in the root /interviews/ folder.")

def app():
    st.title("Qualitative Evidence: Stakeholder Interviews")
    st.markdown("""
    These transcripts document the 'human friction' experienced by the Yeshwantpur-Mathikere community. 
    They serve as the qualitative backbone for the data in **Escape the Knot.pdf**.
    """)
    st.markdown("---")

    # Exact mapping of your root-level filenames
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

    # Path points to the root 'interviews' folder
    base_folder = "interviews"

    for title, filename in interview_mapping:
        st.header(title)
        full_path = os.path.join(base_folder, filename)
        display_pdf(full_path)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
