"""
Unit Tests for Document and Information Extraction:
PDF, DOCX, Images, OCR, and Multi-Signal Event Detection.
"""

from pathlib import Path
import unittest
import shutil

from config import BASE_DIR, ASSETS_DIR
from modules.document_processor import DocumentProcessor
from modules.event_detector import EventDetector
from modules.event_extractor import EventExtractor
from modules.ocr_processor import OCRProcessor


class TestExtractionAndDetection(unittest.TestCase):
    """Test extraction across formats and heuristic event segmentation."""

    @classmethod
    def setUpClass(cls):
        cls.test_temp = BASE_DIR / "temp" / "test_extraction"
        cls.test_temp.mkdir(parents=True, exist_ok=True)
        cls.processor = DocumentProcessor(cls.test_temp)
        cls.samples_dir = ASSETS_DIR / "sample_docs"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_temp, ignore_errors=True)

    def test_pdf_multi_event_extraction(self):
        """Test multi-event PDF extraction and embedded images."""
        pdf_path = self.samples_dir / "cse_events_compendium.pdf"
        self.assertTrue(pdf_path.exists(), "Sample PDF must exist.")

        res = self.processor.process_file(pdf_path)
        self.assertTrue(res["success"])
        self.assertEqual(res["file_type"], ".pdf")
        self.assertGreaterEqual(len(res["pages"]), 4)
        self.assertGreaterEqual(len(res["images"]), 4)
        self.assertIn("Generative AI", res["raw_text"])

        # Detect discrete events
        events = EventDetector.detect_events_from_document(res)
        self.assertGreaterEqual(len(events), 4, "Should detect at least 4 discrete events from multi-page PDF.")

        # Extract structured data for first event
        ev1 = EventExtractor.extract_event_data(events[0])
        self.assertTrue(len(ev1["event_name"]) > 0)
        self.assertIn("12 September 2026", ev1["date"])
        self.assertIn("Computing Lab 3", ev1["venue"])
        self.assertGreaterEqual(len(ev1["images"]), 1)

    def test_docx_table_and_paragraph_extraction(self):
        """Test DOCX extraction including tables and headings."""
        docx_path = self.samples_dir / "department_guest_lectures.docx"
        self.assertTrue(docx_path.exists(), "Sample DOCX must exist.")

        res = self.processor.process_file(docx_path)
        self.assertTrue(res["success"])
        self.assertEqual(res["file_type"], ".docx")
        self.assertGreaterEqual(len(res["blocks"]), 4)
        self.assertIn("Quantum Computing", res["raw_text"])

        events = EventDetector.detect_events_from_document(res)
        self.assertGreaterEqual(len(events), 2, "Should detect seminar and competition from DOCX.")

    def test_poster_image_extraction(self):
        """Test standalone poster image processing."""
        poster_path = self.samples_dir / "cybersecurity_workshop_poster.png"
        self.assertTrue(poster_path.exists(), "Sample poster must exist.")

        res = self.processor.process_file(poster_path)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["images"]), 1)

    def test_empty_and_corrupt_files(self):
        """Test graceful handling of empty or corrupted files."""
        empty_file = self.test_temp / "empty.pdf"
        empty_file.write_bytes(b"")

        res = self.processor.process_file(empty_file)
        self.assertFalse(res["success"])
        self.assertIn("empty", res["error"].lower())

        corrupt_file = self.test_temp / "corrupt.pdf"
        corrupt_file.write_bytes(b"Not a valid PDF header content")

        res_corrupt = self.processor.process_file(corrupt_file)
        self.assertFalse(res_corrupt["success"])
        self.assertIsNotNone(res_corrupt["error"])

    def test_ocr_graceful_fallback(self):
        """Test that OCR extraction never crashes even with random or dummy inputs."""
        dummy_img = self.samples_dir / "gen_ai_workshop.jpg"
        text, success, msg = OCRProcessor.extract_text(dummy_img)
        self.assertIsInstance(text, str)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)


if __name__ == "__main__":
    unittest.main()
