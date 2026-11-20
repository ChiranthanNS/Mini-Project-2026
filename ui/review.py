"""
Review & Arrange Page UI Module.
Implements real drag-and-drop Kanban, reordering, event editing with photo management,
manual event creation, event deletion, duplicate detection alerts, search, category filtering,
and category/keyword management.
"""

from pathlib import Path
from typing import Dict, List, Optional
import shutil
import uuid
import streamlit as st
from PIL import Image

from modules.duplicate_detector import DuplicateDetector
from modules.keyword_manager import KeywordManager
from modules.image_processor import ImageProcessor
from ui.components.kanban_board import render_kanban_board


def render_review_page(
    events: List[Dict],
    km: KeywordManager,
    session_temp_dir: Path,
):
    """Render the Review and Arrange workspace."""

    # 1. Header & Quick Controls
    header_col1, header_col2, header_col3 = st.columns([4, 1.8, 1.8])

    with header_col1:
        st.html(
            """
            <div style="margin-bottom: 8px;">
                <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 4px;">
                    Review & Arrange Events
                </h2>
                <p style="color: #64748B; font-size: 0.95rem; margin-bottom: 0;">
                    Verify classifications, drag-and-drop between categories, reorder events, and edit details.
                </p>
            </div>
            """
        )

    with header_col2:
        if st.button("➕ Add Event Manually", use_container_width=True):
            st.session_state.active_modal = "add_event"
            st.rerun()

    with header_col3:
        if st.button("⚙️ Manage Categories", use_container_width=True):
            st.session_state.active_modal = "manage_categories"
            st.rerun()

    st.divider()

    # 2. Duplicate Detection Banner
    duplicate_pairs = DuplicateDetector.find_duplicate_pairs(events)
    if duplicate_pairs and not st.session_state.get("dismissed_duplicates", False):
        st.warning(
            f"⚠️ **Possible Duplicate Events Detected ({len(duplicate_pairs)} pair(s))**"
        )
        for pair in duplicate_pairs[:3]:
            dcol1, dcol2, dcol3 = st.columns([4, 1.2, 1.2])
            with dcol1:
                st.markdown(
                    f"• **'{pair['event_a_name']}'** vs **'{pair['event_b_name']}'** "
                    f"({pair['similarity']}% similarity, File: `{pair['event_a_file']}`)"
                )
            with dcol2:
                if st.button("Keep Both", key=f"keep_{pair['pair_id']}", use_container_width=True):
                    st.session_state.dismissed_duplicates = True
                    st.rerun()
            with dcol3:
                if st.button("Remove Duplicate", key=f"rem_{pair['pair_id']}", type="primary", use_container_width=True):
                    # Remove the second event
                    st.session_state.events = [e for e in st.session_state.events if e["id"] != pair["event_b_id"]]
                    st.success("Duplicate event removed.")
                    st.rerun()

    # 3. Search and Category Filter Toolbar
    search_col, filter_col, view_col = st.columns([3.5, 2.5, 1.5])

    with search_col:
        search_query = st.text_input(
            "Search events...",
            placeholder="🔍 Search by name, venue, organizer, or keywords...",
            label_visibility="collapsed",
            key="event_search_input",
        ).strip().lower()

    with filter_col:
        category_options = ["All Categories"] + km.get_categories()
        selected_category_filter = st.selectbox(
            "Filter Category",
            options=category_options,
            label_visibility="collapsed",
            key="category_filter_dropdown",
        )

    with view_col:
        view_mode = st.radio(
            "View Mode",
            options=["Kanban", "Cards"],
            horizontal=True,
            label_visibility="collapsed",
            key="review_view_mode",
        )

    # 4. Live Counter Badges
    categories = km.get_categories()
    category_counts = {c: 0 for c in categories}
    for e in events:
        cat = e.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Filter events based on search and category
    filtered_events = []
    for ev in events:
        if selected_category_filter != "All Categories" and ev.get("category") != selected_category_filter:
            continue

        if search_query:
            searchable_blob = (
                f"{ev.get('event_name', '')} {ev.get('description', '')} "
                f"{ev.get('organizer', '')} {ev.get('venue', '')} "
                f"{ev.get('department', '')} {ev.get('category', '')}"
            ).lower()
            if search_query not in searchable_blob:
                continue

        filtered_events.append(ev)

    # Display Counters
    counter_badges = [
        f"<b>Total Events:</b> {len(events)}",
        f"<b>Visible:</b> {len(filtered_events)}",
    ]
    for cat in categories:
        count = category_counts.get(cat, 0)
        if count > 0:
            color = km.get_color(cat)
            counter_badges.append(f"<span style='color:{color}; font-weight:700;'>{cat}:</span> {count}")

    st.html(
        f"""
        <div style="background: #F1F5F9; border-radius: 8px; padding: 10px 16px; font-size: 0.88rem; color: #334155; margin-bottom: 1.2rem; display: flex; flex-wrap: wrap; gap: 16px; align-items: center;">
            {" &nbsp;•&nbsp; ".join(counter_badges)}
        </div>
        """
    )

    # 5. Handle Modals (Edit, Add, Delete Confirmation, Manage Categories)
    active_modal = st.session_state.get("active_modal")

    if active_modal == "edit_event":
        _render_edit_modal(events, km, session_temp_dir)
    elif active_modal == "add_event":
        _render_add_modal(km, session_temp_dir)
    elif active_modal == "delete_confirm":
        _render_delete_modal()
    elif active_modal == "manage_categories":
        _render_manage_categories_modal(km)

    # 6. View Rendering (Kanban Drag-and-Drop or Detailed Card Grid)
    if view_mode == "Kanban":
        st.markdown(
            "<div style='font-size: 0.85rem; color: #64748B; margin-bottom: 6px;'>Drag cards across columns to change their category in real time. Drag up/down to reorder.</div>",
            unsafe_allow_html=True,
        )
        drag_result = render_kanban_board(
            events=filtered_events,
            categories=categories if selected_category_filter == "All Categories" else [selected_category_filter],
            colors=km.colors,
            key="main_kanban_component",
        )

        # Handle real drag & drop update event
        if drag_result and drag_result.get("action") == "drag_reorder":
            moved_id = drag_result.get("moved_event_id")
            new_cat = drag_result.get("new_category")
            category_order_map = drag_result.get("category_order_map", {})

            # 1. Update moved event category
            if moved_id and new_cat:
                for e in st.session_state.events:
                    if e["id"] == moved_id:
                        if e.get("category") != new_cat:
                            e["category"] = new_cat
                            e["needs_review"] = False
                            e["confidence"] = 1.0  # User approved
                            e["classification_source"] = "manual_drag"
                        break

            # 2. Update sequence order across categories
            if category_order_map:
                new_ordered_events = []
                # Map by id for instant lookup
                event_dict = {e["id"]: e for e in st.session_state.events}
                for cat_name, id_list in category_order_map.items():
                    for eid in id_list:
                        if eid in event_dict:
                            event_dict[eid]["category"] = cat_name
                            new_ordered_events.append(event_dict[eid])

                # Include any events that were not visible due to filters
                existing_ids = {e["id"] for e in new_ordered_events}
                for e in st.session_state.events:
                    if e["id"] not in existing_ids:
                        new_ordered_events.append(e)

                st.session_state.events = new_ordered_events
                st.rerun()

    # Detailed Card View / Management Controls (Below Kanban or in Card Mode)
    st.markdown("### 🗂️ Event Directory & Granular Controls")
    if not filtered_events:
        st.info("No events match the current search or category filter.")
        return

    # Render cards in a responsive 2-column or 3-column layout
    cols = st.columns(2)
    for idx, ev in enumerate(filtered_events):
        with cols[idx % 2]:
            _render_single_event_card(ev, idx, len(filtered_events), km)


def _render_single_event_card(ev: Dict, idx: int, total: int, km: KeywordManager):
    """Render an individual interactive event card with clean formatting and controls."""
    cat = ev.get("category", "Other")
    cat_color = km.get_color(cat)
    conf = ev.get("confidence", 0.0)
    conf_pct = int(conf * 100)
    conf_level = ev.get("confidence_level", "LOW")
    needs_review = ev.get("needs_review", False)
    images = ev.get("images", [])

    conf_bg = "#DEF7EC" if conf_level == "HIGH" else ("#FEF08A" if conf_level == "MEDIUM" else "#FEE2E2")
    conf_fg = "#03543F" if conf_level == "HIGH" else ("#854D0E" if conf_level == "MEDIUM" else "#991B1B")

    with st.container(border=True):
        st.html(
            f"""
            <div style="border-left: 5px solid {cat_color}; padding-left: 12px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="font-size: 0.82rem; font-weight: 700; color: {cat_color}; text-transform: uppercase; letter-spacing: 0.5px;">
                        ● {cat}
                    </span>
                    <div>
                        {'<span style="background: #FFEDD5; color: #C2410C; font-size: 0.75rem; font-weight: 700; padding: 3px 8px; border-radius: 4px; margin-right: 6px;">⚠️ Needs Review</span>' if needs_review else ''}
                        <span style="background: {conf_bg}; color: {conf_fg}; font-size: 0.75rem; font-weight: 700; padding: 3px 8px; border-radius: 4px;">
                            {conf_pct}% ({conf_level})
                        </span>
                    </div>
                </div>
                <div style="font-weight: 700; font-size: 1.1rem; color: #1E293B; margin-bottom: 4px; line-height: 1.4;">
                    {ev.get('event_name', 'Untitled Event')}
                </div>
                <div style="font-size: 0.85rem; color: #64748B;">
                    📅 <b>{ev.get('date') or 'Date unspecified'}</b> &nbsp;&nbsp;|&nbsp;&nbsp; 📍 <b>{ev.get('venue') or 'Venue unspecified'}</b>
                </div>
            </div>
            """
        )

        # Image preview if available
        if images and Path(images[0]).exists():
            img_cols = st.columns(min(len(images), 3))
            for i, img_p in enumerate(images[:3]):
                if Path(img_p).exists():
                    with img_cols[i]:
                        st.image(str(img_p), use_container_width=True, caption=f"Photo {i+1}")
        else:
            st.caption("📷 *No event photograph available*")

        # Short description
        desc_preview = (ev.get("description") or "No description available.")
        if len(desc_preview) > 160:
            desc_preview = desc_preview[:160] + "..."
        st.markdown(f"*{desc_preview}*")

        # Quick action toolbar
        btn_col1, btn_col2, btn_col3, btn_col4, btn_col5 = st.columns([1.5, 1.5, 1, 1, 1.2])

        with btn_col1:
            if st.button("✏️ Edit", key=f"edit_btn_{ev['id']}", use_container_width=True):
                st.session_state.edit_target_id = ev["id"]
                st.session_state.active_modal = "edit_event"
                st.rerun()

        with btn_col2:
            # Quick category move
            cur_cat = ev.get("category", "Other")
            avail_cats = km.get_categories()
            cur_idx = avail_cats.index(cur_cat) if cur_cat in avail_cats else 0
            new_cat_choice = st.selectbox(
                "Move",
                options=avail_cats,
                index=cur_idx,
                key=f"cat_sel_{ev['id']}",
                label_visibility="collapsed",
            )
            if new_cat_choice != cur_cat:
                ev["category"] = new_cat_choice
                ev["needs_review"] = False
                ev["confidence"] = 1.0
                ev["classification_source"] = "manual_select"
                st.rerun()

        with btn_col3:
            # Move Up
            if st.button("⬆️", key=f"up_{ev['id']}", help="Move Up", disabled=(idx == 0)):
                _swap_events(idx, idx - 1)
                st.rerun()

        with btn_col4:
            # Move Down
            if st.button("⬇️", key=f"down_{ev['id']}", help="Move Down", disabled=(idx == total - 1)):
                _swap_events(idx, idx + 1)
                st.rerun()

        with btn_col5:
            if st.button("🗑️", key=f"del_{ev['id']}", help="Delete Event"):
                st.session_state.delete_target_id = ev["id"]
                st.session_state.delete_target_name = ev.get("event_name", "this event")
                st.session_state.active_modal = "delete_confirm"
                st.rerun()


def _swap_events(idx1: int, idx2: int):
    """Swap event order positions in session state."""
    events = st.session_state.events
    if 0 <= idx1 < len(events) and 0 <= idx2 < len(events):
        events[idx1], events[idx2] = events[idx2], events[idx1]


# -------------------------------------------------------------------------
# MODAL IMPLEMENTATIONS
# -------------------------------------------------------------------------

def _render_edit_modal(events: List[Dict], km: KeywordManager, session_temp_dir: Path):
    """Render the full event editing modal."""
    target_id = st.session_state.get("edit_target_id")
    ev = next((e for e in events if e["id"] == target_id), None)
    if not ev:
        st.session_state.active_modal = None
        return

    st.markdown("### ✏️ Edit Event Details")
    with st.form("edit_event_form", clear_on_submit=False):
        c1, c2 = st.columns([3, 2])
        with c1:
            name_val = st.text_input("Event Name*", value=ev.get("event_name", ""))
        with c2:
            cats = km.get_categories()
            cur_cat = ev.get("category", "Other")
            cat_idx = cats.index(cur_cat) if cur_cat in cats else 0
            cat_val = st.selectbox("Category*", options=cats, index=cat_idx)

        desc_val = st.text_area("Description*", value=ev.get("description", ""), height=120)

        m1, m2, m3 = st.columns(3)
        with m1:
            date_val = st.text_input("Date", value=ev.get("date", ""))
            time_val = st.text_input("Time", value=ev.get("time", ""))
        with m2:
            venue_val = st.text_input("Venue", value=ev.get("venue", ""))
            org_val = st.text_input("Organizer", value=ev.get("organizer", ""))
        with m3:
            dept_val = st.text_input("Department", value=ev.get("department", ""))
            club_val = st.text_input("Club / Chapter", value=ev.get("club", ""))

        m4, m5 = st.columns(2)
        with m4:
            part_val = st.text_input("Participants Count", value=ev.get("participants", ""))
        with m5:
            team_val = st.text_input("Team Size", value=ev.get("team_size", ""))

        # Current photographs management
        st.markdown("**Photographs Management:**")
        current_images = ev.get("images", [])
        if current_images:
            img_cols = st.columns(min(len(current_images), 4))
            for i, ipath in enumerate(current_images):
                with img_cols[i]:
                    if Path(ipath).exists():
                        st.image(str(ipath), use_container_width=True, caption=f"Photo {i+1}")

        remove_photos = st.checkbox("Remove all existing photographs", value=False)
        new_photos = st.file_uploader(
            "Add / Replace Photographs (Upload JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="edit_photo_upload",
        )

        sub_col1, sub_col2 = st.columns([1, 1])
        with sub_col1:
            save_clicked = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        with sub_col2:
            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

        if save_clicked:
            if not name_val.strip():
                st.error("Event Name cannot be empty.")
                return

            ev["event_name"] = name_val.strip()
            ev["category"] = cat_val
            ev["description"] = desc_val.strip()
            ev["date"] = date_val.strip()
            ev["time"] = time_val.strip()
            ev["venue"] = venue_val.strip()
            ev["organizer"] = org_val.strip()
            ev["department"] = dept_val.strip()
            ev["club"] = club_val.strip()
            ev["participants"] = part_val.strip()
            ev["team_size"] = team_val.strip()
            ev["needs_review"] = False
            ev["confidence"] = 1.0
            ev["classification_source"] = "manual_edit"

            if remove_photos:
                ev["images"] = []

            # Handle new photo uploads
            if new_photos:
                imgs_dir = session_temp_dir / "images"
                imgs_dir.mkdir(parents=True, exist_ok=True)
                uploaded_paths = []
                for uf in new_photos:
                    saved_path = ImageProcessor.save_image_bytes(
                        image_bytes=uf.getvalue(),
                        destination_dir=imgs_dir,
                        prefix="manual_photo",
                        extension=Path(uf.name).suffix.lower(),
                    )
                    uploaded_paths.append(str(saved_path))
                if remove_photos:
                    ev["images"] = uploaded_paths
                else:
                    ev["images"].extend(uploaded_paths)

            st.session_state.active_modal = None
            st.session_state.edit_target_id = None
            st.success("Event details updated successfully!")
            st.rerun()

        if cancel_clicked:
            st.session_state.active_modal = None
            st.session_state.edit_target_id = None
            st.rerun()


def _render_add_modal(km: KeywordManager, session_temp_dir: Path):
    """Render modal for manually adding a new event."""
    st.markdown("### ➕ Add New Event Manually")
    with st.form("add_event_form", clear_on_submit=False):
        c1, c2 = st.columns([3, 2])
        with c1:
            name_val = st.text_input("Event Name*", placeholder="e.g. National Hackathon 2026")
        with c2:
            cats = km.get_categories()
            cat_val = st.selectbox("Category*", options=cats)

        desc_val = st.text_area("Description*", placeholder="Provide details regarding the event...", height=100)

        m1, m2, m3 = st.columns(3)
        with m1:
            date_val = st.text_input("Date", placeholder="e.g. 25 October 2026")
            time_val = st.text_input("Time", placeholder="e.g. 9:00 AM - 5:00 PM")
        with m2:
            venue_val = st.text_input("Venue", placeholder="e.g. Auditorium")
            org_val = st.text_input("Organizer", placeholder="e.g. Department of CSE")
        with m3:
            dept_val = st.text_input("Department", placeholder="e.g. CSE")
            club_val = st.text_input("Club / Chapter", placeholder="e.g. IEEE Student Branch")

        new_photos = st.file_uploader(
            "Event Photographs (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="add_photo_upload",
        )

        sub_col1, sub_col2 = st.columns([1, 1])
        with sub_col1:
            add_clicked = st.form_submit_button("➕ Add Event", type="primary", use_container_width=True)
        with sub_col2:
            cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)

        if add_clicked:
            if not name_val.strip():
                st.error("Please provide an Event Name.")
                return

            saved_images = []
            if new_photos:
                imgs_dir = session_temp_dir / "images"
                imgs_dir.mkdir(parents=True, exist_ok=True)
                for uf in new_photos:
                    sp = ImageProcessor.save_image_bytes(
                        image_bytes=uf.getvalue(),
                        destination_dir=imgs_dir,
                        prefix="manual_add",
                        extension=Path(uf.name).suffix.lower(),
                    )
                    saved_images.append(str(sp))

            new_event = {
                "id": str(uuid.uuid4()),
                "event_name": name_val.strip(),
                "description": desc_val.strip(),
                "date": date_val.strip(),
                "time": time_val.strip(),
                "venue": venue_val.strip(),
                "organizer": org_val.strip(),
                "department": dept_val.strip(),
                "club": club_val.strip(),
                "participants": "",
                "team_size": "",
                "images": saved_images,
                "category": cat_val,
                "confidence": 1.0,
                "confidence_level": "HIGH",
                "classification_source": "manual_add",
                "needs_review": False,
                "suggested_categories": [],
                "source_file": "Manual Entry",
                "page_number": 1,
            }

            st.session_state.events.append(new_event)
            st.session_state.active_modal = None
            st.success("New event successfully added!")
            st.rerun()

        if cancel_clicked:
            st.session_state.active_modal = None
            st.rerun()


def _render_delete_modal():
    """Render confirmation dialog for deleting an event."""
    target_id = st.session_state.get("delete_target_id")
    target_name = st.session_state.get("delete_target_name", "this event")

    st.error(f"⚠️ Are you sure you want to remove **'{target_name}'**?")
    st.caption("This action will remove the event from statistics, pie charts, and the final PDF.")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🗑️ Remove Event", type="primary", use_container_width=True):
            st.session_state.events = [e for e in st.session_state.events if e["id"] != target_id]
            st.session_state.active_modal = None
            st.session_state.delete_target_id = None
            st.success("Event removed.")
            st.rerun()

    with c2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.active_modal = None
            st.session_state.delete_target_id = None
            st.rerun()


def _render_manage_categories_modal(km: KeywordManager):
    """Render dialog to manage categories, keywords, and weights."""
    st.markdown("### ⚙️ Category & Keyword Configuration")
    tabs = st.tabs(["Manage Categories", "Manage Keywords & Weights"])

    # Tab 1: Categories
    with tabs[0]:
        st.markdown("**Current Categories:**")
        cats = km.get_categories()
        for c in cats:
            c_col1, c_col2, c_col3 = st.columns([3, 1.5, 1])
            with c_col1:
                st.markdown(f"• **{c}**")
            with c_col2:
                color_pick = st.color_picker("Color", value=km.get_color(c), key=f"color_{c}", label_visibility="collapsed")
                if color_pick != km.get_color(c):
                    km.colors[c] = color_pick
            with c_col3:
                if c != "Other":
                    if st.button("Delete", key=f"del_cat_{c}"):
                        km.remove_category(c)
                        st.rerun()

        st.markdown("---")
        st.markdown("**Add New Category:**")
        nc1, nc2, nc3 = st.columns([3, 1, 1.5])
        with nc1:
            new_cat_name = st.text_input("Category Name", key="new_cat_input", placeholder="e.g. Cultural Fest")
        with nc2:
            new_cat_color = st.color_picker("Color", value="#8B5CF6", key="new_cat_color")
        with nc3:
            if st.button("➕ Add Category", key="add_cat_btn"):
                if new_cat_name and km.add_category(new_cat_name, new_cat_color):
                    st.success(f"Added category '{new_cat_name}'")
                    st.rerun()

    # Tab 2: Keywords & Weights
    with tabs[1]:
        sel_cat = st.selectbox("Select Category to manage keywords:", options=km.get_categories())
        keywords_dict = km.get_keywords(sel_cat)

        st.markdown(f"**Keywords for `{sel_cat}`:**")
        for kw, weight in list(keywords_dict.items()):
            kw_col1, kw_col2, kw_col3 = st.columns([3, 1.5, 1])
            with kw_col1:
                st.markdown(f"• `{kw}`")
            with kw_col2:
                new_w = st.number_input(f"Weight", min_value=1, max_value=10, value=weight, key=f"w_{sel_cat}_{kw}", label_visibility="collapsed")
                if new_w != weight:
                    km.set_keyword(sel_cat, kw, int(new_w))
            with kw_col3:
                if st.button("Remove", key=f"rem_kw_{sel_cat}_{kw}"):
                    km.remove_keyword(sel_cat, kw)
                    st.rerun()

        st.markdown("---")
        st.markdown(f"**Add Keyword to `{sel_cat}`:**")
        ak1, ak2, ak3 = st.columns([3, 1.5, 1.5])
        with ak1:
            new_kw_text = st.text_input("New Keyword / Phrase", key=f"new_kw_input_{sel_cat}")
        with ak2:
            new_kw_w = st.number_input("Weight (1-10)", min_value=1, max_value=10, value=3, key=f"new_kw_w_{sel_cat}")
        with ak3:
            if st.button("➕ Add Keyword", key=f"add_kw_btn_{sel_cat}"):
                if new_kw_text and km.set_keyword(sel_cat, new_kw_text, int(new_kw_w)):
                    st.success(f"Added keyword '{new_kw_text}'")
                    st.rerun()

    if st.button("Close Configuration", key="close_manage_modal"):
        st.session_state.active_modal = None
        st.rerun()
