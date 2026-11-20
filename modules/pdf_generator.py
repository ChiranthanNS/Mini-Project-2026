"""
Publication-Quality PDF Newsletter Generator using ReportLab.
Includes cover page, executive summary, category summary table, embedded pie chart,
category-wise event sections, multi-photo responsive gallery layouts, and running page numbering.
Strictly generates from the final user-approved state.
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from PIL import Image as PILImage

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    PageBreak,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas

from modules.image_processor import ImageProcessor
from modules.statistics import StatisticsEngine
from config import CATEGORY_COLORS


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that dynamically calculates total pages
    and prints running headers and 'Page X of Y' footers on all pages except the cover.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        # Omit header and footer on cover page (page 1)
        if self._pageNumber == 1:
            return

        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#4B5563"))

        page_w, page_h = letter
        margin = 40

        # Running Header
        header_text = getattr(self, "header_text", "Department Event Newsletter")
        self.drawString(margin, page_h - 30, header_text)
        self.setStrokeColor(colors.HexColor("#E5E7EB"))
        self.setLineWidth(0.75)
        self.line(margin, page_h - 35, page_w - margin, page_h - 35)

        # Running Footer
        footer_dept = getattr(self, "footer_dept", "Academic Newsletter")
        page_str = f"Page {self._pageNumber} of {total_pages}"
        self.line(margin, 40, page_w - margin, 40)
        self.drawString(margin, 26, footer_dept)
        self.drawRightString(page_w - margin, 26, page_str)

        self.restoreState()


class PDFNewsletterGenerator:
    """Generates the professional academic event newsletter PDF."""

    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Create typography styles for cover, headings, and descriptions."""
        self.styles.add(
            ParagraphStyle(
                name="CoverInst",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                textColor=colors.HexColor("#1E3A8A"),
                alignment=1, # Centered
                spaceAfter=6,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CoverDept",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#374151"),
                alignment=1,
                spaceAfter=20,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=26,
                leading=32,
                textColor=colors.HexColor("#1E3A8A"),
                alignment=1,
                spaceAfter=10,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CoverSubtitle",
                parent=self.styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=13,
                leading=17,
                textColor=colors.HexColor("#4B5563"),
                alignment=1,
                spaceAfter=25,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CoverMeta",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                textColor=colors.HexColor("#1F2937"),
                alignment=1,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionHeading",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=18,
                leading=22,
                textColor=colors.HexColor("#1E3A8A"),
                spaceBefore=14,
                spaceAfter=8,
                keepWithNext=True,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CategoryHeading",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=15,
                leading=19,
                textColor=colors.white,
                keepWithNext=True,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="EventTitle",
                parent=self.styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=13,
                leading=17,
                textColor=colors.HexColor("#111827"),
                spaceBefore=8,
                spaceAfter=4,
                keepWithNext=True,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="EventMetaText",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=13,
                textColor=colors.HexColor("#374151"),
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="EventDescText",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=14,
                textColor=colors.HexColor("#1F2937"),
                spaceBefore=6,
                spaceAfter=8,
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="NoPhotoText",
                parent=self.styles["Normal"],
                fontName="Helvetica-Oblique",
                fontSize=8.5,
                leading=11,
                textColor=colors.HexColor("#9CA3AF"),
                alignment=1,
            )
        )

    def generate_pdf(
        self,
        events: List[Dict],
        categories: List[str],
        report_settings: Dict,
        temp_dir: Path,
    ) -> Path:
        """
        Build and write the PDF document based on final approved events state.
        """
        # Document Setup: Letter size with 40pt margins
        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45,
        )

        flowables = []

        # ----------------------------------------------------
        # 1. COVER PAGE
        # ----------------------------------------------------
        inst_name = report_settings.get("institution_name", "Institution")
        dept_name = report_settings.get("department_name", "Department")
        report_title = report_settings.get("report_title", "Department Event Newsletter")
        subtitle = report_settings.get("subtitle", "")
        academic_year = report_settings.get("academic_year", "")
        reporting_period = report_settings.get("reporting_period", "")
        logo_path = report_settings.get("logo_path")

        flowables.append(Spacer(1, 20))

        # Logo if available
        if logo_path and Path(logo_path).exists():
            try:
                with PILImage.open(logo_path) as pimg:
                    orig_w, orig_h = pimg.size
                w, h = ImageProcessor.get_proportional_dimensions(orig_w, orig_h, 140, 100)
                rl_logo = RLImage(str(logo_path), width=w, height=h)
                rl_logo.hAlign = "CENTER"
                flowables.append(rl_logo)
                flowables.append(Spacer(1, 15))
            except Exception:
                pass

        flowables.append(Paragraph(inst_name.upper(), self.styles["CoverInst"]))
        flowables.append(Paragraph(dept_name, self.styles["CoverDept"]))

        # Elegant divider
        flowables.append(HRFlowable(width="80%", thickness=2, color=colors.HexColor("#D97706"), spaceAfter=25))

        flowables.append(Paragraph(report_title.upper(), self.styles["CoverTitle"]))
        if subtitle:
            flowables.append(Paragraph(subtitle, self.styles["CoverSubtitle"]))
        else:
            flowables.append(Spacer(1, 15))

        # Academic Metadata Box
        meta_data = [
            [
                Paragraph("<b>Academic Year:</b>", self.styles["EventMetaText"]),
                Paragraph(academic_year, self.styles["EventMetaText"]),
            ],
            [
                Paragraph("<b>Reporting Period:</b>", self.styles["EventMetaText"]),
                Paragraph(reporting_period, self.styles["EventMetaText"]),
            ],
            [
                Paragraph("<b>Total Events Documented:</b>", self.styles["EventMetaText"]),
                Paragraph(f"<b>{len(events)} Events</b>", self.styles["EventMetaText"]),
            ],
            [
                Paragraph("<b>Date of Compilation:</b>", self.styles["EventMetaText"]),
                Paragraph(datetime.now().strftime("%B %d, %Y"), self.styles["EventMetaText"]),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[160, 220])
        meta_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ])
        )
        meta_table.hAlign = "CENTER"
        flowables.append(meta_table)

        # Cover page break
        flowables.append(PageBreak())

        # ----------------------------------------------------
        # 2. EXECUTIVE SUMMARY & STATISTICS PAGE
        # ----------------------------------------------------
        flowables.append(Paragraph("EXECUTIVE SUMMARY & EVENT METRICS", self.styles["SectionHeading"]))
        flowables.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1E3A8A"), spaceAfter=15))

        summary_p = (
            f"This newsletter provides a structured compilation of <b>{len(events)} events</b> conducted during the "
            f"academic session {academic_year} ({reporting_period}). All events have been categorized and verified "
            "to reflect departmental contributions across co-curricular, technical, and community outreach domains."
        )
        flowables.append(Paragraph(summary_p, self.styles["EventDescText"]))
        flowables.append(Spacer(1, 10))

        # Generate and insert statistics table
        cat_counts = StatisticsEngine.get_category_counts(events, categories)
        summary_stats = StatisticsEngine.get_summary_stats(events, categories)

        table_rows = [[
            Paragraph("<b>Category</b>", self.styles["EventMetaText"]),
            Paragraph("<b>Count</b>", self.styles["EventMetaText"]),
            Paragraph("<b>Share (%)</b>", self.styles["EventMetaText"]),
        ]]
        for cat in categories:
            cnt = cat_counts.get(cat, 0)
            pct = summary_stats["category_percentages"].get(cat, 0.0)
            table_rows.append([
                Paragraph(f"<b>{cat}</b>", self.styles["EventMetaText"]),
                Paragraph(str(cnt), self.styles["EventMetaText"]),
                Paragraph(f"{pct}%", self.styles["EventMetaText"]),
            ])
        # Total row
        table_rows.append([
            Paragraph("<b>TOTAL</b>", self.styles["EventMetaText"]),
            Paragraph(f"<b>{len(events)}</b>", self.styles["EventMetaText"]),
            Paragraph("<b>100.0%</b>", self.styles["EventMetaText"]),
        ])

        stats_table = Table(table_rows, colWidths=[200, 80, 90])
        stats_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E2E8F0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ])
        )
        # Fix header text colors
        for i in range(3):
            table_rows[0][i].style.textColor = colors.white

        stats_table.hAlign = "CENTER"
        flowables.append(stats_table)
        flowables.append(Spacer(1, 15))

        # Insert Pie Chart Image
        chart_png_path = temp_dir / "pdf_pie_chart.png"
        chart_path = StatisticsEngine.generate_matplotlib_pie_chart(cat_counts, chart_png_path)
        if chart_path and chart_path.exists():
            rl_chart = RLImage(str(chart_path), width=390, height=260)
            rl_chart.hAlign = "CENTER"
            flowables.append(rl_chart)

        # Page break before category sections
        flowables.append(PageBreak())

        # ----------------------------------------------------
        # 3. CATEGORY-WISE EVENT SECTIONS
        # ----------------------------------------------------
        available_categories = [cat for cat in categories if cat_counts.get(cat, 0) > 0]

        for cat in available_categories:
            cat_events = [e for e in events if e.get("category") == cat]
            if not cat_events:
                continue

            cat_color = CATEGORY_COLORS.get(cat, "#1E3A8A")

            # Category Banner Table
            banner_cell = Paragraph(
                f"<b>{cat.upper()}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Total: {len(cat_events)} Events",
                self.styles["CategoryHeading"],
            )
            banner_table = Table([[banner_cell]], colWidths=[530])
            banner_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(cat_color)),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ])
            )
            flowables.append(banner_table)
            flowables.append(Spacer(1, 10))

            # Render each event in its EXACT APPROVED ORDER
            for idx, ev in enumerate(cat_events, start=1):
                event_flowables = []

                # Event Title
                event_name = ev.get("event_name", "Untitled Event")
                event_flowables.append(
                    Paragraph(f"<b>{idx}. {event_name}</b>", self.styles["EventTitle"])
                )

                # Metadata Table
                meta_items = []
                if ev.get("date"):
                    meta_items.append(["Date:", ev["date"]])
                if ev.get("time"):
                    meta_items.append(["Time:", ev["time"]])
                if ev.get("venue"):
                    meta_items.append(["Venue:", ev["venue"]])
                if ev.get("organizer"):
                    meta_items.append(["Organizer:", ev["organizer"]])
                if ev.get("department"):
                    meta_items.append(["Department:", ev["department"]])
                if ev.get("club"):
                    meta_items.append(["Club/Chapter:", ev["club"]])
                if ev.get("participants"):
                    meta_items.append(["Participants:", ev["participants"]])
                if ev.get("team_size"):
                    meta_items.append(["Team Size:", ev["team_size"]])

                if meta_items:
                    # Arrange into a 2-column or 4-column compact table
                    meta_table_data = []
                    # 2 items per row
                    for row_i in range(0, len(meta_items), 2):
                        item1 = meta_items[row_i]
                        row_cells = [
                            Paragraph(f"<b>{item1[0]}</b>", self.styles["EventMetaText"]),
                            Paragraph(item1[1], self.styles["EventMetaText"]),
                        ]
                        if row_i + 1 < len(meta_items):
                            item2 = meta_items[row_i + 1]
                            row_cells.extend([
                                Paragraph(f"<b>{item2[0]}</b>", self.styles["EventMetaText"]),
                                Paragraph(item2[1], self.styles["EventMetaText"]),
                            ])
                        else:
                            row_cells.extend(["", ""])
                        meta_table_data.append(row_cells)

                    compact_meta_table = Table(meta_table_data, colWidths=[80, 180, 80, 180])
                    compact_meta_table.setStyle(
                        TableStyle([
                            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#F3F4F6")),
                            ("TOPPADDING", (0, 0), (-1, -1), 3),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ])
                    )
                    event_flowables.append(compact_meta_table)
                    event_flowables.append(Spacer(1, 6))

                # Photographs layout
                photos = ev.get("images", [])
                valid_photos = [p for p in photos if Path(p).exists()]

                if valid_photos:
                    photo_flowable = self._build_photo_layout(valid_photos)
                    if photo_flowable:
                        event_flowables.append(photo_flowable)
                        event_flowables.append(Spacer(1, 6))
                else:
                    event_flowables.append(
                        Paragraph("<i>[No event photograph available]</i>", self.styles["NoPhotoText"])
                    )
                    event_flowables.append(Spacer(1, 4))

                # Description
                description = ev.get("description", "").strip()
                if description:
                    # Replace single newlines with spaces and double newlines with breaks
                    desc_paras = [p.strip() for p in description.split("\n\n") if p.strip()]
                    for p in desc_paras:
                        event_flowables.append(Paragraph(p, self.styles["EventDescText"]))

                # Event separator line
                event_flowables.append(
                    HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#D1D5DB"), spaceAfter=14)
                )

                # Keep heading and metadata together where possible
                flowables.append(KeepTogether(event_flowables[:2]))
                flowables.extend(event_flowables[2:])

            # Space between categories
            flowables.append(Spacer(1, 15))

        # Build document with NumberedCanvas
        def on_first_page(canvas_obj, doc_obj):
            pass

        def on_later_pages(canvas_obj, doc_obj):
            canvas_obj.header_text = f"{inst_name} — {report_title}"
            canvas_obj.footer_dept = dept_name

        doc.build(
            flowables,
            canvasmaker=NumberedCanvas,
            onFirstPage=on_first_page,
            onLaterPages=on_later_pages,
        )

        return self.output_path

    def _build_photo_layout(self, image_paths: List[str]) -> Optional[Table]:
        """
        Creates a responsive, aspect-ratio-preserving photo layout:
        - 1 photo: Large centered image (max width 460pt, max height 220pt)
        - 2 photos: Side-by-side grid (each max width 225pt, max height 160pt)
        - 3+ photos: 2-column or 3-column gallery grid without stretching
        """
        if not image_paths:
            return None

        rl_images = []
        for p in image_paths:
            try:
                with PILImage.open(p) as img:
                    orig_w, orig_h = img.size
                rl_images.append((p, orig_w, orig_h))
            except Exception:
                continue

        if not rl_images:
            return None

        # Case 1: Single Photo
        if len(rl_images) == 1:
            p, orig_w, orig_h = rl_images[0]
            w, h = ImageProcessor.get_proportional_dimensions(orig_w, orig_h, 440, 210)
            rl_img = RLImage(p, width=w, height=h)
            img_table = Table([[rl_img]], colWidths=[520])
            img_table.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ])
            )
            return img_table

        # Case 2: Exactly 2 Photos (Side-by-side)
        elif len(rl_images) == 2:
            row_cells = []
            for p, orig_w, orig_h in rl_images:
                w, h = ImageProcessor.get_proportional_dimensions(orig_w, orig_h, 240, 150)
                rl_img = RLImage(p, width=w, height=h)
                row_cells.append(rl_img)

            img_table = Table([row_cells], colWidths=[260, 260])
            img_table.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ])
            )
            return img_table

        # Case 3: 3 or more Photos (Gallery Grid, 2 per row)
        else:
            grid_rows = []
            current_row = []
            for p, orig_w, orig_h in rl_images:
                w, h = ImageProcessor.get_proportional_dimensions(orig_w, orig_h, 240, 135)
                current_row.append(RLImage(p, width=w, height=h))
                if len(current_row) == 2:
                    grid_rows.append(current_row)
                    current_row = []

            if current_row:
                current_row.append("")  # Empty cell for odd count
                grid_rows.append(current_row)

            img_table = Table(grid_rows, colWidths=[260, 260])
            img_table.setStyle(
                TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ])
            )
            return img_table
