"""
Upload Page UI Module.
Provides drag-and-drop file upload for PDF, DOCX, JPG, JPEG, and PNG files,
validation, file listing with removal controls, and triggers event analysis.
"""

from pathlib import Path
from typing import Callable, List
import streamlit as st
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB


def render_upload_page(
    session_temp_dir: Path,
    on_analyze_callback: Callable[[List[Path]], None],
    on_load_samples_callback: Callable[[], None],
):
    """Render the File Upload Page with modern styling and validation."""
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 2rem;">
            <h1 style="font-size: 2.2rem; color: #1E3A8A; margin-bottom: 0.5rem; font-weight: 700;">
                Event Document Uploader
            </h1>
            <p style="font-size: 1.05rem; color: #4B5563; max-width: 650px; margin: 0 auto;">
                Upload event documents, reports, brochures, or posters. The system will automatically
                extract text, retrieve photographs, segment events, and classify them.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize uploaded files registry in session state
    if "uploaded_file_records" not in st.session_state:
        st.session_state.uploaded_file_records = []

    upload_dir = session_temp_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Modern Upload Card
    with st.container():
        st.markdown(
            f"""
            <div style="background-color: #F8FAFC; border: 2px dashed #93C5FD; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 2.5rem; color: #3B82F6; margin-bottom: 8px;">📂</div>
                <div style="font-weight: 600; font-size: 1.1rem; color: #1E293B;">Drag & Drop Event Documents Here</div>
                <div style="font-size: 0.9rem; color: #64748B; margin-top: 4px;">
                    Supported: <b>PDF • DOCX • JPG • JPEG • PNG</b> (Max {MAX_FILE_SIZE_MB}MB per file)
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "docx", "jpg", "jpeg", "png"],
            accept_multiple_files=True,
            label_visibility="collapsed",
            key="file_uploader_widget",
        )

    # Process newly dropped files
    if uploaded_files:
        for uf in uploaded_files:
            file_name = uf.name
            # Check if already in registry
            if any(rec["name"] == file_name for rec in st.session_state.uploaded_file_records):
                continue

            file_size_bytes = len(uf.getvalue())
            file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
            ext = Path(file_name).suffix.lower()

            # Validation
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"⚠️ '{file_name}' exceeds {MAX_FILE_SIZE_MB}MB limit.")
                continue

            if ext not in SUPPORTED_EXTENSIONS:
                st.error(f"⚠️ '{file_name}' has unsupported format '{ext}'.")
                continue

            # Save to temporary session directory
            saved_path = upload_dir / file_name
            with open(saved_path, "wb") as f:
                f.write(uf.getvalue())

            st.session_state.uploaded_file_records.append({
                "name": file_name,
                "type": ext.upper().replace(".", ""),
                "size_mb": file_size_mb if file_size_mb > 0.01 else f"{round(file_size_bytes/1024, 1)} KB",
                "path": saved_path,
                "status": "Ready",
            })

    # Render File Table / Card list if files are present
    records = st.session_state.uploaded_file_records

    if records:
        st.markdown("### 📋 Uploaded Documents")
        for idx, rec in enumerate(records):
            col_icon, col_info, col_status, col_action = st.columns([0.8, 4.5, 1.8, 1.2])

            with col_icon:
                icon = "📄"
                if rec["type"] in ["JPG", "JPEG", "PNG"]:
                    icon = "🖼️"
                elif rec["type"] == "DOCX":
                    icon = "📝"
                st.markdown(f"<div style='font-size: 1.8rem; text-align: center;'>{icon}</div>", unsafe_allow_html=True)

            with col_info:
                st.markdown(f"**{rec['name']}**")
                st.caption(f"Type: `{rec['type']}` &nbsp;|&nbsp; Size: `{rec['size_mb']}`")

            with col_status:
                st.markdown(
                    "<span style='background-color: #DEF7EC; color: #03543F; font-size: 0.8rem; font-weight: 600; padding: 3px 8px; border-radius: 6px;'>✓ Ready</span>",
                    unsafe_allow_html=True,
                )

            with col_action:
                if st.button("✕ Remove", key=f"remove_file_{idx}", help=f"Remove {rec['name']}"):
                    try:
                        rec["path"].unlink(missing_ok=True)
                    except Exception:
                        pass
                    st.session_state.uploaded_file_records.pop(idx)
                    st.rerun()

            st.markdown("<hr style='margin: 0.4rem 0; border: none; border-top: 1px solid #E5E7EB;'/>", unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        btn_col1, btn_col2, btn_col3 = st.columns([1.5, 2, 2.5])

        with btn_col1:
            if st.button("🗑️ Clear All", use_container_width=True):
                for rec in st.session_state.uploaded_file_records:
                    try:
                        rec["path"].unlink(missing_ok=True)
                    except Exception:
                        pass
                st.session_state.uploaded_file_records = []
                st.rerun()

        with btn_col3:
            if st.button("🚀 Analyze Events", type="primary", use_container_width=True):
                file_paths = [rec["path"] for rec in st.session_state.uploaded_file_records]
                on_analyze_callback(file_paths)

    else:
        st.markdown("<br/>", unsafe_allow_html=True)
        demo_col1, demo_col2, demo_col3 = st.columns([1, 2.5, 1])
        with demo_col2:
            st.info("Don't have event files handy? You can load pre-bundled academic event samples to explore the workflow instantly:")
            if st.button("⚡ Load Academic Sample Documents (PDF, DOCX, Posters)", use_container_width=True):
                on_load_samples_callback()
