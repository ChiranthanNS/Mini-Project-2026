"""
PDF Processing Module v2 using PyMuPDF (fitz).

Enhancements:
- Font-size aware heading detection (larger text = heading candidate)
- Rich block extraction with bbox, font size, and text type hints
- OCR at higher DPI (200) for better scanned page accuracy
- Image size filtering with minimum thresholds (100x100px)
- Page-level image list with correct per-page association
- De-duplication using MD5 hash
"""

from pathlib import Path
from typing import Dict, List, Optional
import io
import hashlib
import pymupdf as fitz
from PIL import Image
from modules.image_processor import ImageProcessor
from modules.ocr_processor import OCRProcessor


# Minimum font size to be treated as a heading (points)
HEADING_FONT_SIZE_THRESHOLD = 13.0

# Minimum image dimensions to include (px)
MIN_IMG_WIDTH = 100
MIN_IMG_HEIGHT = 100


class PDFProcessor:
    """Extracts text (with heading detection) and embedded images from PDF documents."""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_pdf(self, pdf_path: Path) -> Dict:
        """
        Process a PDF file.
        Returns:
            - success: bool
            - pages: List[Dict] with page_number, text, blocks, images, is_scanned, ocr_used
            - all_images: List[str]
            - full_text: str
            - warnings: List[str]
            - error: Optional[str]
        """
        result = {
            "success": False,
            "filename": pdf_path.name,
            "pages": [],
            "all_images": [],
            "full_text": "",
            "warnings": [],
            "error": None,
        }

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            result["error"] = f"Unable to open PDF: {str(e)}"
            return result

        try:
            full_text_parts = []
            extracted_image_hashes: set = set()

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1

                # --- 1. Extract rich text blocks with font-size info ---
                page_text_blocks = []
                raw_dict = page.get_text("dict")
                plain_text_lines = []

                for block in raw_dict.get("blocks", []):
                    if block.get("type") != 0:  # 0 = text block
                        continue
                    block_lines_text = []
                    max_font_size = 0.0

                    for line in block.get("lines", []):
                        line_text = ""
                        line_max_size = 0.0
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            font_size = span.get("size", 0.0)
                            line_text += span_text
                            if font_size > line_max_size:
                                line_max_size = font_size
                        if line_text.strip():
                            block_lines_text.append(line_text.strip())
                            if line_max_size > max_font_size:
                                max_font_size = line_max_size

                    if block_lines_text:
                        combined = "\n".join(block_lines_text)
                        is_heading = (
                            max_font_size >= HEADING_FONT_SIZE_THRESHOLD
                            and len(combined) < 150
                            and "\n" not in combined
                        )
                        page_text_blocks.append({
                            "text": combined,
                            "type": "heading" if is_heading else "paragraph",
                            "font_size": max_font_size,
                            "bbox": block.get("bbox", []),
                        })
                        plain_text_lines.append(combined)

                plain_text = "\n".join(plain_text_lines).strip()

                # --- 2. OCR fallback for scanned pages ---
                is_scanned = False
                ocr_used = False

                if len(plain_text) < 40:
                    is_scanned = True
                    try:
                        pix = page.get_pixmap(dpi=200)
                        img_bytes = pix.tobytes("png")
                        ocr_text, ocr_success, ocr_msg = OCRProcessor.extract_text(img_bytes)
                        if ocr_success and ocr_text.strip():
                            plain_text = ocr_text.strip()
                            ocr_used = True
                            # Add as a single paragraph block
                            page_text_blocks.append({
                                "text": plain_text,
                                "type": "paragraph",
                                "font_size": 11.0,
                                "bbox": [],
                            })
                        else:
                            result["warnings"].append(
                                f"Page {page_num} in '{pdf_path.name}' appears scanned; OCR did not extract usable text. {ocr_msg}"
                            )
                    except Exception as ocr_err:
                        result["warnings"].append(f"Page {page_num} OCR failed: {str(ocr_err)}")

                # --- 3. Extract embedded images ---
                page_images: List[str] = []
                try:
                    image_list = page.get_images(full=True)
                    for img_info in image_list:
                        xref = img_info[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image.get("image")
                        image_ext = base_image.get("ext", "png")
                        width = base_image.get("width", 0)
                        height = base_image.get("height", 0)

                        if width < MIN_IMG_WIDTH or height < MIN_IMG_HEIGHT or not image_bytes:
                            continue

                        img_hash = hashlib.md5(image_bytes).hexdigest()
                        if img_hash in extracted_image_hashes:
                            continue
                        extracted_image_hashes.add(img_hash)

                        saved_path = ImageProcessor.save_image_bytes(
                            image_bytes=image_bytes,
                            destination_dir=self.temp_dir / "images",
                            prefix=f"pdf_p{page_num}",
                            extension=f".{image_ext}",
                        )
                        page_images.append(str(saved_path))
                        result["all_images"].append(str(saved_path))
                except Exception as img_err:
                    result["warnings"].append(f"Image extraction on page {page_num}: {str(img_err)}")

                # 4. If scanned and no embedded images, save page render as photo candidate
                if is_scanned and not page_images:
                    try:
                        pix = page.get_pixmap(dpi=150)
                        saved_path = ImageProcessor.save_image_bytes(
                            image_bytes=pix.tobytes("png"),
                            destination_dir=self.temp_dir / "images",
                            prefix=f"scanned_p{page_num}",
                            extension=".png",
                        )
                        page_images.append(str(saved_path))
                        result["all_images"].append(str(saved_path))
                    except Exception:
                        pass

                page_record = {
                    "page_number": page_num,
                    "text": plain_text,
                    "blocks": page_text_blocks,
                    "images": page_images,
                    "is_scanned": is_scanned,
                    "ocr_used": ocr_used,
                }
                result["pages"].append(page_record)
                # Collect full text — use plain_text from rawdict OR fallback to get_text()
                if plain_text:
                    full_text_parts.append(plain_text)
                elif not plain_text:
                    # Fallback: get_text() for compatibility
                    fallback_text = page.get_text("text").strip()
                    if fallback_text:
                        full_text_parts.append(fallback_text)
                        # Also update the page record text
                        page_record["text"] = fallback_text

            doc.close()
            result["full_text"] = "\n\n".join(full_text_parts)
            result["success"] = True

        except Exception as e:
            result["error"] = f"Error processing PDF '{pdf_path.name}': {str(e)}"
            return result

        return result
