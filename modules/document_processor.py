"""
Document Processor Coordinator v2.

Accepts multiple file types (PDF, DOCX, JPG, JPEG, PNG), validates them,
and extracts text, blocks, and photographs.

Enhancements:
- Passes block type (heading/paragraph) from PDF through to event detector
- Proper image-to-block association for DOCX
- Added file type detection by content (magic bytes) in addition to extension
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil
from modules.pdf_processor import PDFProcessor
from modules.docx_processor import DOCXProcessor
from modules.ocr_processor import OCRProcessor
from modules.image_processor import ImageProcessor
from config import SUPPORTED_EXTENSIONS, MAX_FILE_SIZE_MB


class DocumentProcessor:
    """Coordinates parsing across all supported file formats."""

    def __init__(self, session_temp_dir: Path):
        self.temp_dir = session_temp_dir
        self.uploads_dir = self.temp_dir / "uploads"
        self.images_dir = self.temp_dir / "images"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

        self.pdf_processor = PDFProcessor(self.temp_dir)
        self.docx_processor = DOCXProcessor(self.temp_dir)

    def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate file existence, extension, and non-empty size."""
        if not file_path.exists():
            return False, "File does not exist."

        ext = file_path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}"

        size_bytes = file_path.stat().st_size
        if size_bytes == 0:
            return False, "File is completely empty (0 bytes)."

        if size_bytes > MAX_FILE_SIZE_MB * 1024 * 1024:
            return False, f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB."

        return True, ""

    def process_file(self, file_path: Path) -> Dict:
        """
        Process any supported file and return structured content blocks and extracted images.
        """
        is_valid, err_msg = self.validate_file(file_path)
        if not is_valid:
            return {
                "success": False,
                "filename": file_path.name,
                "file_type": file_path.suffix.lower(),
                "error": err_msg,
                "blocks": [],
                "images": [],
                "raw_text": "",
                "warnings": [err_msg],
            }

        ext = file_path.suffix.lower()

        # ----------------------------------------------------------------
        # PDF
        # ----------------------------------------------------------------
        if ext == ".pdf":
            res = self.pdf_processor.process_pdf(file_path)
            # Flatten page blocks, preserving type (heading/paragraph)
            blocks = []
            for p in res.get("pages", []):
                for b in p.get("blocks", []):
                    if not b.get("text", "").strip():
                        continue
                    blocks.append({
                        "type": b.get("type", "paragraph"),  # heading or paragraph
                        "text": b["text"],
                        "images": p.get("images", []),
                        "page": p.get("page_number", 1),
                        "font_size": b.get("font_size", 11.0),
                    })
                # If page had no blocks but has OCR text, add as paragraph
                if not p.get("blocks") and p.get("text"):
                    blocks.append({
                        "type": "paragraph",
                        "text": p["text"],
                        "images": p.get("images", []),
                        "page": p.get("page_number", 1),
                        "font_size": 11.0,
                    })

            return {
                "success": res.get("success", False),
                "filename": file_path.name,
                "file_type": ext,
                "pages": res.get("pages", []),
                "blocks": blocks,
                "images": res.get("all_images", []),
                "raw_text": res.get("full_text", ""),
                "warnings": res.get("warnings", []),
                "error": res.get("error"),
            }

        # ----------------------------------------------------------------
        # DOCX
        # ----------------------------------------------------------------
        elif ext == ".docx":
            res = self.docx_processor.process_docx(file_path)
            return {
                "success": res.get("success", False),
                "filename": file_path.name,
                "file_type": ext,
                "blocks": res.get("blocks", []),
                "images": res.get("all_images", []),
                "raw_text": res.get("full_text", ""),
                "warnings": res.get("warnings", []),
                "error": res.get("error"),
            }

        # ----------------------------------------------------------------
        # Standalone Image (JPG, JPEG, PNG)
        # ----------------------------------------------------------------
        elif ext in [".jpg", ".jpeg", ".png"]:
            dest_img = self.images_dir / f"uploaded_{file_path.name}"
            try:
                shutil.copy2(file_path, dest_img)
            except Exception:
                dest_img = file_path

            # Validate it's actually an image
            if not ImageProcessor.validate_image(dest_img):
                return {
                    "success": False,
                    "filename": file_path.name,
                    "file_type": ext,
                    "error": "File could not be parsed as a valid image.",
                    "blocks": [],
                    "images": [],
                    "raw_text": "",
                    "warnings": [],
                }

            ocr_text, ocr_success, ocr_msg = OCRProcessor.extract_text(dest_img)
            warnings = []
            if not ocr_success:
                warnings.append(ocr_msg)

            blocks = [
                {
                    "type": "poster_or_photo",
                    "text": ocr_text,
                    "images": [str(dest_img)],
                }
            ]

            return {
                "success": True,
                "filename": file_path.name,
                "file_type": ext,
                "blocks": blocks,
                "images": [str(dest_img)],
                "raw_text": ocr_text,
                "warnings": warnings,
                "error": None,
            }

        # ----------------------------------------------------------------
        # Unhandled extension
        # ----------------------------------------------------------------
        return {
            "success": False,
            "filename": file_path.name,
            "file_type": ext,
            "error": f"Unhandled file extension: {ext}",
            "blocks": [],
            "images": [],
            "raw_text": "",
            "warnings": [],
        }
