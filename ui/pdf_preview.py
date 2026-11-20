"""
PDF Preview & Download Page UI Module.
Embeds the generated PDF directly in the browser via base64 iframe,
provides download controls, regeneration triggers, and Start New Project cleanup.
"""

from pathlib import Path
from typing import Callable, Optional
import base64
import streamlit as st


def render_pdf_preview_page(
    pdf_path: Path,
    report_title: str,
    on_back_to_review_callback: Callable[[], None],
    on_regenerate_callback: Callable[[], None],
    on_start_new_project_callback: Callable[[], None],
):
    """Render the PDF Preview and Download Screen."""
    st.markdown(
        """
        <div style="margin-bottom: 1.2rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 2px;">
                🎉 Newsletter PDF Generated Successfully!
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Preview your official academic event report below or download the publication-ready PDF document.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not pdf_path.exists():
        st.error("Generated PDF file could not be found.")
        return

    pdf_bytes = pdf_path.read_bytes()
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    clean_filename = f"{report_title.replace(' ', '_')}.pdf"

    # Action Toolbar
    act_col1, act_col2, act_col3, act_col4 = st.columns([2, 1.3, 1.3, 1.4])

    with act_col1:
        st.download_button(
            label="📥 Download Newsletter PDF",
            data=pdf_bytes,
            file_name=clean_filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    with act_col2:
        if st.button("← Back to Review", use_container_width=True):
            on_back_to_review_callback()

    with act_col3:
        if st.button("🔄 Regenerate", use_container_width=True):
            on_regenerate_callback()

    with act_col4:
        if st.button("🆕 Start New Project", use_container_width=True):
            st.session_state.confirm_start_new = True
            st.rerun()

    # Start New Project Confirmation
    if st.session_state.get("confirm_start_new", False):
        st.warning("⚠️ **Starting a new project will remove all current session data and files. Continue?**")
        conf_col1, conf_col2, _ = st.columns([1, 1, 3])
        with conf_col1:
            if st.button("Yes, Clear Session", type="primary", use_container_width=True):
                st.session_state.confirm_start_new = False
                on_start_new_project_callback()
        with conf_col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.confirm_start_new = False
                st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Embedded PDF Viewer iframe
    pdf_display = f"""
    <div style="border: 1px solid #CBD5E1; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <iframe
            src="data:application/pdf;base64,{base64_pdf}#toolbar=1"
            width="100%"
            height="850px"
            type="application/pdf"
            style="border: none;"
        >
            <p>Your browser does not support embedded PDF viewing. Please use the Download button above.</p>
        </iframe>
    </div>
    """
    st.markdown(pdf_display, unsafe_allow_html=True)
