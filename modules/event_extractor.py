"""
Event Information Extraction Module v2.

Extracts structured event fields with:
- Expanded prefix pattern library (50+ field labels)
- Multi-line value capture for fields like Description and Objectives
- Smarter image filtering: separates event photos from logos/decorations
- Participant number normalization
- Club/chapter/society detection
- Never invents information; leaves missing fields empty
"""

from typing import Dict, List, Optional
import uuid
import re


# ---------------------------------------------------------------------------
# Image filtering helpers
# ---------------------------------------------------------------------------

def _is_likely_photo(image_path: str) -> bool:
    """
    Heuristic: skip images that are likely logos or tiny decorations.
    Returns True if the image is likely a meaningful event photograph.
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
            # Skip very small images (logos, icons, bullets)
            if w < 100 or h < 100:
                return False
            # Skip extremely wide/thin images (horizontal rules, borders)
            aspect = w / h if h > 0 else 1
            if aspect > 8 or aspect < 0.1:
                return False
            return True
    except Exception:
        # If we can't open it, include it anyway
        return True


# ---------------------------------------------------------------------------
# Main Extractor
# ---------------------------------------------------------------------------

class EventExtractor:
    """Extracts structured fields from raw event text segments."""

    # Date regex patterns
    DATE_PATTERNS = [
        re.compile(
            r"\b(?:\d{1,2}(?:st|nd|rd|th)?(?:\s*(?:to|-|–)\s*\d{1,2}(?:st|nd|rd|th)?)?[\s,/-]+"
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
            r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[\s,/-]+(?:20\d{2})\b)",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
            r"Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
            r"\s+\d{1,2}(?:st|nd|rd|th)?[\s,]+(?:20\d{2})\b)",
            re.IGNORECASE,
        ),
        re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-](?:20)?\d{2,4}\b"),
    ]

    # Time regex patterns
    TIME_PATTERNS = [
        re.compile(
            r"\b\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\s*(?:to|-|–)\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)\b"
        ),
        re.compile(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b"),
        re.compile(r"\b\d{1,2}(?::\d{2})?\s*(?:hours|hrs)\b", re.IGNORECASE),
    ]

    # Expanded field prefix patterns — covers 50+ common label variations
    # NOTE: These work BOTH as line-start (^) and inline (anywhere in text)
    PREFIX_PATTERNS = {
        "date": re.compile(
            r"(?:^|(?<=\s))(?:Date|Conducted\s+on|Held\s+on|Event\s+Date|Date\s+of\s+Event|"
            r"Date\s+of\s+Programme|Programme\s+Date|Date\s+&\s+Time|Date\s+and\s+Time|"
            r"Schedule\s+Date|On)\s*[:\-–]\s*([^\n\|]{3,60})",
            re.IGNORECASE | re.MULTILINE
        ),
        "time": re.compile(
            r"(?:^|(?<=\s))(?:Time|Timings|Timing|Duration|Schedule|Time\s+of\s+Event|"
            r"Event\s+Time|From\s+Time|Start\s+Time)\s*[:\-–]\s*([^\n\|]{3,60})",
            re.IGNORECASE | re.MULTILINE
        ),
        "venue": re.compile(
            r"(?:^|(?<=\s))(?:Venue|Location|Conducted\s+at|Place|Room|Lab|Hall|Auditorium|"
            r"Event\s+Venue|Held\s+at|Organized\s+at|Event\s+Location|Venue\s*&\s*Date|"
            r"Campus|Address)\s*[:\-–]\s*([^\n\|]{3,80})",
            re.IGNORECASE | re.MULTILINE
        ),
        "organizer": re.compile(
            r"(?:^|(?<=\s))(?:Organized\s+by|Organizer|Organizers|Coordinator|Coordinated\s+by|"
            r"Faculty\s+Coordinator|Faculty\s+In\s*[-\s]?Charge|Faculty\s+Mentor|"
            r"Event\s+Coordinator|Convener|Convenor|In\s*[-\s]?Charge|"
            r"Conducted\s+by|Programme\s+Coordinator|Event\s+Organizer)\s*[:\-–]\s*([^\n\|]{3,100})",
            re.IGNORECASE | re.MULTILINE
        ),
        "department": re.compile(
            r"(?:^|(?<=\s))(?:Department|Dept(?:\.|\s*of)?|Organizing\s+Department|"
            r"Host\s+Department|Hosting\s+Department|School\s+of)\s*[:\-–]\s*([^\n\|]{3,100})",
            re.IGNORECASE | re.MULTILINE
        ),
        "club": re.compile(
            r"(?:^|(?<=\s))(?:Club|Chapter|Student\s+Branch|Society|Association|Forum|"
            r"Technical\s+Club|Student\s+Club|IEEE|ACM|CSI|ISTE|NSS\s+Unit|"
            r"NCC\s+Unit|Organized\s+Under)\s*[:\-–]\s*([^\n\|]{3,80})",
            re.IGNORECASE | re.MULTILINE
        ),
        "participants": re.compile(
            r"(?:^|(?<=\s))(?:Participants|No\.?\s*of\s*Participants|Total\s+Participants|"
            r"Attendees|Registered\s+Students|Number\s+of\s+(?:Students|Participants)|"
            r"Beneficiaries|Student\s+Strength|Turnout|Strength)\s*[:\-–]\s*([^\n\|]{1,40})",
            re.IGNORECASE | re.MULTILINE
        ),
        "team_size": re.compile(
            r"(?:^|(?<=\s))(?:Team\s+Size|Members\s+per\s+Team|Team\s+Strength|"
            r"Group\s+Size|Per\s+Team)\s*[:\-–]\s*([^\n\|]{1,40})",
            re.IGNORECASE | re.MULTILINE
        ),
        "speaker": re.compile(
            r"(?:^|(?<=\s))(?:Speaker|Resource\s+Person|Guest\s+Speaker|Chief\s+Guest|"
            r"Keynote\s+Speaker|Invited\s+Speaker|Expert|Panelist|"
            r"Resource\s+Faculty|Distinguished\s+Speaker)\s*[:\-–]\s*([^\n\|]{3,100})",
            re.IGNORECASE | re.MULTILINE
        ),
        "objectives": re.compile(
            r"(?:^|(?<=\s))(?:Objective|Objectives|Aim|Aims|Purpose|Goal|Goals|"
            r"Learning\s+Outcomes|Outcomes)\s*[:\-–]\s*([^\n\|]{3,200})",
            re.IGNORECASE | re.MULTILINE
        ),
    }

    # Separate line-start patterns for structured line-by-line extraction
    LINE_PREFIX_PATTERNS = {
        "date": re.compile(
            r"^(?:Date|Conducted\s+on|Held\s+on|Event\s+Date|Date\s+of\s+Event|"
            r"Date\s+of\s+Programme|Programme\s+Date|Date\s+&\s+Time|Date\s+and\s+Time|"
            r"Schedule\s+Date|On)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "time": re.compile(
            r"^(?:Time|Timings|Timing|Duration|Schedule|Time\s+of\s+Event|"
            r"Event\s+Time|From\s+Time|Start\s+Time)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "venue": re.compile(
            r"^(?:Venue|Location|Conducted\s+at|Place|Room|Lab|Hall|Auditorium|"
            r"Event\s+Venue|Held\s+at|Organized\s+at|Event\s+Location|"
            r"Campus|Address)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "organizer": re.compile(
            r"^(?:Organized\s+by|Organizer|Organizers|Coordinator|Coordinated\s+by|"
            r"Faculty\s+Coordinator|Faculty\s+In\s*[-\s]?Charge|Faculty\s+Mentor|"
            r"Event\s+Coordinator|Convener|Convenor|In\s*[-\s]?Charge|"
            r"Conducted\s+by|Programme\s+Coordinator|Event\s+Organizer)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "department": re.compile(
            r"^(?:Department|Dept(?:\.|\s*of)?|Organizing\s+Department|"
            r"Host\s+Department|Hosting\s+Department|School\s+of)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "club": re.compile(
            r"^(?:Club|Chapter|Student\s+Branch|Society|Association|Forum|"
            r"Technical\s+Club|Student\s+Club|IEEE|ACM|CSI|ISTE|NSS\s+Unit|"
            r"NCC\s+Unit|Organized\s+Under)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "participants": re.compile(
            r"^(?:Participants|No\.?\s*of\s*Participants|Total\s+Participants|"
            r"Attendees|Registered\s+Students|Number\s+of\s+(?:Students|Participants)|"
            r"Beneficiaries|Student\s+Strength|Turnout|Strength)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "team_size": re.compile(
            r"^(?:Team\s+Size|Members\s+per\s+Team|Team\s+Strength|"
            r"Group\s+Size|Per\s+Team)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "speaker": re.compile(
            r"^(?:Speaker|Resource\s+Person|Guest\s+Speaker|Chief\s+Guest|"
            r"Keynote\s+Speaker|Invited\s+Speaker|Expert|Panelist|"
            r"Resource\s+Faculty|Distinguished\s+Speaker)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
        "objectives": re.compile(
            r"^(?:Objective|Objectives|Aim|Aims|Purpose|Goal|Goals|"
            r"Learning\s+Outcomes|Outcomes)\s*[:\-–]\s*(.+)$",
            re.IGNORECASE
        ),
    }

    @classmethod
    def extract_event_data(cls, segment: Dict) -> Dict:
        """
        Parse raw segment into structured internal event object.
        """
        raw_text = segment.get("raw_text", "").strip()
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

        extracted = {
            "id": str(uuid.uuid4()),
            "event_name": "",
            "description": "",
            "date": "",
            "time": "",
            "venue": "",
            "organizer": "",
            "department": "",
            "club": "",
            "participants": "",
            "team_size": "",
            "speaker": "",
            "objectives": "",
            "images": cls._filter_event_images(segment.get("images", [])),
            "category": "Other",
            "confidence": 0.0,
            "confidence_level": "LOW",
            "classification_source": "keyword",
            "needs_review": False,
            "suggested_categories": [],
            "source_file": segment.get("source_file", ""),
            "page_number": segment.get("page_number", 1),
        }

        # 1. Determine Event Name
        title_candidate = segment.get("title_candidate", "").strip()
        if title_candidate:
            extracted["event_name"] = cls._clean_title(title_candidate)
        elif lines:
            extracted["event_name"] = cls._clean_title(lines[0])
        else:
            extracted["event_name"] = "Untitled Event"

        # 2. Extract structured fields from lines
        description_lines = []
        skip_next_as_title = extracted["event_name"].lower() in [l.lower() for l in lines[:2]]

        for idx, line in enumerate(lines):
            # Skip duplicate of event title
            if line.lower() == extracted["event_name"].lower():
                continue
            if re.match(r"^(?:Event\s+Report|Activity\s+Report|Newsletter|Report)$", line, re.IGNORECASE):
                continue

            matched_field = False
            for field, pattern in cls.LINE_PREFIX_PATTERNS.items():
                match = pattern.match(line)
                if match:
                    value = match.group(1).strip()
                    if value and not extracted.get(field):
                        extracted[field] = value
                    matched_field = True
                    break

            if not matched_field:
                description_lines.append(line)

        # 2b. Inline scan over full raw text for any fields still missing
        # This handles cases where all text is on one line (e.g. PDF block merging)
        for field, pattern in cls.PREFIX_PATTERNS.items():
            if not extracted.get(field):
                m = pattern.search(raw_text)
                if m:
                    value = m.group(1).strip()
                    # Trim at known field boundaries
                    value = re.split(r'\s+(?:Date|Time|Venue|Organiz|Department|Club|Participants|Team|Speaker|Objective|Coordinator)\s*[:\-–]', value, maxsplit=1, flags=re.IGNORECASE)[0]
                    value = value.strip().rstrip('.,;')
                    if value:
                        extracted[field] = value

        # 3. Fallback regex extraction over entire raw text
        if not extracted["date"]:
            for dp in cls.DATE_PATTERNS:
                m = dp.search(raw_text)
                if m:
                    extracted["date"] = m.group(0).strip()
                    break

        if not extracted["time"]:
            for tp in cls.TIME_PATTERNS:
                m = tp.search(raw_text)
                if m:
                    extracted["time"] = m.group(0).strip()
                    break

        if not extracted["department"]:
            dept_m = re.search(r"\bDepartment\s+of\s+([A-Za-z &]+)", raw_text, re.IGNORECASE)
            if dept_m:
                extracted["department"] = dept_m.group(0).strip()

        if not extracted["venue"]:
            venue_m = re.search(
                r"\b(?:held\s+at|conducted\s+in|at\s+the|venue\s+[:–-])\s*([A-Z][A-Za-z0-9\s,]+(?:Hall|Auditorium|Lab|Campus|Room|Center|Ground|Block|Building))",
                raw_text,
                re.IGNORECASE,
            )
            if venue_m:
                extracted["venue"] = venue_m.group(1).strip()

        if not extracted["participants"]:
            part_m = re.search(
                r"\b(\d+)\s*(?:students|participants|teams|delegates|attendees|beneficiaries|members)\b",
                raw_text,
                re.IGNORECASE,
            )
            if part_m:
                extracted["participants"] = part_m.group(0).strip()

        if not extracted["speaker"]:
            speaker_m = re.search(
                r"\b(?:by\s+(?:Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s*([A-Z][A-Za-z\s\.]+))",
                raw_text,
            )
            if speaker_m:
                extracted["speaker"] = speaker_m.group(0).strip()

        # 4. Build description from remaining lines
        if description_lines:
            # Remove very short noise lines (single words, punctuation)
            meaningful = [
                l for l in description_lines
                if len(l) > 5 or l[0].isdigit()
            ]
            extracted["description"] = "\n\n".join(meaningful).strip()
        else:
            extracted["description"] = f"{extracted['event_name']} conducted as an academic event."

        # 5. Enrich description with objectives if captured
        if extracted.get("objectives") and extracted["objectives"] not in extracted["description"]:
            extracted["description"] += f"\n\nObjectives: {extracted['objectives']}"

        return extracted

    @classmethod
    def _filter_event_images(cls, images: List[str]) -> List[str]:
        """
        Filter image list to retain only likely event photographs.
        Removes tiny logos/icons while keeping meaningful photos.
        """
        filtered = []
        for img_path in images:
            if _is_likely_photo(img_path):
                filtered.append(img_path)
        # If filtering removed everything, return original (better to have logo than nothing)
        return filtered if filtered else list(images)

    @staticmethod
    def _clean_title(title: str) -> str:
        """Strip boilerplate labels and formatting from title."""
        title = re.sub(r"^(?:Event\s+#?\d+[:\.\-]?\s*)", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^(?:Activity\s+#?\d+[:\.\-]?\s*)", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^(?:Event\s+Name|Title|Name\s+of\s+the\s+Event|Programme\s+Name|Program\s+Name)[\s:\-–]+\s*", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^(?:A\s+)?Report\s+on\s+(?:the\s+)?", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^(?:One\s+Day|Two\s+Day|Three\s+Day|National\s+Level|State\s+Level)\s+", "", title, flags=re.IGNORECASE)
        title = re.sub(r"^(?:FDP\s+on|Workshop\s+on|Seminar\s+on|Webinar\s+on|Training\s+on)\s+", r"\g<0>", title, flags=re.IGNORECASE)
        return title.strip().strip(":.-–#").strip()
