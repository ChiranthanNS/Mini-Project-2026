"""
OCR Processing Module using Tesseract with:
- Image pre-processing: grayscale, contrast stretch, denoising, DPI upscaling
- Graceful fallback and error handling
- OCR confidence filtering (discard garbage text)
- Support for image bytes, PIL images, and file paths
"""

import shutil
from pathlib import Path
from typing import Optional, Tuple, Union
import os
from PIL import Image, ImageFilter, ImageEnhance, ImageOps
import pytesseract
from config import TESSERACT_CMD

FALLBACK_OCR_MESSAGE = (
    "Text could not be completely extracted from this file. "
    "Please review the detected event information manually."
)

# Minimum OCR text length to be considered valid (not garbage)
MIN_OCR_TEXT_LENGTH = 15


class OCRProcessor:
    """Manages Tesseract OCR detection, image pre-processing, and error handling."""

    _tesseract_available: Optional[bool] = None

    @classmethod
    def _initialize_tesseract(cls) -> bool:
        """Check if Tesseract binary is available on the system."""
        if cls._tesseract_available is not None:
            return cls._tesseract_available

        # 1. Check custom path from config / env
        if TESSERACT_CMD and Path(TESSERACT_CMD).exists():
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
            cls._tesseract_available = True
            return True

        # 2. Check standard Windows installation paths
        common_windows_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for path in common_windows_paths:
            if Path(path).exists():
                pytesseract.pytesseract.tesseract_cmd = path
                cls._tesseract_available = True
                return True

        # 3. Check if tesseract is on PATH
        which_path = shutil.which("tesseract")
        if which_path:
            pytesseract.pytesseract.tesseract_cmd = which_path
            cls._tesseract_available = True
            return True

        cls._tesseract_available = False
        return False

    @classmethod
    def is_available(cls) -> bool:
        """Return True if Tesseract OCR is available on the system."""
        return cls._initialize_tesseract()

    @classmethod
    def _preprocess_image(cls, pil_image: Image.Image) -> Image.Image:
        """
        Apply preprocessing pipeline to maximize OCR accuracy:
        1. Convert to RGB (handle RGBA/P modes)
        2. Upscale if too small (minimum 300 DPI equivalent)
        3. Convert to grayscale
        4. Auto-contrast stretch
        5. Mild unsharp mask (sharpening)
        6. Binarize with adaptive threshold approximation
        """
        try:
            # Step 1: Ensure RGB
            if pil_image.mode not in ("RGB", "L"):
                pil_image = pil_image.convert("RGB")

            # Step 2: Upscale small images for better OCR (minimum 1200px wide)
            w, h = pil_image.size
            if w < 1200:
                scale = max(1.5, 1200 / w)
                new_w = int(w * scale)
                new_h = int(h * scale)
                pil_image = pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # Step 3: Convert to grayscale
            gray = pil_image.convert("L")

            # Step 4: Auto contrast stretch
            gray = ImageOps.autocontrast(gray, cutoff=2)

            # Step 5: Enhance contrast
            enhancer = ImageEnhance.Contrast(gray)
            gray = enhancer.enhance(1.5)

            # Step 6: Sharpen
            gray = gray.filter(ImageFilter.SHARPEN)

            return gray
        except Exception:
            # If preprocessing fails, return original
            return pil_image

    @classmethod
    def _clean_ocr_text(cls, raw_text: str) -> str:
        """
        Post-process raw OCR output to fix common artifacts and normalize text.
        """
        import re
        # Remove null bytes and control characters
        text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", " ", raw_text)
        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Remove lines that are only punctuation/symbols (OCR noise)
        lines = text.split("\n")
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines with mostly non-alphanumeric characters (noise)
            alphanum_count = sum(1 for c in stripped if c.isalnum())
            if stripped and alphanum_count / max(len(stripped), 1) > 0.3:
                clean_lines.append(stripped)
        # Rejoin and normalize spaces
        text = "\n".join(clean_lines)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    @classmethod
    def extract_text(
        cls,
        image_input: Union[Image.Image, Path, str, bytes],
    ) -> Tuple[str, bool, str]:
        """
        Extract text from an image using Tesseract OCR with preprocessing.
        Returns:
            Tuple[extracted_text, success_bool, status_message]
        Never raises exceptions; gracefully returns fallback message.
        """
        if not cls.is_available():
            return (
                "",
                False,
                f"OCR is not configured or Tesseract is not installed. {FALLBACK_OCR_MESSAGE}",
            )

        try:
            pil_image = None
            if isinstance(image_input, Image.Image):
                pil_image = image_input.copy()
            elif isinstance(image_input, (str, Path)):
                pil_image = Image.open(image_input)
            elif isinstance(image_input, bytes):
                import io
                pil_image = Image.open(io.BytesIO(image_input))
            else:
                return ("", False, FALLBACK_OCR_MESSAGE)

            # Apply preprocessing for better accuracy
            preprocessed = cls._preprocess_image(pil_image)

            # Tesseract config: PSM 3 = fully automatic page segmentation
            # OEM 3 = both LSTM and legacy engine
            custom_config = r"--oem 3 --psm 3"
            text = pytesseract.image_to_string(preprocessed, config=custom_config)
            clean_text = cls._clean_ocr_text(text)

            if clean_text and len(clean_text) >= MIN_OCR_TEXT_LENGTH:
                return (clean_text, True, "Text extracted successfully using OCR.")
            else:
                # Try again with PSM 6 (assume a single uniform block of text)
                text2 = pytesseract.image_to_string(preprocessed, config="--oem 3 --psm 6")
                clean_text2 = cls._clean_ocr_text(text2)
                if clean_text2 and len(clean_text2) >= MIN_OCR_TEXT_LENGTH:
                    return (clean_text2, True, "Text extracted using OCR (single block mode).")
                return ("", False, FALLBACK_OCR_MESSAGE)

        except Exception as e:
            return (
                "",
                False,
                f"{FALLBACK_OCR_MESSAGE} (Detail: {str(e)})",
            )
