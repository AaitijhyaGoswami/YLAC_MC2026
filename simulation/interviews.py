import streamlit as st
import base64
import os

def display_pdf(file_path):
    """Encodes the PDF and embeds it using an <embed> tag for stability."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        
        # Embed tag is often more reliable for PDFs than iframes
        pdf_display = f"""
        <embed
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="1000"
            type="application/pdf"
        >
        """
        st.markdown(pdf_display, unsafe_allow_html=True)
        
        # Direct download link as a safety fallback
        st.markdown(
            f'<div style="text-align: right;"><a href="data:application/pdf;base64,{base64_pdf}" download="{os.path.basename(file_path)}" style="color: #4CAF50; text-decoration: none; font-size: 0.8em;">📥 Download Transcript PDF</a></div>', 
            unsafe_allow_html=True
        )
    else:
        st.error(f"File not found: {os.path.basename(file_path)} (Path tried: {file_path})")

def app():
    st.title("Qualitative Evidence: Stakeholder Interviews")
    st.markdown("""
    These transcripts document the 'human friction' experienced by the Yeshwantpur-Mathikere community. 
    They serve as the qualitative backbone for the data in **Escape the Knot.pdf**.
    """)
    st.markdown("---")

    # Clean list with no citation markers
    interview_mapping = [
        ("Interview 01: Street Vendor (Bazaar Street)", "street_vendor.pdf"),
        ("Interview 02: Restaurant Owner (Constitution Circle)", "rest_owner.pdf"),
        ("Interview 03: Hotel Owner (Bazaar Circle)", "hotel_owner.pdf"),
        ("Interview 04: Ticket Collector (Administrative Inquiry)", "tc_ysp.pdf"),
        ("Interview 05: Kiosk Operator (Main Concourse)", "shop_ypr.pdf"),
        ("Interview 06: Elderly Pedestrian (Mathikere Resident)", "elderly.pdf"),
        ("Interview 07: Student at KV IISc (Mathikere Resident)", "student.pdf"),
        ("Interview 08: PhD Research Scholar (IISc Bengaluru)", "scholar.pdf"),
        ("Interview 09: Swiggy Delivery Executive (Mathikere - IISc)", "delivery.pdf"),
        ("Interview 10: Auto-Rickshaw Driver (Yeshwantpur Stand)", "auto.pdf")
    ]

    # Relies on the 'interviews' folder being in the project root
    base_folder = "interviews"

    for title, filename in interview_mapping:
        st.header(title)
        full_path = os.path.join(base_folder, filename)
        display_pdf(full_path)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("---")
