"""
Duplicate Event Detection Module.
Detects potential duplicates using fuzzy string similarity on event names, dates, and descriptions.
Never automatically deletes events without explicit user confirmation.
"""

from typing import Dict, List, Optional
import difflib
import re


class DuplicateDetector:
    """Detects potential duplicate events across uploaded documents."""

    @staticmethod
    def _clean_string(text: str) -> str:
        """Normalize string for fuzzy comparison."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def find_duplicate_pairs(cls, events: List[Dict]) -> List[Dict]:
        """
        Compare all pairs of events and flag potential duplicates.
        Returns a list of duplicate candidate dictionaries.
        """
        duplicates = []
        n = len(events)
        if n < 2:
            return duplicates

        for i in range(n):
            for j in range(i + 1, n):
                e1 = events[i]
                e2 = events[j]

                name1 = cls._clean_string(e1.get("event_name", ""))
                name2 = cls._clean_string(e2.get("event_name", ""))

                if not name1 or not name2:
                    continue

                name_sim = difflib.SequenceMatcher(None, name1, name2).ratio()

                date1 = cls._clean_string(e1.get("date", ""))
                date2 = cls._clean_string(e2.get("date", ""))
                dates_match = bool(date1 and date2 and (date1 == date2 or date1 in date2 or date2 in date1))

                desc1 = cls._clean_string(e1.get("description", "")[:250])
                desc2 = cls._clean_string(e2.get("description", "")[:250])
                desc_sim = difflib.SequenceMatcher(None, desc1, desc2).ratio() if (desc1 and desc2) else 0.0

                is_duplicate = False
                confidence_score = name_sim

                # High name similarity (> 85%)
                if name_sim >= 0.85:
                    is_duplicate = True
                # Moderate name similarity (> 70%) with exact date or strong description overlap
                elif name_sim >= 0.70 and (dates_match or desc_sim >= 0.65):
                    is_duplicate = True
                    confidence_score = max(name_sim, (name_sim + desc_sim) / 2)

                if is_duplicate:
                    duplicates.append({
                        "pair_id": f"{e1['id']}_{e2['id']}",
                        "event_a_id": e1["id"],
                        "event_b_id": e2["id"],
                        "event_a_name": e1.get("event_name", ""),
                        "event_b_name": e2.get("event_name", ""),
                        "event_a_date": e1.get("date", "N/A"),
                        "event_b_date": e2.get("date", "N/A"),
                        "event_a_file": e1.get("source_file", ""),
                        "event_b_file": e2.get("source_file", ""),
                        "similarity": int(confidence_score * 100),
                    })

        return duplicates
