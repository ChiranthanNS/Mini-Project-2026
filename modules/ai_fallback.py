"""
Optional AI/NLP Fallback Module using Google Gemini API v2.

Triggered ONLY as a fallback for ambiguous or low-confidence events when an API key is provided.
Enhanced with:
- Better prompt engineering with few-shot examples
- Structured JSON validation
- More robust error recovery
- Never blocks the application or crashes on API failure.
"""

from typing import Dict, List, Optional, Tuple
import os
import json
import re
from config import GEMINI_API_KEY, GEMINI_MODEL


class AIFallbackClassifier:
    """Optional Gemini API fallback for ambiguous or low-confidence event classification."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "") or GEMINI_API_KEY

    def is_available(self) -> bool:
        """Check if an API key is configured."""
        return bool(self.api_key and self.api_key.strip() and self.api_key not in ("your_api_key_here", "your_gemini_api_key_here"))

    def classify_fallback(
        self,
        event_data: Dict,
        valid_categories: List[str],
    ) -> Tuple[bool, str]:
        """
        Attempt AI classification for ambiguous or low-confidence event.
        Returns:
            Tuple[success: bool, message: str]
        If successful, updates event_data in-place.
        """
        if not self.is_available():
            return False, "Gemini API key is not configured. Retaining keyword classification."

        event_name = event_data.get("event_name", "")
        description = event_data.get("description", "")
        organizer = event_data.get("organizer", "")
        venue = event_data.get("venue", "")
        date = event_data.get("date", "")

        # Build a rich context string
        context_parts = [f"Event Name: {event_name}"]
        if organizer:
            context_parts.append(f"Organizer: {organizer}")
        if venue:
            context_parts.append(f"Venue: {venue}")
        if date:
            context_parts.append(f"Date: {date}")
        if description:
            context_parts.append(f"Description: {description[:800]}")
        combined_text = "\n".join(context_parts)

        # Category definitions to guide the AI
        category_guidance = {
            "Workshop": "Hands-on training, practical session, skill development, lab activity",
            "Hackathon": "Build-a-thon, ideathon, 24-hour coding and building challenge, prototype development",
            "Codathon": "Competitive programming contest, coding challenge, algorithmic competition",
            "Outreach Activity": "Community service, NSS, awareness campaign, school visit, blood donation, tree plantation",
            "Technical Event": "Tech fest, project exhibition, tech expo, science day, project fair",
            "Seminar / Guest Lecture": "Guest speaker, keynote address, expert talk, webinar, panel discussion, invited lecture",
            "Competition": "Quiz, paper presentation, poster presentation, debate, tournament, championship",
            "FDP / Certification": "Faculty development program, NPTEL/MOOC course, certification program, MoU, value-added course",
            "Other": "Orientation, inauguration, valedictory, cultural event, sports day, alumni meet",
        }

        guidance_text = "\n".join([
            f"- {cat}: {desc}"
            for cat, desc in category_guidance.items()
            if cat in valid_categories
        ])

        prompt = f"""You are an expert academic event classification assistant for Indian engineering colleges.

VALID CATEGORIES (choose exactly one):
{json.dumps(valid_categories)}

CATEGORY GUIDANCE:
{guidance_text}

ANALYZE THIS EVENT:
{combined_text}

INSTRUCTIONS:
1. Read the event name and description carefully
2. Match to the MOST specific valid category (not just the first keyword match)
3. FDP/Certification events are distinct from regular Workshops
4. A "Guest Lecture" with a named speaker → Seminar / Guest Lecture
5. Any competitive event with ranking/prizes → Competition or Codathon
6. Respond ONLY with valid JSON, no markdown, no explanation outside JSON

Respond with EXACTLY this JSON format:
{{
    "category": "<Exact Category Name from the list above>",
    "confidence": <float between 0.60 and 0.98>,
    "reason": "<one sentence explaining why this category was chosen>"
}}"""

        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(GEMINI_MODEL)

            generation_config = {
                "temperature": 0.1,   # Very deterministic for classification
                "max_output_tokens": 200,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
            )

            if not response or not response.text:
                return False, "AI response was empty. Retained keyword classification."

            # Clean JSON from response
            cleaned_text = response.text.strip()
            # Remove any markdown code fences
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", cleaned_text, flags=re.MULTILINE)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text, flags=re.MULTILINE).strip()
            # Extract JSON object if surrounded by other text
            json_match = re.search(r"\{[^}]+\}", cleaned_text, re.DOTALL)
            if json_match:
                cleaned_text = json_match.group(0)

            parsed = json.loads(cleaned_text)
            chosen_cat = parsed.get("category", "").strip()
            confidence = float(parsed.get("confidence", 0.75))
            reason = parsed.get("reason", "")

            # Exact match to valid categories (case-insensitive)
            matched_valid = None
            for cat in valid_categories:
                if cat.lower() == chosen_cat.lower():
                    matched_valid = cat
                    break

            # Fuzzy match if exact fails
            if not matched_valid:
                for cat in valid_categories:
                    if cat.lower() in chosen_cat.lower() or chosen_cat.lower() in cat.lower():
                        matched_valid = cat
                        break

            if not matched_valid:
                return False, f"AI suggested unknown category '{chosen_cat}'. Retaining keyword classification."

            # Update event data
            event_data["category"] = matched_valid
            event_data["confidence"] = round(max(0.55, min(0.98, confidence)), 2)
            event_data["confidence_level"] = "HIGH" if confidence >= 0.80 else "MEDIUM"
            event_data["classification_source"] = "ai_fallback"
            event_data["ai_reason"] = reason
            event_data["needs_review"] = False

            return True, f"AI classified as '{matched_valid}' ({int(confidence * 100)}%). Reason: {reason}"

        except json.JSONDecodeError as e:
            return False, f"AI returned invalid JSON ({str(e)}). Retaining keyword classification."
        except Exception as e:
            # Never block or crash
            return False, f"AI classification failed ({str(e)}). Retaining keyword classification."
