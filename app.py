"""
Automated Event Classification and Newsletter PDF Generator
Main Streamlit Application Entrypoint.
"""

from pathlib import Path
import os
import shutil
import uuid
import streamlit as st
from dotenv import load_dotenv

# Ensure dotenv is loaded
load_dotenv()

from config import (
    BASE_DIR,
    TEMP_DIR,
    ASSETS_DIR,
    DEFAULT_REPORT_SETTINGS,
    GEMINI_API_KEY,
)
from modules.keyword_manager import KeywordManager
from modules.ocr_processor import OCRProcessor
from modules.pdf_generator import PDFNewsletterGenerator
from ui.upload import render_upload_page
from ui.processing import execute_processing_pipeline
from ui.review import render_review_page
from ui.dashboard import render_dashboard_page
from ui.settings import render_settings_page
from ui.pdf_preview import render_pdf_preview_page

# Configure Streamlit page settings
st.set_page_config(
    page_title="Event Classification & Newsletter Generator",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Professional Academic CSS
CUSTOM_CSS = """
<style>
    /* Global Styling */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Workflow Step Indicator */
    .step-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 10px 24px;
        margin-bottom: 1.8rem;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.88rem;
        font-weight: 600;
        color: #94A3B8;
    }
    .step-item.active {
        color: #1E3A8A;
    }
    .step-item.completed {
        color: #059669;
    }
    .step-num {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        background: #E2E8F0;
        color: #64748B;
    }
    .step-item.active .step-num {
        background: #1E3A8A;
        color: #FFFFFF;
    }
    .step-item.completed .step-num {
        background: #059669;
        color: #FFFFFF;
    }
    .step-arrow {
        color: #CBD5E1;
        font-size: 1.1rem;
    }

    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
    }

    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #1E3A8A !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #64748B !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state():
    """Initialize temporary session storage and state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]

    session_temp_dir = TEMP_DIR / f"session_{st.session_state.session_id}"
    session_temp_dir.mkdir(parents=True, exist_ok=True)
    st.session_state.session_temp_dir = session_temp_dir

    if "current_step" not in st.session_state:
        st.session_state.current_step = "upload"

    if "events" not in st.session_state:
        st.session_state.events = []

    if "uploaded_file_records" not in st.session_state:
        st.session_state.uploaded_file_records = []

    if "keyword_manager" not in st.session_state:
        st.session_state.keyword_manager = KeywordManager()

    if "report_settings" not in st.session_state:
        st.session_state.report_settings = dict(DEFAULT_REPORT_SETTINGS)
        # Point to default logo if exists
        default_logo = ASSETS_DIR / "default_logo.png"
        if default_logo.exists():
            st.session_state.report_settings["logo_path"] = str(default_logo)

    if "gemini_api_key" not in st.session_state:
        st.session_state.gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    if "generated_pdf_path" not in st.session_state:
        st.session_state.generated_pdf_path = None


def clear_session_and_restart():
    """Completely clear temporary files and reset state for a clean new project."""
    temp_dir = st.session_state.get("session_temp_dir")
    if temp_dir and temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    # Clear all state variables
    for key in list(st.session_state.keys()):
        del st.session_state[key]

    init_session_state()
    st.rerun()


def render_workflow_header(current_step: str):
    """Render top workflow progress indicator bar."""
    steps = [
        ("upload", "01", "Upload Files"),
        ("review", "02", "Review & Arrange"),
        ("dashboard", "03", "Analytics"),
        ("settings", "04", "Report Settings"),
        ("pdf_preview", "05", "PDF Preview"),
    ]

    step_order = ["upload", "review", "dashboard", "settings", "pdf_preview"]
    curr_idx = step_order.index(current_step) if current_step in step_order else 0

    html_parts = ['<div class="step-container">']
    for idx, (step_id, step_num, step_label) in enumerate(steps):
        if idx < curr_idx:
            status_class = "completed"
            icon = "✓"
        elif idx == curr_idx:
            status_class = "active"
            icon = step_num
        else:
            status_class = ""
            icon = step_num

        html_parts.append(
            f'<div class="step-item {status_class}">'
            f'<div class="step-num">{icon}</div>'
            f'<span>{step_label}</span>'
            f'</div>'
        )

        if idx < len(steps) - 1:
            html_parts.append('<div class="step-arrow">›</div>')

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_sidebar():
    """Render application sidebar with status, navigation, and settings."""
    with st.sidebar:
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 1.2rem;">
                <span style="font-size: 2rem;">📰</span>
                <div>
                    <h3 style="margin: 0; font-size: 1.15rem; color: #1E3A8A; font-weight: 700;">Event Newsletter</h3>
                    <span style="font-size: 0.75rem; color: #64748B;">Automated Classifier & PDF</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### 🧭 Workflow Navigation")

        step = st.session_state.current_step
        has_events = len(st.session_state.events) > 0
        has_pdf = st.session_state.generated_pdf_path is not None

        if st.button("01 • 📂 Document Upload", use_container_width=True, type="primary" if step == "upload" else "secondary"):
            st.session_state.current_step = "upload"
            st.rerun()

        if st.button("02 • 🗂️ Review & Arrange", use_container_width=True, disabled=not has_events, type="primary" if step == "review" else "secondary"):
            st.session_state.current_step = "review"
            st.rerun()

        if st.button("03 • 📊 Dashboard & Metrics", use_container_width=True, disabled=not has_events, type="primary" if step == "dashboard" else "secondary"):
            st.session_state.current_step = "dashboard"
            st.rerun()

        if st.button("04 • ⚙️ Report Settings", use_container_width=True, disabled=not has_events, type="primary" if step == "settings" else "secondary"):
            st.session_state.current_step = "settings"
            st.rerun()

        if st.button("05 • 📄 PDF Preview", use_container_width=True, disabled=not has_pdf, type="primary" if step == "pdf_preview" else "secondary"):
            st.session_state.current_step = "pdf_preview"
            st.rerun()

        st.markdown("---")

        # Live Project Status Card
        if has_events:
            st.markdown("### 📌 Active Project")
            st.markdown(f"• **Events:** `{len(st.session_state.events)}`")
            km = st.session_state.keyword_manager
            counts = {c: 0 for c in km.get_categories()}
            for e in st.session_state.events:
                c = e.get("category", "Other")
                counts[c] = counts.get(c, 0) + 1
            for cat, cnt in counts.items():
                if cnt > 0:
                    st.caption(f"&nbsp;&nbsp;› {cat}: {cnt}")
            st.markdown("---")

        # System Engines Status
        with st.expander("🛠️ Engine Diagnostic Status", expanded=False):
            # OCR status
            ocr_ready = OCRProcessor.is_available()
            if ocr_ready:
                st.success("✓ Tesseract OCR: Active")
            else:
                st.info("ℹ️ Tesseract OCR: Not detected on PATH. Fallback graceful mode active.")

            # Gemini Fallback Status
            key = st.session_state.gemini_api_key
            if key and key != "your_gemini_api_key_here":
                st.success("✓ Gemini Fallback API: Configured")
            else:
                st.caption("• Optional AI Fallback: None (Keyword Engine is Primary)")

            # Custom Gemini Key input
            custom_key = st.text_input(
                "Gemini API Key (Optional)",
                value=st.session_state.gemini_api_key,
                type="password",
                help="Only used as an optional fallback when keyword confidence is ambiguous.",
            )
            if custom_key != st.session_state.gemini_api_key:
                st.session_state.gemini_api_key = custom_key
                st.success("API key updated for current session.")

        # Start New Project / Clear Session
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("🆕 Start New Project", use_container_width=True):
            clear_session_and_restart()


def main():
    init_session_state()
    render_sidebar()

    current_step = st.session_state.current_step
    render_workflow_header(current_step)

    # PAGE ROUTER
    if current_step == "upload":
        def on_analyze(files: list[Path]):
            st.session_state.files_to_process = files
            st.session_state.current_step = "processing"
            st.rerun()

        def on_load_samples():
            # Copy sample files into session upload directory
            sample_dir = ASSETS_DIR / "sample_docs"
            upload_dir = st.session_state.session_temp_dir / "uploads"
            sample_files = list(sample_dir.glob("*.pdf")) + list(sample_dir.glob("*.docx")) + list(sample_dir.glob("*.png"))

            st.session_state.uploaded_file_records = []
            for sf in sample_files:
                dest = upload_dir / sf.name
                shutil.copy2(sf, dest)
                st.session_state.uploaded_file_records.append({
                    "name": sf.name,
                    "type": sf.suffix.upper().replace(".", ""),
                    "size_mb": f"{round(sf.stat().st_size / 1024, 1)} KB",
                    "path": dest,
                    "status": "Ready",
                })
            st.success(f"Loaded {len(sample_files)} academic sample files!")
            st.rerun()

        render_upload_page(
            session_temp_dir=st.session_state.session_temp_dir,
            on_analyze_callback=on_analyze,
            on_load_samples_callback=on_load_samples,
        )

    elif current_step == "processing":
        files_to_process = st.session_state.get("files_to_process", [])
        events = execute_processing_pipeline(
            file_paths=files_to_process,
            session_temp_dir=st.session_state.session_temp_dir,
            km=st.session_state.keyword_manager,
            gemini_key=st.session_state.gemini_api_key,
        )
        st.session_state.events = events
        st.session_state.current_step = "review"
        st.rerun()

    elif current_step == "review":
        render_review_page(
            events=st.session_state.events,
            km=st.session_state.keyword_manager,
            session_temp_dir=st.session_state.session_temp_dir,
        )

        st.markdown("<br/>", unsafe_allow_html=True)
        nav_col1, nav_col2, nav_col3 = st.columns([1.5, 2, 2.5])
        with nav_col1:
            if st.button("← Back to Upload", use_container_width=True):
                st.session_state.current_step = "upload"
                st.rerun()
        with nav_col3:
            if st.button("Proceed to Dashboard & Analytics →", type="primary", use_container_width=True):
                st.session_state.current_step = "dashboard"
                st.rerun()

    elif current_step == "dashboard":
        def on_proceed_to_pdf():
            st.session_state.current_step = "settings"
            st.rerun()

        def on_back_to_review():
            st.session_state.current_step = "review"
            st.rerun()

        render_dashboard_page(
            events=st.session_state.events,
            km=st.session_state.keyword_manager,
            on_proceed_to_pdf_callback=on_proceed_to_pdf,
            on_back_to_review_callback=on_back_to_review,
        )

    elif current_step == "settings":
        def on_generate_pdf(report_settings: dict):
            pdf_out_path = st.session_state.session_temp_dir / "Event_Newsletter_Report.pdf"
            pdf_gen = PDFNewsletterGenerator(pdf_out_path)
            with st.spinner("Compiling publication-quality PDF newsletter..."):
                pdf_gen.generate_pdf(
                    events=st.session_state.events,
                    categories=st.session_state.keyword_manager.get_categories(),
                    report_settings=report_settings,
                    temp_dir=st.session_state.session_temp_dir,
                )
            st.session_state.generated_pdf_path = pdf_out_path
            st.session_state.current_step = "pdf_preview"
            st.rerun()

        def on_back_to_dash():
            st.session_state.current_step = "dashboard"
            st.rerun()

        render_settings_page(
            events=st.session_state.events,
            session_temp_dir=st.session_state.session_temp_dir,
            on_generate_pdf_callback=on_generate_pdf,
            on_back_to_dashboard_callback=on_back_to_dash,
        )

    elif current_step == "pdf_preview":
        pdf_path = st.session_state.generated_pdf_path
        report_title = st.session_state.report_settings.get("report_title", "Event_Newsletter")

        def on_back_to_rev():
            st.session_state.current_step = "review"
            st.rerun()

        def on_regen():
            st.session_state.current_step = "settings"
            st.rerun()

        render_pdf_preview_page(
            pdf_path=pdf_path,
            report_title=report_title,
            on_back_to_review_callback=on_back_to_rev,
            on_regenerate_callback=on_regen,
            on_start_new_project_callback=clear_session_and_restart,
        )


if __name__ == "__main__":
    main()
