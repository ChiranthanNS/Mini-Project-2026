"""
Utility script to generate realistic sample academic event documents:
1. Multi-event PDF with embedded images
2. DOCX document with tables and text
3. Event poster image
4. Institution logo
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pymupdf as fitz
import docx
from docx.shared import Inches, Pt, RGBColor

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DIR = BASE_DIR / "assets" / "sample_docs"
ASSETS_DIR = BASE_DIR / "assets"

SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def create_sample_photo(filename: str, title: str, bg_color="#1E3A8A", text_color="#FFFFFF") -> Path:
    """Create a sample event photo."""
    img = Image.new("RGB", (640, 420), color=bg_color)
    draw = ImageDraw.Draw(img)
    # Draw simple design
    draw.rectangle([(20, 20), (620, 400)], outline="#D97706", width=4)
    # Simple icon / text
    font = ImageFont.load_default()
    draw.text((40, 50), "ACADEMIC EVENT PHOTOGRAPH", fill="#FCD34D", font=font)
    draw.text((40, 180), title, fill=text_color, font=font)
    draw.text((40, 350), "Department of Computer Science & Engineering", fill="#94A3B8", font=font)

    out_path = SAMPLE_DIR / filename
    img.save(out_path)
    return out_path


def create_default_logo() -> Path:
    """Create a sample institution logo."""
    logo_path = ASSETS_DIR / "default_logo.png"
    if logo_path.exists():
        return logo_path

    img = Image.new("RGBA", (300, 300), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Circle emblem
    draw.ellipse([(15, 15), (285, 285)], fill="#1E3A8A", outline="#D97706", width=6)
    draw.ellipse([(35, 35), (265, 265)], fill="#FFFFFF", outline="#1E3A8A", width=3)
    # Emblem text
    font = ImageFont.load_default()
    draw.text((85, 90), "VVCE", fill="#1E3A8A", font=font)
    draw.text((65, 140), "ESTD. 1997", fill="#D97706", font=font)
    draw.text((55, 180), "EXCELLENCE", fill="#1E3A8A", font=font)

    img.save(logo_path)
    return logo_path


def generate_sample_pdf() -> Path:
    """Generate a multi-page PDF containing 4 distinct events with embedded photos."""
    pdf_path = SAMPLE_DIR / "cse_events_compendium.pdf"

    # Create dummy images to embed
    photo1 = create_sample_photo("gen_ai_workshop.jpg", "Hands-on Generative AI Workshop", bg_color="#1E3A8A")
    photo2 = create_sample_photo("hackathon_teams.jpg", "National AI Innovation Hackathon", bg_color="#4C1D95")
    photo3 = create_sample_photo("codathon_coding.jpg", "ByteCode Competitive Codathon", bg_color="#064E3B")
    photo4 = create_sample_photo("rural_outreach.jpg", "Digital Literacy Village Outreach", bg_color="#78350F")

    doc = fitz.open()

    # Event 1: Hands-on Workshop
    page1 = doc.new_page()
    text1 = """Event 1: Generative AI and LLM Workshop
Date: 12 September 2026
Time: 9:30 AM to 4:30 PM
Venue: Alan Turing Computing Lab 3
Organized by: Department of Computer Science & Engineering
Coordinator: Dr. K. Ramesh
Participants: 65 students

The Department conducted an intensive hands-on workshop focused on Generative AI architectures, prompt engineering, and building LLM agents. Students engaged in hands-on practical sessions and developed interactive question-answering systems using Python and open-source models. Skill development in real-time model deployment was demonstrated."""
    page1.insert_text((50, 60), text1, fontsize=12)
    # Embed photo1
    page1.insert_image(fitz.Rect(50, 320, 450, 560), filename=str(photo1))

    # Event 2: Hackathon
    page2 = doc.new_page()
    text2 = """Event 2: National AI Innovation Hackathon
Date: 20 September 2026
Time: 8:00 AM to 8:00 PM (12-Hour Challenge)
Venue: Main Campus Auditorium
Organizer: CSI Student Chapter & Dept of CSE
Participants: 120 students
Team Size: 4 members per team

A 12-hour buildathon and innovation challenge where inter-disciplinary student teams collaborated to develop functional prototypes solving civic and healthcare problems. Mentors from top technology enterprises guided the problem-solving and solution development sprints. Teams demonstrated working software prototypes to an industry jury panel."""
    page2.insert_text((50, 60), text2, fontsize=12)
    page2.insert_image(fitz.Rect(50, 320, 450, 560), filename=str(photo2))

    # Event 3: Codathon
    page3 = doc.new_page()
    text3 = """Event 3: ByteCode Competitive Codathon 2026
Date: 28 September 2026
Time: 2:00 PM to 6:00 PM
Venue: Central Computer Center
Organizer: Coding Club & Dept of CSE
Participants: 90 participants

A premier competitive programming contest featuring advanced algorithm challenges, dynamic programming, and graph data structure problems. Over 90 programmers participated in the 4-hour coding competition hosted on a competitive programming platform with automated test benchmarks."""
    page3.insert_text((50, 60), text3, fontsize=12)
    page3.insert_image(fitz.Rect(50, 300, 450, 540), filename=str(photo3))

    # Event 4: Outreach
    page4 = doc.new_page()
    text4 = """Event 4: Rural School Digital Literacy Outreach Program
Date: 05 October 2026
Time: 10:00 AM to 3:00 PM
Venue: Government Higher Primary School, Srirangapatna
Organizer: Social Outreach Forum & Dept of CSE
Participants: 45 student volunteers

As part of the institutional community service and social outreach initiative, faculty and student volunteers visited rural schools to conduct digital literacy awareness sessions. Children were introduced to computer basics, safe internet practices, and interactive educational software as part of this community service initiative."""
    page4.insert_text((50, 60), text4, fontsize=12)
    page4.insert_image(fitz.Rect(50, 300, 450, 540), filename=str(photo4))

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def generate_sample_docx() -> Path:
    """Generate a DOCX containing Seminar and Technical Events with table metadata."""
    docx_path = SAMPLE_DIR / "department_guest_lectures.docx"

    photo_seminar = create_sample_photo("seminar_speaker.jpg", "Expert Talk on Quantum Computing", bg_color="#312E81")

    doc = docx.Document()
    doc.add_heading("Department Activity Compilation: Seminars & Competitions", level=1)

    # Event 1: Seminar / Guest Lecture
    doc.add_heading("Distinguished Expert Lecture on Quantum Computing", level=2)
    doc.add_paragraph("Event Name: Distinguished Expert Lecture on Quantum Computing")

    table1 = doc.add_table(rows=4, cols=2)
    meta_pairs = [
        ("Date", "15 September 2026"),
        ("Venue", "Sir M. Visvesvaraya Seminar Hall"),
        ("Organizer", "Department of CSE"),
        ("Resource Person", "Dr. Arvind Sridhar, Senior Research Scientist, IBM Quantum"),
    ]
    for idx, (k, v) in enumerate(meta_pairs):
        row = table1.rows[idx]
        row.cells[0].text = k
        row.cells[1].text = v

    doc.add_paragraph(
        "The department organized an insightful seminar and guest lecture on Quantum Computing Foundations and Algorithms. "
        "The invited talk covered qubits, quantum superposition, entanglement, and quantum cryptography. "
        "Over 110 faculty and postgraduate researchers attended this academic expert session."
    )
    doc.add_picture(str(photo_seminar), width=Inches(4.5))

    # Event 2: Technical Competition
    doc.add_heading("State-Level Technical Project Exhibition & Competition", level=2)
    doc.add_paragraph("Event Name: State-Level Technical Project Exhibition & Competition")

    table2 = doc.add_table(rows=3, cols=2)
    meta_pairs2 = [
        ("Date", "22 September 2026"),
        ("Venue", "Campus Innovation Quadrangle"),
        ("Organizer", "IEEE Student Branch"),
    ]
    for idx, (k, v) in enumerate(meta_pairs2):
        row = table2.rows[idx]
        row.cells[0].text = k
        row.cells[1].text = v

    doc.add_paragraph(
        "A premier technical competition and project exhibition showcasing innovative engineering models. "
        "Student teams competed across IoT, Machine Learning, and Robotics tracks, judged by external evaluators. "
        "Prizes worth INR 50,000 were awarded during the championship contest."
    )

    doc.save(str(docx_path))
    return docx_path


def generate_sample_poster() -> Path:
    """Generate an event poster image."""
    poster_path = SAMPLE_DIR / "cybersecurity_workshop_poster.png"
    img = Image.new("RGB", (700, 900), color="#0F172A")
    draw = ImageDraw.Draw(img)

    draw.rectangle([(20, 20), (680, 880)], outline="#38BDF8", width=5)
    font = ImageFont.load_default()

    draw.text((120, 60), "DEPARTMENT OF COMPUTER SCIENCE", fill="#38BDF8", font=font)
    draw.text((160, 100), "PRESENTS HANDS-ON WORKSHOP", fill="#F8FAFC", font=font)

    draw.text((80, 220), "ADVANCED CYBERSECURITY & ETHICAL HACKING", fill="#F59E0B", font=font)
    draw.text((100, 260), "PRACTICAL TRAINING & LAB SESSIONS", fill="#E2E8F0", font=font)

    draw.text((60, 420), "Date: 18 September 2026", fill="#FFFFFF", font=font)
    draw.text((60, 460), "Time: 10:00 AM - 5:00 PM", fill="#FFFFFF", font=font)
    draw.text((60, 500), "Venue: Cyber Forensic Lab", fill="#FFFFFF", font=font)
    draw.text((60, 540), "Coordinator: Prof. Smitha Rao", fill="#FFFFFF", font=font)
    draw.text((60, 580), "Registration: Open to all Engineering Students", fill="#94A3B8", font=font)

    draw.text((60, 720), "A skill development and hands-on training workshop on penetration testing,", fill="#CBD5E1", font=font)
    draw.text((60, 750), "network vulnerability scanning, and cybersecurity defenses.", fill="#CBD5E1", font=font)

    img.save(poster_path)
    return poster_path


if __name__ == "__main__":
    print("Generating sample assets...")
    create_default_logo()
    generate_sample_pdf()
    generate_sample_docx()
    generate_sample_poster()
    print("Sample assets generated successfully!")
