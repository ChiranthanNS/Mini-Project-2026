# Automated Event Classification and Newsletter PDF Generator

An end-to-end full-stack Python application that automates the extraction, intelligent classification, human-in-the-loop verification, and publication-quality PDF newsletter generation for academic department and institutional events.

---

## 1. Project Title
**Automated Event Classification and Newsletter PDF Generator**

---

## 2. Problem Statement
Faculty members and department coordinators are regularly tasked with compiling departmental or institutional newsletters and annual activity reports. Event evidence is distributed across disparate files—multi-page event compilations in PDF, Word documents (DOCX) containing activity reports, brochures, promotional posters (JPG, PNG), and event photographs.

Historically, preparing newsletters requires:
- Manually reading through dozens of files.
- Identifying and categorizing event types (Workshops, Hackathons, Guest Lectures, Outreach, etc.).
- Copying event titles, dates, descriptions, venues, and attendee counts.
- Manually extracting and cropping photographs.
- Counting events category-wise and calculating statistics.
- Manually formatting a multi-page newsletter document.

This manual workflow is repetitive, error-prone, and can take days to finalize.

---

## 3. Objective
Develop a self-contained, session-based web application that:
1. Ingests heterogeneous event files (**PDF, DOCX, JPG, JPEG, PNG**) in bulk.
2. Extracts clean text and embedded photographs while preserving associations.
3. Automatically detects individual events across single and multi-event documents.
4. Classifies events using an accurate, configurable, weighted keyword scoring engine.
5. Flags ambiguous events with a "Needs Review" status and calculates confidence levels.
6. Provides an interactive **Drag-and-Drop Kanban Board** to adjust categories and reorder events in real-time.
7. Allows comprehensive editing of event details, manual event addition, deletion, and photo management.
8. Generates dynamic real-time statistics and category distribution pie charts.
9. Produces a formal, publication-ready PDF newsletter complete with an academic cover page, executive metrics, embedded pie chart, category sections, responsive multi-photo gallery layouts, and running page numbers.
10. Enforces privacy by requiring **no permanent database** and clearing all session artifacts on project completion.

---

## 4. Key Features
- **Multi-Format Ingestion**: Supports simultaneous upload of PDF, DOCX, JPG, JPEG, and PNG files with size validation.
- **Deep Document Processing**:
  - PyMuPDF (`pymupdf`) extracts text blocks and embedded image binaries.
  - `python-docx` extracts headings, paragraphs, formatted metadata tables, and embedded graphics.
  - Tesseract OCR handles scanned PDFs and image posters with a graceful fallback.
- **Multi-Signal Event Segmentation**: Heuristically detects individual events using headings, templates, numbered lists, date markers, and page boundaries.
- **Configurable Weighted Keyword Classifier**:
  - Normalizes text (case, punctuation, multi-word phrases, title boost).
  - Scores categories using configurable weights.
  - Computes confidence percentages (High, Medium, Low) and marks close-score ambiguities for review.
- **Optional Gemini AI Fallback**: If configured, triggers Google Gemini API solely for ambiguous/low-confidence items. Operates 100% offline without it.
- **Interactive Review & Arrange Workspace**:
  - Bidirectional drag-and-drop Kanban board (powered by HTML5/SortableJS custom component).
  - Fine-grained Move Up / Move Down buttons.
  - Modal editor for editing titles, descriptions, dates, venues, organizers, and photos.
  - Multi-photo management: preview, add, replace, or remove photographs.
  - Modal to manually add missed events.
  - Deletion with confirmation.
  - Real-time search across names, descriptions, organizers, venues, and departments.
  - Category filtering and live event counters.
  - Fuzzy duplicate event detection banner with "Keep Both" and "Remove Duplicate" options.
- **Live Analytics Dashboard**:
  - Interactive Plotly donut chart and horizontal bar chart updating synchronously with every drag, edit, or deletion.
  - Category breakdown summary cards.
- **Publication-Quality PDF Engine**:
  - Formal academic cover page with institution logo, department, academic year, reporting period, and metadata box.
  - Executive summary and category summary table.
  - Embedded high-resolution Matplotlib pie chart.
  - Category-wise sections respecting user reordering.
  - Responsive photo layouts: single large photo, side-by-side 2-photo grid, or multi-photo gallery grid without stretching.
  - Clean placeholder if no photograph is available.
  - Running headers and "Page X of Y" dynamic two-pass footers.
- **Privacy & Session Cleanup**: Session-scoped temporary storage with one-click "Start New Project" cleanup.

---

## 5. Workflow Architecture

```
[ Upload Files ]
       ↓
[ File Validation & Format Check ]
       ↓
[ Text & Embedded Image Extraction (PDF / DOCX / Images) ]
       ↓
[ OCR (If Scanned Page / Poster Detected) ]
       ↓
[ Multi-Signal Event Boundary Detection ]
       ↓
[ Metadata Extraction (Name, Date, Venue, Photos) ]
       ↓
[ Weighted Keyword Classification & Ambiguity Flagging ]
       ↓
[ Optional Gemini AI Fallback (If Configured & Ambiguous) ]
       ↓
[ Review & Arrange Workspace (Drag & Drop / Reorder / Edit / Add / Delete) ]
       ↓
[ Dynamic Analytics Dashboard & Final Pre-flight Validation ]
       ↓
[ Publication PDF Compilation (ReportLab + NumberedCanvas) ]
       ↓
[ Embedded PDF Preview & Download ]
       ↓
[ Start New Project / Session Cleanup ]
```

---

## 6. Architecture & Directory Structure

```
Mini Project/
├── app.py                      # Main Streamlit web application & router
├── config.py                   # Central settings, categories, keywords & weights
├── requirements.txt            # Production dependencies
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules for session files & cache
├── README.md                   # Complete documentation
│
├── modules/
│   ├── __init__.py
│   ├── keyword_manager.py      # Category & keyword configuration manager
│   ├── image_processor.py      # Aspect ratio math, resizing, thumbnails, placeholders
│   ├── ocr_processor.py        # Tesseract OCR integration with graceful fallback
│   ├── pdf_processor.py        # PyMuPDF text & embedded image extraction
│   ├── docx_processor.py       # python-docx parser for headings, tables & photos
│   ├── document_processor.py   # Unified document processing coordinator
│   ├── event_detector.py       # Multi-signal boundary detection for single/multi events
│   ├── event_extractor.py      # Regex & heuristic metadata extraction
│   ├── classifier.py           # Weighted keyword scoring & confidence engine
│   ├── ai_fallback.py          # Optional Google Gemini fallback classifier
│   ├── duplicate_detector.py   # Fuzzy similarity matcher on names, dates & desc
│   ├── statistics.py           # Metric calculation, Plotly & Matplotlib chart generation
│   └── pdf_generator.py        # ReportLab PDF compiler with NumberedCanvas
│
├── ui/
│   ├── __init__.py
│   ├── upload.py               # Drag-and-drop file upload interface
│   ├── processing.py           # Real-time multi-stage progress pipeline
│   ├── review.py               # Review workspace, search, filters & modals
│   ├── dashboard.py            # Analytics dashboard & dynamic charts
│   ├── settings.py             # Publication metadata & logo configuration
│   ├── pdf_preview.py          # Embedded base64 PDF viewer & download
│   └── components/
│       ├── kanban_board.py     # Streamlit custom component wrapper
│       └── kanban/
│           └── index.html      # SortableJS Kanban UI with bidirectional sync
│
├── assets/
│   ├── default_logo.png        # Default institution emblem
│   ├── generate_sample_docs.py # Sample generator script
│   └── sample_docs/            # Realistic sample files for immediate testing
│       ├── cse_events_compendium.pdf
│       ├── department_guest_lectures.docx
│       ├── cybersecurity_workshop_poster.png
│       └── ...
│
└── tests/
    ├── test_extraction.py           # Unit tests for PDF, DOCX, images & OCR
    ├── test_classification.py       # Unit tests for scoring, weights & ambiguity
    ├── test_critical_workflows.py   # Tests verifying sections 62-66 requirements
    └── run_all_tests.py             # Master test suite runner
```

---

## 7. Technology Stack
- **Frontend / Application Framework**: Streamlit (`streamlit>=1.35.0`)
- **Backend & Processing**: Python 3.10+ (tested on Python 3.14)
- **PDF Extraction**: PyMuPDF (`pymupdf>=1.24.0`)
- **DOCX Extraction**: `python-docx>=1.1.0`
- **OCR Engine**: Tesseract OCR via `pytesseract>=0.3.10`
- **Image Processing**: Pillow (`pillow>=10.0.0`)
- **PDF Compilation**: ReportLab (`reportlab>=4.1.0`)
- **Charts & Visualization**: Plotly (`plotly>=5.20.0`) and Matplotlib (`matplotlib>=3.8.0`)
- **Optional AI Fallback**: Google Generative AI (`google-generativeai>=0.5.0`)
- **Configuration & Environment**: `python-dotenv>=1.0.0`

---

## 8. Installation & Setup

### Prerequisites
- Python 3.10 or higher installed.
- (Optional) Tesseract OCR installed on your system if OCR on scanned images is needed:
  - Windows: Download installer from UB-Mannheim Tesseract OCR.
  - Linux: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`

### Step 1: Clone or Navigate to Directory
```bash
cd "c:\Users\chira\OneDrive\Desktop\Mini Project"
```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

---

## 9. Running Locally

To launch the web application:
```bash
streamlit run app.py
```

The application will start and open automatically in your browser at `http://localhost:8501`.

---

## 10. Environment Variables & Optional Gemini API Setup

Create a `.env` file in the project root based on `.env.example`:

```bash
# Optional: Google Gemini API Key for fallback classification
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Explicit path to Tesseract binary if not on PATH
# e.g., C:\Program Files\Tesseract-OCR\tesseract.exe
TESSERACT_CMD=
```

> **Note on AI Independence**: The application operates autonomously without any API keys. The Gemini API is strictly an optional fallback when keyword classification returns ambiguous results.

---

## 11. How Keyword Classification & Weighted Scoring Work

1. **Text Normalization**:
   - The event title and description are converted to lowercase.
   - Punctuation is stripped, and multiple whitespaces are collapsed.
2. **Title Weight Boost**:
   - Matches within the event title receive a **2.0x weight multiplier** because the title is the strongest categorical signal.
3. **Phrase Priority Matching**:
   - Multi-word phrases (e.g., `hands-on workshop`, `innovation challenge`, `guest lecture`) are sorted by length and matched with word boundaries before single words.
4. **Weighted Scoring**:
   - Each category receives a score:
     $$\text{Score} = \sum (\text{occurrences} \times \text{weight})$$
5. **Confidence Percentage**:
   - Calculated by combining the dominance ratio between the top-scoring category and the runner-up with the magnitude of the score:
     $$\text{Dominance} = \frac{S_1}{S_1 + S_2}$$
     $$\text{Confidence} = 0.55 \times \text{Dominance} + 0.45 \times \min(1.0, S_1 / 12)$$
   - Mapped to:
     - **HIGH CONFIDENCE**: $\ge 80\%$
     - **MEDIUM CONFIDENCE**: $50\% - 79\%$
     - **LOW CONFIDENCE**: $< 50\%$
6. **Ambiguity Flagging ("Needs Review")**:
   - If the difference between the 1st and 2nd category score is $\le 2$ or the top score is $< 3$, the event is flagged with a **⚠️ Needs Review** badge and suggested categories are provided.

---

## 12. Modifying Categories & Keywords

### Via UI:
1. In the **Review & Arrange** step, click **⚙️ Manage Categories**.
2. **Add Category**: Enter a category name and pick a theme color.
3. **Delete Category**: Click **Delete** next to any custom or default category.
4. **Manage Keywords**: Switch to the **Manage Keywords & Weights** tab, select a category, and modify keyword weights (1–10) or add new multi-word phrases.

### Via Code:
Edit `config.py`:
- Update `DEFAULT_CATEGORIES` list.
- Update `DEFAULT_KEYWORDS` dictionary with keywords and integer weights.
- Changes propagate across classification, the UI, charts, and the PDF generator.

---

## 13. How the PDF is Generated

The PDF compiler uses ReportLab with a dynamic `NumberedCanvas`:
1. **Cover Page**: Displays the institution logo, institution name, department, report title, subtitle, academic year, reporting period, total events count, and date. Header and footer are suppressed on this page.
2. **Executive Summary & Statistics Page**:
   - Provides summary text and a structured table of category event counts and percentage shares.
   - Embeds a 300-DPI Matplotlib pie chart reflecting the final approved event distribution.
3. **Category Sections**:
   - Only non-empty categories are created.
   - Events are rendered in the exact sequence approved by the user.
   - Metadata is displayed in a clean, bordered grid (Date, Time, Venue, Organizer, Department, Club, Participants).
4. **Responsive Photo Layout**:
   - **1 Photo**: Centered image up to 440pt width and 210pt height, preserving aspect ratio.
   - **2 Photos**: Side-by-side 2-column grid.
   - **3+ Photos**: Multi-row gallery grid (2 per row).
   - **0 Photos**: Clean placeholder notice (`[No event photograph available]`).
5. **Running Headers & Footers**: Two-pass canvas calculates total pages and prints running header rules and `Page X of Y` footers.

---

## 14. Automated Testing & Verification

A comprehensive test suite is included in `tests/`:

```bash
python tests/run_all_tests.py
```

### Verified Acceptance Tests:
1. **Multi-event PDF extraction**: Verifies extraction of 4+ events and images from sample PDF.
2. **DOCX table & paragraph extraction**: Verifies extraction of tables and headings.
3. **Poster image processing**: Verifies standalone image handling.
4. **OCR graceful fallback**: Confirms zero crashes when OCR binary is missing or on non-text images.
5. **Empty and corrupted file handling**: Validates clean user error reporting.
6. **Section 18 test case**: "AI Innovation Challenge 2026" classified as Hackathon with weighted score.
7. **Workshop classification**: "Hands-on Deep Learning Workshop" categorized with High confidence.
8. **Ambiguity detection**: Verifies close scores trigger `needs_review = True`.
9. **Category & keyword management**: Tests dynamic category addition and custom weight scoring.
10. **Duplicate detection**: Fuzzy string matching correctly identifies duplicate event pairs.
11. **Section 62 Critical Test**: Dragging "AI Innovation Challenge" from Codathon to Hackathon updates counts, dashboard, and ensures the PDF reflects Hackathon and NOT Codathon.
12. **Section 63 Critical Test**: Editing an event name to "Generative AI Hands-on Workshop" updates the PDF.
13. **Section 64 Critical Test**: Deleting 2 out of 10 events updates dashboard count to 8 and PDF count to 8.
14. **Section 65 Critical Test**: Manually adding an event increases count from 5 to 6 across dashboard and PDF.
15. **Section 66 Critical Test**: Event with 3 photographs renders all 3 in a gallery layout in the PDF.

---

## 15. Deployment (Streamlit Community Cloud)

This project is built for zero-configuration deployment on **Streamlit Community Cloud**:
1. Push repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/) and select your repository.
3. Main file path: `app.py`.
4. (Optional) In Advanced Settings, add `GEMINI_API_KEY` under Secrets.
5. Click **Deploy**.
6. The app requires no local database, dynamically manages temporary storage, and uses relative paths.

---

## 16. Known Limitations & Future Enhancements

### Current Limitations:
- Scanned PDF OCR speed depends on local CPU capabilities and Tesseract installation.
- Documents with highly irregular handwritten notes may require manual field editing.

### Future Enhancements:
- Multi-language OCR support for regional language event posters (e.g., Hindi, Kannada, Tamil).
- Support for exporting the newsletter in editable DOCX format in addition to PDF.
- PDF theme selector allowing faculty to toggle between Classic Academic, Modern Minimal, and Magazine layout styles.
