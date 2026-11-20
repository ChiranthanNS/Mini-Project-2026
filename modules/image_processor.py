"""
Image processing module for handling event photographs, thumbnails, and PDF layout assets.
Preserves aspect ratio, avoids stretching, and validates image formats.
"""

from pathlib import Path
from typing import Optional, Tuple
import uuid
from PIL import Image, ImageDraw, ImageFont
import io


class ImageProcessor:
    """Handles image loading, aspect ratio preservation, resizing, and placeholder generation."""

    @staticmethod
    def validate_image(file_bytes_or_path) -> bool:
        """Check if image can be parsed by Pillow."""
        try:
            if isinstance(file_bytes_or_path, (str, Path)):
                with Image.open(file_bytes_or_path) as img:
                    img.verify()
                return True
            elif isinstance(file_bytes_or_path, bytes):
                with Image.open(io.BytesIO(file_bytes_or_path)) as img:
                    img.verify()
                return True
        except Exception:
            return False
        return False

    @staticmethod
    def save_image_bytes(
        image_bytes: bytes,
        destination_dir: Path,
        prefix: str = "img",
        extension: str = ".jpg",
    ) -> Path:
        """Save image bytes to destination folder with unique filename."""
        destination_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{prefix}_{uuid.uuid4().hex[:10]}{extension}"
        filepath = destination_dir / filename
        
        # Verify and re-encode to RGB JPEG/PNG for safety
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                # Handle RGBA conversion for JPEG
                if extension.lower() in [".jpg", ".jpeg"] and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(filepath, quality=90)
        except Exception:
            # Fallback to direct binary write
            filepath.write_bytes(image_bytes)

        return filepath

    @staticmethod
    def get_proportional_dimensions(
        original_width: int,
        original_height: int,
        max_width: float,
        max_height: float,
    ) -> Tuple[float, float]:
        """Calculate dimensions that fit within (max_width, max_height) without stretching."""
        if original_width <= 0 or original_height <= 0:
            return max_width, max_height

        aspect = original_width / original_height
        target_aspect = max_width / max_height

        if aspect > target_aspect:
            # Width limited
            width = max_width
            height = max_width / aspect
        else:
            # Height limited
            height = max_height
            width = max_height * aspect

        return width, height

    @staticmethod
    def create_placeholder_image(
        destination_dir: Path,
        text: str = "No Event Photograph Available",
        width: int = 600,
        height: int = 350,
    ) -> Path:
        """Create a clean, elegant academic placeholder image when no photo is provided."""
        destination_dir.mkdir(parents=True, exist_ok=True)
        img_path = destination_dir / "placeholder_no_photo.png"
        if img_path.exists():
            return img_path

        img = Image.new("RGB", (width, height), color="#F3F4F6")
        draw = ImageDraw.Draw(img)

        # Draw subtle border
        draw.rectangle([(2, 2), (width - 3, height - 3)], outline="#D1D5DB", width=2)
        
        # Draw camera/document icon outline
        cx, cy = width // 2, height // 2 - 25
        icon_w, icon_h = 70, 50
        draw.rounded_rectangle(
            [(cx - icon_w // 2, cy - icon_h // 2), (cx + icon_w // 2, cy + icon_h // 2)],
            radius=8,
            outline="#9CA3AF",
            width=3,
        )
        # Inner lens circle
        draw.ellipse([(cx - 15, cy - 15), (cx + 15, cy + 15)], outline="#9CA3AF", width=3)

        # Simple text label
        # In Pillow, default font is available
        try:
            # Attempt to use a basic font
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            draw.text(((width - text_w) // 2, cy + 45), text, fill="#6B7280", font=font)
        except Exception:
            pass

        img.save(img_path, format="PNG")
        return img_path

    @staticmethod
    def create_thumbnail(image_path: Path, max_size: Tuple[int, int] = (300, 200)) -> bytes:
        """Create a thumbnail in bytes for quick display."""
        try:
            with Image.open(image_path) as img:
                img_copy = img.copy()
                img_copy.thumbnail(max_size, Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                if img_copy.mode in ("RGBA", "P"):
                    img_copy = img_copy.convert("RGB")
                img_copy.save(buffer, format="JPEG", quality=85)
                return buffer.getvalue()
        except Exception:
            return b""
