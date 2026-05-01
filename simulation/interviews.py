import streamlit as st
import streamlit.components.v1 as components  # Required for robust HTML rendering
import base64
import os

def display_pdf(file_path):
    """Uses Streamlit components to force-render the PDF and provides a download button."""
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        
        # Using st.components.v1.html creates an isolated sandbox for the PDF
        pdf_display = f"""
        <embed
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="1000"
            type="application/pdf"
        >
        """
        components.html(pdf_display, height=1010)
        
        # Use Streamlit's native download button for the fallback
        st.download_button(
            label=f"📥 Download {os.path.basename(file_path)}",
            data=pdf_data,
            file_name=os.path.basename(file_path),
            mime="application/pdf"
        )
    else:
        st.error(f"File not found: {os.path.basename(file_path)} at path: {file_path}")

def app():
    st.title("Qualitative Evidence: Stakeholder Interviews")
    st.markdown("""
    These transcripts document the 'human friction' experienced by the Yeshwantpur-Mathikere community. 
    They serve as the qualitative backbone for the data in **Escape the Knot.pdf**.
    """)
    st.markdown("---")

    # Mapping your specific root-level filenames
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

    # Ensure this folder is at the root level of your project
    base_folder = "interviews"

    for title, filename in interview_mapping:
        st.header(title)
        full_path = os.path.join(base_folder, filename)
        display_pdf(full_path)
        st.markdown("---")
