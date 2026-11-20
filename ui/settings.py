"""
Report Settings & Final Validation Page UI Module.
Allows faculty to customize Institution, Department, Title, Academic Year,
Reporting Period, and upload an institution logo. Performs pre-PDF validation checks.
"""

from pathlib import Path
from typing import Callable, Dict, List
import streamlit as st
from PIL import Image

from config import DEFAULT_REPORT_SETTINGS
from modules.image_processor import ImageProcessor


def render_settings_page(
    events: List[Dict],
    session_temp_dir: Path,
    on_generate_pdf_callback: Callable[[Dict], None],
    on_back_to_dashboard_callback: Callable[[], None],
):
    """Render Report Settings and Final Pre-flight Validation."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 2px;">
                Report Settings & Final Validation
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Configure the publication details for the cover page, headers, and metadata before generating the official PDF.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "report_settings" not in st.session_state:
        st.session_state.report_settings = dict(DEFAULT_REPORT_SETTINGS)

    current_settings = st.session_state.report_settings

    # 1. Validation Checklist
    st.markdown("### ✅ Pre-Generation Validation Status")
    total_events = len(events)
    events_no_photos = [e for e in events if not e.get("images") or len(e["images"]) == 0]
    events_no_dates = [e for e in events if not e.get("date")]

    vcol1, vcol2 = st.columns(2)
    with vcol1:
        st.markdown(f"• **Events Ready for Compilation:** `{total_events}`")
        if events_no_photos:
            st.warning(f"⚠️ `{len(events_no_photos)}` event(s) have no photographs. Clean placeholders will be used in the PDF.")
        else:
            st.success("✓ All events have associated photographs.")

    with vcol2:
        if events_no_dates:
            st.info(f"ℹ️ `{len(events_no_dates)}` event(s) have unspecified dates.")
        else:
            st.success("✓ All events have verified dates.")

    st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #E2E8F0;'/>", unsafe_allow_html=True)

    # 2. Report Settings Form
    st.markdown("### 🏛️ Institutional & Newsletter Metadata")

    with st.form("report_settings_form"):
        col_inst, col_dept = st.columns(2)
        with col_inst:
            inst_name = st.text_input(
                "Institution Name*",
                value=current_settings.get("institution_name", "Vidyavardhaka College of Engineering"),
            )
        with col_dept:
            dept_name = st.text_input(
                "Department / Program Name*",
                value=current_settings.get("department_name", "Department of Computer Science & Engineering"),
            )

        col_title, col_sub = st.columns([1.5, 1])
        with col_title:
            rep_title = st.text_input(
                "Report Title*",
                value=current_settings.get("report_title", "Department Event Newsletter"),
            )
        with col_sub:
            subtitle = st.text_input(
                "Subtitle (Optional)",
                value=current_settings.get("subtitle", "Comprehensive Activity Compendium"),
            )

        col_yr, col_period = st.columns(2)
        with col_yr:
            acad_year = st.text_input(
                "Academic Year*",
                value=current_settings.get("academic_year", "2026–2027"),
            )
        with col_period:
            period = st.text_input(
                "Reporting Period*",
                value=current_settings.get("reporting_period", "June 2026 – September 2026"),
            )

        # Logo Upload
        st.markdown("**Institution Logo:**")
        existing_logo = current_settings.get("logo_path")
        if existing_logo and Path(existing_logo).exists():
            st.image(str(existing_logo), width=120, caption="Current Institution Logo")

        logo_file = st.file_uploader(
            "Upload Logo (PNG, JPG, JPEG)",
            type=["png", "jpg", "jpeg"],
            key="logo_uploader",
        )

        st.markdown("<br/>", unsafe_allow_html=True)
        btn1, btn2 = st.columns([1, 1.5])
        with btn1:
            back_clicked = st.form_submit_button("← Back to Dashboard", use_container_width=True)
        with btn2:
            generate_clicked = st.form_submit_button("🚀 Generate PDF Newsletter", type="primary", use_container_width=True)

        if generate_clicked:
            # Handle logo
            logo_path_to_save = existing_logo
            if logo_file:
                logos_dir = session_temp_dir / "logos"
                logos_dir.mkdir(parents=True, exist_ok=True)
                saved_logo = ImageProcessor.save_image_bytes(
                    image_bytes=logo_file.getvalue(),
                    destination_dir=logos_dir,
                    prefix="inst_logo",
                    extension=Path(logo_file.name).suffix.lower(),
                )
                logo_path_to_save = str(saved_logo)

            updated_settings = {
                "institution_name": inst_name.strip(),
                "department_name": dept_name.strip(),
                "report_title": rep_title.strip(),
                "subtitle": subtitle.strip(),
                "academic_year": acad_year.strip(),
                "reporting_period": period.strip(),
                "logo_path": logo_path_to_save,
            }
            st.session_state.report_settings = updated_settings
            on_generate_pdf_callback(updated_settings)

        if back_clicked:
            on_back_to_dashboard_callback()
