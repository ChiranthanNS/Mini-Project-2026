"""
Streamlit Custom Component Wrapper for Kanban Drag-and-Drop Board.
Provides real-time bidirectional drag-and-drop between categories and reordering within columns.
"""

from pathlib import Path
from typing import Dict, List, Optional
import base64
import streamlit as st
import streamlit.components.v1 as components
from modules.image_processor import ImageProcessor

COMPONENT_DIR = Path(__file__).resolve().parent / "kanban"
_kanban_component = components.declare_component("kanban_board", path=str(COMPONENT_DIR))


def render_kanban_board(
    events: List[Dict],
    categories: List[str],
    colors: Dict[str, str],
    key: str = "event_kanban",
) -> Optional[Dict]:
    """
    Renders the real drag-and-drop Kanban board.
    Returns drag event payload when user moves or reorders a card.
    """
    # Prepare serializable event representations with small thumbnails
    prepared_events = []
    for ev in events:
        thumb_b64 = None
        images = ev.get("images", [])
        if images and Path(images[0]).exists():
            try:
                thumb_bytes = ImageProcessor.create_thumbnail(Path(images[0]), max_size=(240, 140))
                if thumb_bytes:
                    thumb_b64 = base64.b64encode(thumb_bytes).decode("utf-8")
            except Exception:
                pass

        prepared_events.append({
            "id": ev.get("id"),
            "event_name": ev.get("event_name", "Untitled Event"),
            "date": ev.get("date", ""),
            "description": (ev.get("description", "") or "")[:120] + "...",
            "category": ev.get("category", "Other"),
            "confidence": ev.get("confidence", 0.0),
            "confidence_level": ev.get("confidence_level", "LOW"),
            "classification_source": ev.get("classification_source", "keyword"),
            "needs_review": ev.get("needs_review", False),
            "has_image": bool(images),
            "images_count": len(images),
            "thumbnail_base64": thumb_b64,
        })

    try:
        component_value = _kanban_component(
            events=prepared_events,
            categories=categories,
            colors=colors,
            key=key,
            default=None,
        )
        return component_value
    except Exception as e:
        st.warning(f"Interactive Kanban board encountered an issue: {str(e)}. Using fallback grid.")
        return None
