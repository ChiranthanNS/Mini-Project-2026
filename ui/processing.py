"""
Processing Page UI Module.
Displays real-time step-by-step progress during text/image extraction,
event detection, OCR, keyword classification, and preparation for review.
"""

from pathlib import Path
from typing import Dict, List, Optional
import time
import streamlit as st

from modules.document_processor import DocumentProcessor
from modules.event_detector import EventDetector
from modules.event_extractor import EventExtractor
from modules.classifier import EventClassifier
from modules.ai_fallback import AIFallbackClassifier
from modules.keyword_manager import KeywordManager


def execute_processing_pipeline(
    file_paths: List[Path],
    session_temp_dir: Path,
    km: KeywordManager,
    gemini_key: Optional[str] = None,
) -> List[Dict]:
    """
    Executes the complete processing pipeline while updating the UI with visual progress steps.
    """
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <h2 style="color: #1E3A8A; font-weight: 700;">Analyzing Uploaded Documents...</h2>
            <p style="color: #6B7280;">Please wait while the engine segments events, extracts photos, and calculates classifications.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    progress_bar = st.progress(0.0)
    status_container = st.empty()

    doc_processor = DocumentProcessor(session_temp_dir)
    classifier = EventClassifier(km)
    ai_fallback = AIFallbackClassifier(api_key=gemini_key)

    steps = [
        "Reading documents & validating formats...",
        "Extracting text content & document hierarchies...",
        "Extracting embedded event photographs...",
        "Running OCR where scanned pages or posters detected...",
        "Detecting discrete event boundaries...",
        "Extracting event metadata (Dates, Venues, Organizers)...",
        "Executing weighted keyword classification...",
        "Calculating category confidence & ambiguity scores...",
        "Evaluating optional AI fallback for ambiguous events...",
        "Finalizing event cards for human review...",
    ]

    all_raw_docs = []
    total_files = len(file_paths)

    # 1-4: Document Processing
    for i, fp in enumerate(file_paths):
        pct = 0.05 + (0.35 * ((i + 1) / total_files))
        progress_bar.progress(pct)
        status_container.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
                <div style="color: #1E3A8A; font-weight: 600;">✓ Processing: <code>{fp.name}</code> ({i+1}/{total_files})</div>
                <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">{steps[min(i, 3)]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(0.08) # Visual smoothness
        doc_res = doc_processor.process_file(fp)
        all_raw_docs.append(doc_res)

    # 5. Event Detection
    progress_bar.progress(0.50)
    status_container.markdown(
        """
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
            <div style="color: #1E3A8A; font-weight: 600;">✓ Detecting individual events across documents...</div>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">Analyzing headings, templates, and boundaries...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.1)

    raw_event_segments = []
    for doc_res in all_raw_docs:
        segments = EventDetector.detect_events_from_document(doc_res)
        raw_event_segments.extend(segments)

    # 6. Information Extraction
    progress_bar.progress(0.65)
    status_container.markdown(
        f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
            <div style="color: #1E3A8A; font-weight: 600;">✓ Extracting details for {len(raw_event_segments)} candidate events...</div>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">Associating titles, dates, venues, organizers, and photographs...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.1)

    extracted_events = []
    for seg in raw_event_segments:
        ev = EventExtractor.extract_event_data(seg)
        extracted_events.append(ev)

    # 7-8. Keyword Classification & Confidence
    progress_bar.progress(0.80)
    status_container.markdown(
        """
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
            <div style="color: #1E3A8A; font-weight: 600;">✓ Executing weighted keyword scoring engine...</div>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 4px;">Scoring categories and computing confidence thresholds...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.1)

    classified_events = []
    for ev in extracted_events:
        c_ev = classifier.classify_event(ev)
        classified_events.append(c_ev)

    # 9. Optional AI Fallback
    progress_bar.progress(0.92)
    if ai_fallback.is_available():
        status_container.markdown(
            """
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
                <div style="color: #1E3A8A; font-weight: 600;">✓ Checking ambiguous events against Gemini AI fallback...</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for ev in classified_events:
            if ev.get("needs_review") or ev.get("confidence", 0) < 0.50:
                ai_fallback.classify_fallback(ev, km.get_categories())

    # 10. Complete
    progress_bar.progress(1.0)
    status_container.markdown(
        f"""
        <div style="background: #DEF7EC; border: 1px solid #31C48D; border-radius: 8px; padding: 16px;">
            <div style="color: #03543F; font-weight: 700; font-size: 1.1rem;">🎉 Analysis Complete! {len(classified_events)} Events Detected.</div>
            <div style="color: #046C4E; font-size: 0.9rem; margin-top: 4px;">Preparing Review & Arrange workspace...</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    time.sleep(0.3)

    return classified_events
