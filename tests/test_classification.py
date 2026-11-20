"""
Unit Tests for Keyword Classification, Weighting, Confidence,
Ambiguity, Category Management, and Duplicate Detection.
"""

import unittest
from modules.keyword_manager import KeywordManager
from modules.classifier import EventClassifier
from modules.duplicate_detector import DuplicateDetector
from modules.ai_fallback import AIFallbackClassifier


class TestClassification(unittest.TestCase):
    """Test classification engine, scoring weights, ambiguity, and duplicates."""

    def setUp(self):
        self.km = KeywordManager()
        self.classifier = EventClassifier(self.km)

    def test_weighted_scoring_example_hackathon(self):
        """
        Verify the exact specification test case (Section 18):
        Event: 'AI Innovation Challenge 2026'
        Description: 'Students formed teams and developed working prototypes using artificial intelligence during an 8-hour challenge.'
        Expected: Category = Hackathon.
        """
        event = {
            "event_name": "AI Innovation Challenge 2026",
            "description": "Students formed teams and developed working prototypes using artificial intelligence during an 8-hour challenge.",
        }
        res = self.classifier.classify_event(event)
        self.assertEqual(res["category"], "Hackathon")
        self.assertGreaterEqual(res["confidence"], 0.70)
        self.assertEqual(res["classification_source"], "keyword")

    def test_workshop_classification(self):
        """Verify workshop with hands-on and practical sessions."""
        event = {
            "event_name": "Hands-on Deep Learning Workshop",
            "description": "Intensive skill development and practical session with tutorial and training.",
        }
        res = self.classifier.classify_event(event)
        self.assertEqual(res["category"], "Workshop")
        self.assertEqual(res["confidence_level"], "HIGH")

    def test_ambiguous_classification_flag(self):
        """
        Verify that genuinely ambiguous events trigger needs_review = True (Section 20).
        Uses an event with extremely weak evidence that scores below MIN_SCORE_THRESHOLD.
        """
        event = {
            "event_name": "Annual Academic Programme",
            "description": "A programme was conducted for the students of the department.",
        }
        res = self.classifier.classify_event(event)
        # Very weak evidence → needs_review should be True (low or zero score)
        self.assertTrue(res["needs_review"])
        self.assertGreaterEqual(len(res["suggested_categories"]), 0)

    def test_custom_category_and_keyword_management(self):
        """Verify custom category addition, keyword weight update, and re-classification."""
        # Add new category
        success = self.km.add_category("Robotics Fest", color="#10B981")
        self.assertTrue(success)
        self.assertIn("Robotics Fest", self.km.get_categories())

        # Set custom weighted keywords
        self.km.set_keyword("Robotics Fest", "robotics", 5)
        self.km.set_keyword("Robotics Fest", "arduino", 4)
        self.km.set_keyword("Robotics Fest", "bot war", 5)

        event = {
            "event_name": "Annual Bot War and Robotics Expo",
            "description": "Students assembled Arduino microcontrollers and fought in the bot war.",
        }

        # IMPORTANT: Rebuild patterns after keyword manager update before classifying
        res = self.classifier.reclassify_with_new_keywords(event)
        self.assertEqual(res["category"], "Robotics Fest")

        # Clean up
        self.km.remove_category("Robotics Fest")
        self.assertNotIn("Robotics Fest", self.km.get_categories())

    def test_duplicate_detection(self):
        """Test fuzzy duplicate detection on similar names and dates."""
        events = [
            {
                "id": "1",
                "event_name": "National Level AI Hackathon 2026",
                "date": "20 September 2026",
                "description": "12 hour innovation sprint.",
                "source_file": "file1.pdf",
            },
            {
                "id": "2",
                "event_name": "National Level AI Hackathon 2026 - Final",
                "date": "20 September 2026",
                "description": "12 hour innovation sprint with prototypes.",
                "source_file": "file2.pdf",
            },
            {
                "id": "3",
                "event_name": "Blood Donation Camp",
                "date": "10 October 2026",
                "description": "Community service drive.",
                "source_file": "file3.pdf",
            },
        ]
        dupes = DuplicateDetector.find_duplicate_pairs(events)
        self.assertEqual(len(dupes), 1)
        self.assertEqual(dupes[0]["event_a_id"], "1")
        self.assertEqual(dupes[0]["event_b_id"], "2")

    def test_ai_fallback_with_missing_key(self):
        """Verify that AI fallback cleanly retains keyword result when API key is missing."""
        ai = AIFallbackClassifier(api_key="")
        self.assertFalse(ai.is_available())
        event = {"event_name": "Test", "description": "Desc", "category": "Other"}
        success, msg = ai.classify_fallback(event, self.km.get_categories())
        self.assertFalse(success)
        self.assertEqual(event["category"], "Other")

    def test_fdp_certification_category(self):
        """Verify FDP / Certification category is correctly identified."""
        event = {
            "event_name": "NPTEL Certification Course Completion Ceremony",
            "description": "Faculty development program and value-added certification course conducted under SWAYAM platform.",
        }
        res = self.classifier.classify_event(event)
        self.assertEqual(res["category"], "FDP / Certification")
        self.assertEqual(res["confidence_level"], "HIGH")

    def test_outreach_activity(self):
        """Verify outreach / community service classification."""
        event = {
            "event_name": "NSS Blood Donation Drive",
            "description": "Community outreach and social service activity. Blood donation camp conducted at the rural village.",
        }
        res = self.classifier.classify_event(event)
        self.assertEqual(res["category"], "Outreach Activity")
        self.assertEqual(res["confidence_level"], "HIGH")

    def test_negation_handling(self):
        """Verify negation correctly suppresses keyword scoring."""
        event = {
            "event_name": "Notice of Cancellation",
            "description": "This was not a workshop or hackathon. No seminar, guest lecture, or coding competition was conducted.",
        }
        res = self.classifier.classify_event(event)
        # With negation, the dominant category should be Other or low confidence
        self.assertEqual(res["category"], "Other")
        # Confidence should be low since negation suppresses all event keywords
        self.assertLess(res["confidence"], 0.60)


if __name__ == "__main__":
    unittest.main()
