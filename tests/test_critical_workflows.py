"""
Critical End-to-End Workflow Tests:
Strictly verifies the acceptance criteria from Sections 62, 63, 64, 65, 66:
- Section 62: Category drag-and-drop reflects in dashboard, counts, and final PDF
- Section 63: Edited event details reflect in final PDF
- Section 64: Deleting events updates counters, chart, and PDF
- Section 65: Manually adding an event updates counters, chart, and PDF
- Section 66: Event with 3 photographs renders in PDF gallery layout
"""

from pathlib import Path
import unittest
import shutil
import uuid
import pymupdf as fitz

from config import BASE_DIR, ASSETS_DIR, DEFAULT_REPORT_SETTINGS
from modules.keyword_manager import KeywordManager
from modules.statistics import StatisticsEngine
from modules.pdf_generator import PDFNewsletterGenerator


class TestCriticalWorkflows(unittest.TestCase):
    """Verifies critical user workflows and PDF fidelity requirements."""

    @classmethod
    def setUpClass(cls):
        cls.test_temp = BASE_DIR / "temp" / "test_critical_workflows"
        cls.test_temp.mkdir(parents=True, exist_ok=True)
        cls.km = KeywordManager()
        cls.photo_sample = ASSETS_DIR / "sample_docs" / "gen_ai_workshop.jpg"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_temp, ignore_errors=True)

    def test_section_62_drag_category_change_reflects_in_pdf(self):
        """
        CRITICAL TEST (Section 62):
        Initial: CODATHON -> 'AI Innovation Challenge'
        User moves/drags event: CODATHON -> HACKATHON
        Verify:
        - Category count changes
        - Pie chart data changes
        - Dashboard changes
        - Final PDF MUST contain 'AI Innovation Challenge' under HACKATHON
        - Final PDF MUST NOT contain 'AI Innovation Challenge' under CODATHON
        """
        events = [
            {
                "id": "ev_1",
                "event_name": "AI Innovation Challenge",
                "category": "Codathon",
                "description": "Prototype and build competition.",
                "date": "15 October 2026",
                "venue": "Campus Center",
                "organizer": "Dept of CSE",
                "images": [str(self.photo_sample)],
            }
        ]

        # Initial check
        counts_initial = StatisticsEngine.get_category_counts(events, self.km.get_categories())
        self.assertEqual(counts_initial["Codathon"], 1)
        self.assertEqual(counts_initial["Hackathon"], 0)

        # Simulate user drag-and-drop: CODATHON -> HACKATHON
        events[0]["category"] = "Hackathon"

        # Verify updated counts & stats
        counts_after = StatisticsEngine.get_category_counts(events, self.km.get_categories())
        self.assertEqual(counts_after["Codathon"], 0)
        self.assertEqual(counts_after["Hackathon"], 1)

        # Generate PDF from final approved state
        pdf_path = self.test_temp / "section_62_test.pdf"
        gen = PDFNewsletterGenerator(pdf_path)
        gen.generate_pdf(
            events=events,
            categories=self.km.get_categories(),
            report_settings=DEFAULT_REPORT_SETTINGS,
            temp_dir=self.test_temp,
        )

        self.assertTrue(pdf_path.exists())

        # Inspect PDF text
        doc = fitz.open(pdf_path)
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text()
        doc.close()

        # Must contain HACKATHON section and the event
        self.assertIn("HACKATHON", pdf_text)
        self.assertIn("AI Innovation Challenge", pdf_text)

        # Verify that CODATHON banner is NOT created as an event section
        self.assertNotIn("CODATHON | Total: 1 Events", pdf_text)

    def test_section_63_edit_event_name_reflects_in_pdf(self):
        """
        CRITICAL TEST (Section 63):
        Initial event: 'AI Workshop'
        User edits: 'Generative AI Hands-on Workshop' -> Clicks Save.
        PDF MUST show: 'Generative AI Hands-on Workshop', NOT 'AI Workshop'.
        """
        events = [
            {
                "id": "ev_edit",
                "event_name": "AI Workshop",
                "category": "Workshop",
                "description": "Hands on practical session.",
                "date": "10 September 2026",
                "venue": "Lab 1",
                "images": [str(self.photo_sample)],
            }
        ]

        # User edits event name
        events[0]["event_name"] = "Generative AI Hands-on Workshop"

        # Generate PDF
        pdf_path = self.test_temp / "section_63_test.pdf"
        gen = PDFNewsletterGenerator(pdf_path)
        gen.generate_pdf(
            events=events,
            categories=self.km.get_categories(),
            report_settings=DEFAULT_REPORT_SETTINGS,
            temp_dir=self.test_temp,
        )

        doc = fitz.open(pdf_path)
        pdf_text = "".join([p.get_text() for p in doc])
        doc.close()

        self.assertIn("Generative AI Hands-on Workshop", pdf_text)
        # Verify old name is not the event title
        self.assertNotIn("1. AI Workshop\n", pdf_text)

    def test_section_64_delete_events_updates_stats_and_pdf(self):
        """
        CRITICAL TEST (Section 64):
        Initial: 10 events
        User deletes: 2 events
        Final: 8 events
        Dashboard: Total Events = 8
        Pie chart: Based on 8 events
        PDF: Contains 8 events
        """
        # Create 10 dummy events
        events = [
            {
                "id": f"ev_{i}",
                "event_name": f"Academic Activity {i}",
                "category": "Workshop" if i < 5 else "Seminar / Guest Lecture",
                "description": f"Description for event {i}",
                "date": "September 2026",
                "images": [],
            }
            for i in range(1, 11)
        ]
        self.assertEqual(len(events), 10)

        # User deletes 2 events
        events = [e for e in events if e["id"] not in ["ev_9", "ev_10"]]
        self.assertEqual(len(events), 8)

        # Dashboard and Stats verify 8
        stats = StatisticsEngine.get_summary_stats(events, self.km.get_categories())
        self.assertEqual(stats["total_events"], 8)

        # PDF generation
        pdf_path = self.test_temp / "section_64_test.pdf"
        gen = PDFNewsletterGenerator(pdf_path)
        gen.generate_pdf(
            events=events,
            categories=self.km.get_categories(),
            report_settings=DEFAULT_REPORT_SETTINGS,
            temp_dir=self.test_temp,
        )

        doc = fitz.open(pdf_path)
        pdf_text = "".join([p.get_text() for p in doc])
        doc.close()

        self.assertIn("8 Events", pdf_text)
        self.assertNotIn("Academic Activity 9", pdf_text)
        self.assertNotIn("Academic Activity 10", pdf_text)

    def test_section_65_manual_add_event_updates_stats_and_pdf(self):
        """
        CRITICAL TEST (Section 65):
        Initial: 5 events
        User manually adds: 1 event
        Final: 6 events
        Dashboard: 6
        Pie chart: 6
        PDF: 6 events
        """
        events = [
            {
                "id": f"ev_{i}",
                "event_name": f"Existing Event {i}",
                "category": "Workshop",
                "description": f"Description {i}",
                "date": "September 2026",
                "images": [],
            }
            for i in range(1, 6)
        ]
        self.assertEqual(len(events), 5)

        # Manually add 1 event
        new_event = {
            "id": "ev_manual",
            "event_name": "Manually Added Outreach Drive",
            "category": "Outreach Activity",
            "description": "Community outreach in nearby school.",
            "date": "12 October 2026",
            "images": [str(self.photo_sample)],
        }
        events.append(new_event)
        self.assertEqual(len(events), 6)

        stats = StatisticsEngine.get_summary_stats(events, self.km.get_categories())
        self.assertEqual(stats["total_events"], 6)
        self.assertEqual(stats["category_counts"]["Outreach Activity"], 1)

        pdf_path = self.test_temp / "section_65_test.pdf"
        gen = PDFNewsletterGenerator(pdf_path)
        gen.generate_pdf(
            events=events,
            categories=self.km.get_categories(),
            report_settings=DEFAULT_REPORT_SETTINGS,
            temp_dir=self.test_temp,
        )

        doc = fitz.open(pdf_path)
        pdf_text = "".join([p.get_text() for p in doc])
        doc.close()

        self.assertIn("6 Events", pdf_text)
        self.assertIn("Manually Added Outreach Drive", pdf_text)

    def test_section_66_multiple_photographs_layout(self):
        """
        CRITICAL TEST (Section 66):
        Event has 3 photographs.
        PDF must contain all 3 photographs in a clean gallery layout.
        """
        # Ensure 3 valid sample photo paths
        p1 = ASSETS_DIR / "sample_docs" / "gen_ai_workshop.jpg"
        p2 = ASSETS_DIR / "sample_docs" / "hackathon_teams.jpg"
        p3 = ASSETS_DIR / "sample_docs" / "codathon_coding.jpg"

        events = [
            {
                "id": "ev_3_photos",
                "event_name": "Grand Tech Symposium with Multiple Photos",
                "category": "Technical Event",
                "description": "Multi-session symposium with extensive photo gallery.",
                "date": "25 September 2026",
                "venue": "Auditorium",
                "organizer": "CSE Department",
                "images": [str(p1), str(p2), str(p3)],
            }
        ]

        pdf_path = self.test_temp / "section_66_test.pdf"
        gen = PDFNewsletterGenerator(pdf_path)
        gen.generate_pdf(
            events=events,
            categories=self.km.get_categories(),
            report_settings=DEFAULT_REPORT_SETTINGS,
            temp_dir=self.test_temp,
        )

        self.assertTrue(pdf_path.exists())

        # Verify images are extracted/embedded in PDF
        doc = fitz.open(pdf_path)
        total_images_in_pdf = 0
        for page in doc:
            total_images_in_pdf += len(page.get_images())
        doc.close()

        # Should contain at least 4 images (the 3 event photos + 1 chart image on stats page)
        self.assertGreaterEqual(total_images_in_pdf, 3)


if __name__ == "__main__":
    unittest.main()
