"""
Event Detection Module v2.

Detects discrete events within single and multi-event documents using:
- Heading-based segmentation (DOCX blocks, PDF blocks)
- Page-level segmentation (multi-page PDFs)
- Table-based segmentation (event data in table rows)
- Regex-pattern segmentation (numbered/labeled event templates)
- Smart image proximity assignment (images assigned to nearest event heading)
- Font-size hints from PyMuPDF (large text → heading candidate)
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class EventDetector:
    """Segments raw document data into individual event candidate segments."""

    # Heading patterns indicating new event start
    EVENT_HEADER_PATTERNS = [
        re.compile(r"^(?:event|activity|program|report|session)\s*#?\s*\d+[\s:\.\-]+(.+)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^(?:event\s+name|title\s+of\s+(?:the\s+)?event|activity\s+name|name\s+of\s+(?:the\s+)?activity|name\s+of\s+the\s+programme|programme\s+name|program\s+name)[\s:\-]+(.+)$", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*([0-9]{1,2})\.\s+([A-Z][A-Za-z0-9\s\-:–]{4,80})$", re.MULTILINE),
        re.compile(r"^#+\s+(.+)$", re.MULTILINE),          # Markdown headings
        re.compile(r"^={3,}\s*(.+?)\s*={3,}$", re.MULTILINE),  # === EVENT ===
        re.compile(r"^-{3,}\s*(.+?)\s*-{3,}$", re.MULTILINE),  # --- EVENT ---
    ]

    # Keyword patterns that strongly signal an event title
    TITLE_KEYWORD_PATTERN = re.compile(
        r"\b(?:workshop|hackathon|codathon|seminar|webinar|bootcamp|guest lecture|expert talk|"
        r"symposium|conference|contest|competition|outreach|exhibition|fest|ideathon|challenge|"
        r"fdp|faculty development|certification|training program|technical event|tech fest|"
        r"guest speaker|keynote|panel discussion|tutorial|masterclass|hands.on)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detect_events_from_document(cls, doc_result: Dict) -> List[Dict]:
        """
        Segment a processed document result into individual event segments.
        Returns a list of event segments:
            - title_candidate: str
            - raw_text: str
            - images: List[str]
            - source_file: str
            - page_number: Optional[int]
        """
        filename = doc_result.get("filename", "Unknown Document")
        blocks = doc_result.get("blocks", [])
        pages = doc_result.get("pages", [])
        all_images = doc_result.get("images", [])
        raw_text = doc_result.get("raw_text", "").strip()

        if not raw_text and not all_images:
            return []

        # Strategy 1: Page-by-page multi-event check
        if len(pages) > 1:
            page_events = cls._try_page_level_segmentation(pages, filename)
            if page_events and len(page_events) > 1:
                return page_events

        # Strategy 2: Block / Heading segmentation (DOCX or structured PDF)
        if blocks:
            block_events = cls._try_block_level_segmentation(blocks, filename, all_images)
            if block_events and len(block_events) > 1:
                return block_events

        # Strategy 3: Table-based segmentation (event data stored as tables)
        if blocks:
            table_events = cls._try_table_segmentation(blocks, filename, all_images)
            if table_events and len(table_events) > 1:
                return table_events

        # Strategy 4: Text pattern segmentation (numbered/labeled events)
        text_events = cls._try_text_regex_segmentation(raw_text, filename, all_images)
        if text_events and len(text_events) > 1:
            return text_events

        # Strategy 5: Fallback — single event for this file
        return [
            {
                "title_candidate": cls._extract_first_title_candidate(raw_text, filename),
                "raw_text": raw_text,
                "images": all_images,
                "source_file": filename,
                "page_number": 1,
            }
        ]

    @classmethod
    def _try_page_level_segmentation(cls, pages: List[Dict], filename: str) -> Optional[List[Dict]]:
        """Check if distinct pages contain individual events."""
        detected = []
        for p in pages:
            p_text = p.get("text", "").strip()
            p_images = p.get("images", [])
            p_num = p.get("page_number", 1)

            if not p_text and not p_images:
                continue

            # Does this page have an event title indicator?
            title_match = cls._find_heading_in_text(p_text)
            if title_match or cls.TITLE_KEYWORD_PATTERN.search(p_text):
                detected.append({
                    "title_candidate": title_match or cls._extract_first_title_candidate(p_text, filename),
                    "raw_text": p_text,
                    "images": p_images,
                    "source_file": filename,
                    "page_number": p_num,
                })

        if len(detected) >= 2:
            return detected
        return None

    @classmethod
    def _try_block_level_segmentation(
        cls, blocks: List[Dict], filename: str, all_images: List[str]
    ) -> Optional[List[Dict]]:
        """Segment by headings in block structures, with smart image proximity assignment."""
        events: List[Dict] = []
        current_event: Optional[Dict] = None
        # Track images used in blocks to avoid reassigning
        block_assigned_images: set = set()

        for b in blocks:
            b_text = b.get("text", "").strip()
            b_type = b.get("type", "paragraph")
            b_images = b.get("images", [])
            b_page = b.get("page", 1)

            if not b_text and not b_images:
                continue

            is_new_event = False
            title_candidate = ""

            # Check if this block is a heading
            if b_type == "heading" and 3 < len(b_text) < 150:
                is_new_event = True
                title_candidate = b_text
            else:
                for pattern in cls.EVENT_HEADER_PATTERNS:
                    m = pattern.match(b_text)
                    if m:
                        is_new_event = True
                        title_candidate = m.group(1).strip() if m.lastindex and m.lastindex >= 1 else b_text
                        break

            if is_new_event:
                if current_event and (current_event["raw_text"] or current_event["images"]):
                    events.append(current_event)
                current_event = {
                    "title_candidate": title_candidate,
                    "raw_text": b_text,
                    "images": [img for img in b_images if img not in block_assigned_images],
                    "source_file": filename,
                    "page_number": b_page,
                }
                block_assigned_images.update(b_images)
            else:
                if current_event is None:
                    current_event = {
                        "title_candidate": cls._extract_first_title_candidate(b_text, filename),
                        "raw_text": b_text,
                        "images": [img for img in b_images if img not in block_assigned_images],
                        "source_file": filename,
                        "page_number": b_page,
                    }
                    block_assigned_images.update(b_images)
                else:
                    if b_text:
                        current_event["raw_text"] += "\n" + b_text
                    for img in b_images:
                        if img not in block_assigned_images and img not in current_event["images"]:
                            current_event["images"].append(img)
                            block_assigned_images.add(img)

        if current_event and (current_event["raw_text"] or current_event["images"]):
            events.append(current_event)

        # Distribute unassigned images to nearest events
        cls._assign_unassigned_images(events, all_images, block_assigned_images)

        return events if len(events) >= 2 else None

    @classmethod
    def _try_table_segmentation(
        cls, blocks: List[Dict], filename: str, all_images: List[str]
    ) -> Optional[List[Dict]]:
        """
        Detect event information stored in table rows.
        Handles both structured row dictionaries (with per-row images from docx)
        and newline-delimited table text.
        """
        table_blocks = [b for b in blocks if b.get("type") == "table"]
        if not table_blocks:
            return None

        MONTH_NAMES = {"january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november", "december"}

        events = []
        for tbl in table_blocks:
            rows_data = tbl.get("rows")
            
            # --- Rich rows mode (extracted directly with per-row images from DOCX) ---
            if rows_data and len(rows_data) >= 2:
                # Detect header in first row
                first_cells = [c.lower() for c in rows_data[0].get("cells", [])]
                is_header = any(
                    any(h in c for h in ["event", "month", "type", "name", "image", "description", "activity", "date", "venue"])
                    for c in first_cells
                )
                data_rows = rows_data[1:] if is_header else rows_data

                for r_info in data_rows:
                    cells = r_info.get("cells", [])
                    if not cells:
                        continue

                    # Filter out month separator rows (e.g., ['August 2025'])
                    distinct = set(c.strip() for c in cells if c.strip())
                    if len(distinct) == 1:
                        val = next(iter(distinct)).lower()
                        if any(m in val for m in MONTH_NAMES):
                            continue

                    # Find description (longest cell, usually >= 15 chars)
                    desc_candidate = max(cells, key=len) if cells else ""
                    if len(desc_candidate) < 15:
                        continue

                    # Pick best title candidate:
                    # Generic types that should not be used as the sole event name
                    GENERIC_TYPES = {
                        "department activity", "department activities", "club activity", "club activities",
                        "activity", "activities", "outreach activity", "outreach activities",
                        "faculty achievement", "faculty achievements", "faculty achivement",
                        "student achievement", "student achievements", "students achievement",
                        "stdents achivement", "event", "events"
                    }

                    title_candidate = ""

                    # Check all cells (prioritize cell 2 which is Event Name in standard academic table templates)
                    candidate_cells = []
                    for c in cells:
                        c_strip = c.strip()
                        if (c_strip and 
                            c_strip != desc_candidate and 
                            len(c_strip) <= 100 and
                            not any(m in c_strip.lower() for m in MONTH_NAMES)):
                            candidate_cells.append(c_strip)

                    # Look for a non-generic title first
                    for c_strip in candidate_cells:
                        if c_strip.lower() not in GENERIC_TYPES and len(c_strip) > 3:
                            title_candidate = c_strip
                            break

                    # If only generic types were found (e.g. "Department activity"), try to derive title from the description
                    if not title_candidate:
                        # Try to extract topic or action from first sentence of description
                        first_sentence = desc_candidate.split(".")[0].strip()
                        # Clean common prefixes like "Department of CSE conducted"
                        clean_lead = re.sub(
                            r"^(?:Department\s+of\s+[A-Za-z\(\)&,\s\-]+conducted|organized|conducted\s+a|organized\s+a)\s+",
                            "",
                            first_sentence,
                            flags=re.IGNORECASE
                        ).strip()
                        if 4 < len(clean_lead) <= 90:
                            title_candidate = clean_lead
                        elif candidate_cells:
                            title_candidate = candidate_cells[0]
                        else:
                            title_candidate = first_sentence[:70]

                    row_images = r_info.get("images", [])
                    raw_text = r_info.get("text", " | ".join(cells))

                    events.append({
                        "title_candidate": title_candidate,
                        "raw_text": raw_text,
                        "images": row_images,
                        "source_file": filename,
                        "page_number": 1,
                    })

                if len(events) >= 2:
                    return events

            # --- Fallback: Plain text table segmentation ---
            tbl_text = tbl.get("text", "")
            rows = [r.strip() for r in tbl_text.split("\n") if r.strip()]

            if len(rows) < 3:
                continue

            header_row = rows[0].lower()
            is_header = any(h in header_row for h in [
                "event", "name", "activity", "date", "venue", "participant", "topic"
            ])
            data_rows = rows[1:] if is_header else rows

            for idx, row in enumerate(data_rows):
                cells = [c.strip() for c in row.split("|") if c.strip()]
                if not cells:
                    continue

                distinct = set(cells)
                if len(distinct) == 1 and any(m in next(iter(distinct)).lower() for m in MONTH_NAMES):
                    continue

                desc_candidate = max(cells, key=len)
                if len(desc_candidate) < 15:
                    continue

                title_cand = cells[0] if len(cells[0]) < 80 else cells[0][:80]
                event_imgs = [all_images[idx]] if idx < len(all_images) else []

                events.append({
                    "title_candidate": title_cand,
                    "raw_text": row,
                    "images": event_imgs,
                    "source_file": filename,
                    "page_number": 1,
                })

        return events if len(events) >= 2 else None

    @classmethod
    def _try_text_regex_segmentation(
        cls, raw_text: str, filename: str, all_images: List[str]
    ) -> Optional[List[Dict]]:
        """Segment raw text using regular expressions for event templates."""
        pattern = re.compile(
            r"(?:^|\n)(?=(?:Event\s+#?\d+|Activity\s+#?\d+|Event\s+Name\s*:|"
            r"Name\s+of\s+(?:the\s+)?Event\s*:|Programme\s+Name\s*:|Program\s+Name\s*:|"
            r"\d+\.\s+[A-Z]))",
            re.IGNORECASE,
        )
        splits = pattern.split(raw_text)
        cleaned_splits = [s.strip() for s in splits if len(s.strip()) > 30]

        if len(cleaned_splits) >= 2:
            events = []
            n_imgs = len(all_images)
            for idx, chunk in enumerate(cleaned_splits):
                title = cls._extract_first_title_candidate(chunk, filename)
                # Smart image distribution: round-robin across events
                event_imgs = []
                if n_imgs > 0:
                    # Assign images proportionally
                    start_img = (idx * n_imgs) // len(cleaned_splits)
                    end_img = ((idx + 1) * n_imgs) // len(cleaned_splits)
                    event_imgs = all_images[start_img:end_img]

                events.append({
                    "title_candidate": title,
                    "raw_text": chunk,
                    "images": event_imgs,
                    "source_file": filename,
                    "page_number": 1,
                })
            return events

        return None

    @classmethod
    def _assign_unassigned_images(
        cls,
        events: List[Dict],
        all_images: List[str],
        already_assigned: set,
    ) -> None:
        """
        Assign remaining unassigned images to events that have no images.
        Uses round-robin among imageless events.
        """
        unassigned = [img for img in all_images if img not in already_assigned]
        if not unassigned or not events:
            return

        # Find events without any images
        imageless_events = [e for e in events if not e["images"]]
        if not imageless_events:
            # Give remaining to last event that has the fewest images
            target = min(events, key=lambda e: len(e["images"]))
            imageless_events = [target]

        for i, img in enumerate(unassigned):
            target_event = imageless_events[i % len(imageless_events)]
            if img not in target_event["images"]:
                target_event["images"].append(img)

    @classmethod
    def _find_heading_in_text(cls, text: str) -> Optional[str]:
        """Check first few lines of text for heading patterns."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            for pattern in cls.EVENT_HEADER_PATTERNS:
                m = pattern.match(line)
                if m:
                    return m.group(1).strip() if m.lastindex and m.lastindex >= 1 else line
            if cls.TITLE_KEYWORD_PATTERN.search(line) and len(line) < 120:
                return line
        return None

    @classmethod
    def _extract_first_title_candidate(cls, text: str, fallback_filename: str) -> str:
        """Heuristically extract the best candidate title from text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if not lines:
            stem = Path(fallback_filename).stem
            return stem.replace("_", " ").replace("-", " ").title()

        # Check for explicit labels: "Event Name: XYZ" / "Programme Name: XYZ"
        label_patterns = [
            r"^(?:Event\s+Name|Name\s+of\s+(?:the\s+)?Event|Title|Programme\s+Name|Program\s+Name|Activity\s+Name|Topic)\s*[:\-–]\s*(.+)$",
        ]
        for line in lines[:6]:
            for lp in label_patterns:
                match = re.search(lp, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        # Check for title keyword in first 4 lines
        for line in lines[:4]:
            if cls.TITLE_KEYWORD_PATTERN.search(line) and len(line) < 120:
                clean_line = re.sub(r"^(?:A\s+)?Report\s+on\s+(?:the\s+)?", "", line, flags=re.IGNORECASE)
                clean_line = re.sub(r"^(?:One\s+Day\s+|Two\s+Day\s+|Three\s+Day\s+)", "", clean_line, flags=re.IGNORECASE)
                return clean_line.strip()

        # Fallback to first line
        first_line = lines[0]
        first_line = re.sub(r"^(?:A\s+)?Report\s+on\s+(?:the\s+)?", "", first_line, flags=re.IGNORECASE)
        first_line = first_line.strip()
        if len(first_line) <= 120:
            return first_line

        return first_line[:100].strip() + "..."
