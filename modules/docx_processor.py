"""
DOCX Processing Module using python-docx.
Extracts paragraphs, headings, tables, and embedded photographs while preserving document order.
"""

from pathlib import Path
from typing import Dict, List, Optional
import docx
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.table import Table
from docx.text.paragraph import Paragraph
from modules.image_processor import ImageProcessor


class DOCXProcessor:
    """Extracts text, headings, tables, and embedded images from DOCX documents."""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def process_docx(self, docx_path: Path) -> Dict:
        """
        Process a DOCX document.
        Returns a dictionary containing:
            - success: bool
            - blocks: List[Dict] with type, text, style, images
            - all_images: List[str]
            - full_text: str
            - warnings: List[str]
            - error: Optional[str]
        """
        result = {
            "success": False,
            "filename": docx_path.name,
            "blocks": [],
            "all_images": [],
            "full_text": "",
            "warnings": [],
            "error": None,
        }

        try:
            doc = docx.Document(docx_path)
        except Exception as e:
            result["error"] = f"Unable to open DOCX document. File may be corrupted or invalid: {str(e)}"
            return result

        try:
            # 1. Map relationship IDs to extracted image filepaths
            rId_to_image_path = {}
            for rel_id, rel in doc.part.related_parts.items():
                if "image" in rel.content_type:
                    image_bytes = rel.blob
                    ext = "." + rel.content_type.split("/")[-1]
                    if ext == ".jpeg":
                        ext = ".jpg"
                    saved_img = ImageProcessor.save_image_bytes(
                        image_bytes=image_bytes,
                        destination_dir=self.temp_dir / "images",
                        prefix="docx_img",
                        extension=ext,
                    )
                    rId_to_image_path[rel_id] = str(saved_img)
                    result["all_images"].append(str(saved_img))

            full_text_parts = []

            # 2. Iterate elements in document order (paragraphs and tables)
            for child in doc.element.body:
                if isinstance(child, CT_P):
                    p = Paragraph(child, doc)
                    text = p.text.strip()
                    style_name = p.style.name if p.style else "Normal"
                    
                    # Check for images referenced in this paragraph's runs
                    p_images = []
                    for rId, img_path in rId_to_image_path.items():
                        if rId in child.xml and img_path not in p_images:
                            p_images.append(img_path)

                    is_heading = (
                        "heading" in style_name.lower()
                        or "title" in style_name.lower()
                        or any(run.bold for run in p.runs if len(run.text.strip()) > 3)
                    )

                    if text or p_images:
                        block_record = {
                            "type": "heading" if is_heading else "paragraph",
                            "text": text,
                            "style": style_name,
                            "images": p_images,
                        }
                        result["blocks"].append(block_record)
                        if text:
                            full_text_parts.append(text)

                elif isinstance(child, CT_Tbl):
                    tbl = Table(child, doc)
                    table_rows_text = []
                    table_rows_data = []

                    for row in tbl.rows:
                        row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        # Check images embedded inside cells of this row
                        row_images = []
                        for cell in row.cells:
                            for rId, img_path in rId_to_image_path.items():
                                if rId in cell._element.xml and img_path not in row_images:
                                    row_images.append(img_path)

                        if row_cells:
                            # Avoid duplicates when cells are merged horizontally
                            unique_cells = []
                            for c in row_cells:
                                if not unique_cells or c != unique_cells[-1]:
                                    unique_cells.append(c)
                            row_str = " | ".join(unique_cells)
                            table_rows_text.append(row_str)
                            table_rows_data.append({
                                "text": row_str,
                                "cells": unique_cells,
                                "images": row_images,
                            })

                    if table_rows_text:
                        table_content = "\n".join(table_rows_text)
                        result["blocks"].append({
                            "type": "table",
                            "text": table_content,
                            "style": "Table",
                            "images": [],
                            "rows": table_rows_data,
                        })
                        full_text_parts.append(table_content)

            result["full_text"] = "\n\n".join(full_text_parts)
            result["success"] = True

        except Exception as e:
            result["error"] = f"Error processing DOCX '{docx_path.name}': {str(e)}"
            return result

        return result
