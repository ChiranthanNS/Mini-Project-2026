"""
Configuration settings for the Automated Event Classification and Newsletter PDF Generator.
All default categories, keywords, weights, thresholds, and report settings are defined here.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
ASSETS_DIR = BASE_DIR / "assets"

# Supported input file extensions
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".jpg", ".jpeg", ".png"]
MAX_FILE_SIZE_MB = 50

# Default Categories
DEFAULT_CATEGORIES = [
    "Workshop",
    "Hackathon",
    "Codathon",
    "Outreach Activity",
    "Technical Event",
    "Seminar / Guest Lecture",
    "Competition",
    "FDP / Certification",
    "Other",
]

# Category Color Mapping (Hex for UI and PDF)
CATEGORY_COLORS = {
    "Workshop": "#2563EB",               # Vibrant Blue
    "Hackathon": "#7C3AED",              # Purple
    "Codathon": "#059669",               # Emerald Green
    "Outreach Activity": "#D97706",      # Amber / Orange
    "Technical Event": "#0284C7",        # Sky Blue
    "Seminar / Guest Lecture": "#4F46E5",# Indigo
    "Competition": "#DC2626",            # Crimson Red
    "FDP / Certification": "#0F766E",    # Teal
    "Other": "#6B7280",                  # Slate Gray
}

# Default Keywords and Weights — MASSIVELY EXPANDED (50+ per category)
DEFAULT_KEYWORDS = {
    "Workshop": {
        # Primary identifiers
        "workshop": 5,
        "training workshop": 5,
        "hands-on workshop": 5,
        "skill development workshop": 5,
        # Training terms
        "hands-on": 4,
        "hands on": 4,
        "training": 4,
        "training program": 4,
        "training session": 4,
        "interactive training": 4,
        "technical training": 4,
        "industry training": 4,
        "in-house training": 4,
        "in house training": 4,
        # Session types
        "practical session": 4,
        "lab session": 4,
        "laboratory session": 4,
        "demo session": 3,
        "demonstration session": 3,
        "practice session": 3,
        "interactive session": 3,
        "group session": 3,
        "group activity": 3,
        # Learning formats
        "skill development": 4,
        "skill building": 4,
        "learning session": 3,
        "tutorial": 3,
        "tutorials": 3,
        "masterclass": 4,
        "bootcamp": 4,
        "boot camp": 4,
        "crash course": 3,
        "intensive course": 3,
        "short course": 3,
        "mini course": 3,
        "workshop on": 4,
        # Tools and activities
        "tool demonstration": 3,
        "software training": 4,
        "hardware workshop": 4,
        "circuit building": 3,
        "prototype building": 3,
        "model making": 3,
        "capstone activity": 3,
        "group project": 3,
        "team activity": 3,
        "collaborative learning": 3,
        "experiential learning": 3,
        "maker workshop": 4,
    },
    "Hackathon": {
        # Primary identifiers
        "hackathon": 5,
        "hack": 4,
        "buildathon": 5,
        "build-a-thon": 5,
        "build a thon": 5,
        "ideathon": 5,
        "idea-thon": 5,
        "designathon": 5,
        "design-a-thon": 5,
        "innovathon": 5,
        # Innovation terms
        "innovation challenge": 5,
        "innovation event": 4,
        "innovation sprint": 4,
        "innovation fest": 4,
        "build challenge": 4,
        "prototype challenge": 4,
        "prototype development": 4,
        "prototype": 4,
        # Time-bound formats
        "24-hour": 4,
        "24 hour": 4,
        "36-hour": 4,
        "36 hour": 4,
        "48-hour": 4,
        "48 hour": 4,
        "overnight hackathon": 5,
        "marathon coding": 4,
        # Team building
        "team challenge": 4,
        "team project": 3,
        "group challenge": 3,
        "solution development": 3,
        "solution building": 3,
        "product development": 3,
        "product demo": 3,
        "product presentation": 3,
        # Problem-solving focus
        "problem statement": 4,
        "problem solving competition": 4,
        "real world problem": 3,
        "open innovation": 4,
        "social hackathon": 4,
        "hardware hack": 4,
        "hardware hackathon": 5,
        "software hackathon": 5,
        "ai hackathon": 5,
        "ml hackathon": 5,
        "project showcase": 3,
        "demo day": 4,
    },
    "Codathon": {
        # Primary identifiers
        "codathon": 5,
        "codeathon": 5,
        "coding contest": 5,
        "coding competition": 5,
        "programming contest": 5,
        "programming competition": 5,
        # Competitive programming
        "competitive programming": 5,
        "competitive coding": 5,
        "algorithmic competition": 4,
        "algorithm contest": 4,
        "data structures contest": 4,
        # Challenge types
        "coding challenge": 5,
        "programming challenge": 5,
        "algorithm challenge": 4,
        "algorithmic challenge": 4,
        "code sprint": 4,
        "coding sprint": 4,
        "code battle": 5,
        "coding battle": 5,
        "code war": 4,
        # Platforms
        "leetcode": 4,
        "hackerrank": 4,
        "codeforces": 4,
        "codechef": 4,
        "topcoder": 4,
        "geeksforgeeks": 3,
        "spoj": 3,
        # Specific formats
        "bug hunt": 4,
        "bug bounty": 4,
        "debugging contest": 5,
        "debug": 4,
        "debugging challenge": 4,
        "code hunt": 4,
        "online judge": 4,
        "ranked coding": 4,
        "timed coding": 4,
        "speed coding": 4,
        "programming olympiad": 5,
        "acm icpc": 5,
        "icpc": 4,
        "open coding": 4,
        "intra department coding": 4,
    },
    "Outreach Activity": {
        # Primary identifiers
        "outreach": 5,
        "community outreach": 5,
        "social outreach": 5,
        "rural outreach": 5,
        "school outreach": 5,
        # Awareness
        "awareness": 4,
        "awareness campaign": 5,
        "public awareness": 4,
        "awareness drive": 4,
        "awareness program": 4,
        "digital awareness": 4,
        "cyber awareness": 4,
        "health awareness": 4,
        # Community service
        "community": 3,
        "community service": 5,
        "community development": 4,
        "social service": 5,
        "social initiative": 4,
        "nss": 4,
        "nss activity": 5,
        "ncc": 3,
        "volunteer": 4,
        "volunteering": 4,
        "social responsibility": 4,
        "csr": 4,
        # Visits and engagement
        "school visit": 5,
        "village visit": 5,
        "rural visit": 5,
        "site visit": 3,
        "field visit": 3,
        "government school": 4,
        "primary school": 4,
        "students mentoring": 3,
        # Specific activities
        "blood donation": 5,
        "blood donation camp": 5,
        "tree plantation": 5,
        "plantation drive": 5,
        "cleanliness drive": 4,
        "swachh bharat": 4,
        "haritha keralam": 4,
        "ngo": 4,
        "charity": 3,
        "charity event": 3,
        "rural development": 4,
        "rural education": 4,
        "digital literacy": 4,
        "environmental awareness": 4,
        "gender awareness": 4,
        "anti-ragging": 3,
    },
    "Technical Event": {
        # Primary identifiers
        "technical event": 5,
        "tech event": 5,
        "technical program": 4,
        # Sessions
        "technical session": 5,
        "technical talk": 5,
        "technology session": 4,
        "technology talk": 4,
        "technical presentation": 4,
        "technical demonstration": 4,
        # Exhibitions and expos
        "tech expo": 5,
        "technology expo": 5,
        "project exhibition": 5,
        "project expo": 5,
        "project fair": 5,
        "science exhibition": 4,
        "science fair": 4,
        "innovation exhibition": 4,
        "prototype exhibition": 4,
        "tech showcase": 4,
        # Festivals
        "tech fest": 5,
        "techfest": 5,
        "technical festival": 5,
        "technology festival": 5,
        "tech symposium": 5,
        "technical symposium": 5,
        "devfest": 5,
        "developer festival": 4,
        # Conferences (technical)
        "technical conference": 4,
        "engineering conference": 4,
        "ieee conference": 4,
        "research presentation": 4,
        "paper presentation technical": 3,
        # Other technical
        "science day": 4,
        "engineers day": 4,
        "technology day": 4,
        "innovation day": 4,
        "demo day technical": 4,
        "technical quiz": 4,
        "technical workshop": 3,
        "capstone presentation": 4,
        "final year project": 3,
        "mini project": 3,
        "project review": 3,
        "technical review": 3,
    },
    "Seminar / Guest Lecture": {
        # Primary identifiers
        "seminar": 5,
        "guest lecture": 5,
        "guest speaker": 5,
        "guest talk": 5,
        "invited lecture": 5,
        "invited talk": 5,
        "invited speaker": 5,
        "expert talk": 5,
        "expert lecture": 5,
        "expert session": 5,
        # Speaker types
        "resource person": 5,
        "resource speaker": 4,
        "industry expert": 5,
        "industry professional": 4,
        "industry speaker": 5,
        "industry practitioner": 4,
        "eminent speaker": 4,
        "distinguished speaker": 4,
        "renowned speaker": 4,
        "motivational speaker": 4,
        # Formats
        "keynote": 5,
        "keynote address": 5,
        "keynote lecture": 5,
        "keynote session": 5,
        "lecture": 4,
        "public lecture": 4,
        "special lecture": 5,
        "endowment lecture": 4,
        "memorial lecture": 4,
        "industry talk": 5,
        "industry lecture": 5,
        "corporate talk": 4,
        # Online
        "webinar": 5,
        "online seminar": 5,
        "virtual seminar": 5,
        "online lecture": 4,
        "virtual lecture": 4,
        "zoom session": 3,
        "teams session": 3,
        # Discussion formats
        "panel discussion": 5,
        "panel session": 4,
        "roundtable": 4,
        "roundtable discussion": 4,
        "open discussion": 3,
        "interactive seminar": 4,
        "knowledge sharing": 3,
        "talk by": 4,
        "lecture by": 4,
        "address by": 3,
        "chief guest": 3,
    },
    "Competition": {
        # Primary identifiers
        "competition": 5,
        "competitive event": 5,
        "contest": 5,
        # Quiz
        "quiz": 5,
        "quiz competition": 5,
        "technical quiz": 4,
        "general quiz": 4,
        "online quiz": 4,
        "quiz contest": 5,
        # Presentation competitions
        "paper presentation": 5,
        "poster presentation": 5,
        "project presentation": 4,
        "research presentation": 4,
        "technical presentation": 4,
        # Championship types
        "championship": 5,
        "technical competition": 5,
        "inter-college competition": 5,
        "intra-college competition": 5,
        "national competition": 5,
        "state competition": 4,
        "university competition": 4,
        # Specific competitions
        "tournament": 4,
        "debate": 4,
        "debate competition": 5,
        "elocution": 4,
        "elocution competition": 5,
        "declamation": 4,
        "essay competition": 4,
        "essay writing": 4,
        "technical writing": 4,
        "technical event competition": 5,
        "treasure hunt": 4,
        "scavenger hunt": 4,
        "gaming tournament": 4,
        "esports": 4,
        "e-sports": 4,
        "robowar": 4,
        "robo race": 4,
        "circuit design contest": 4,
        "app development contest": 4,
        "web design competition": 4,
        "photography contest": 3,
        "innovation competition": 4,
        "entrepreneurship competition": 4,
        "business plan competition": 4,
        "startup competition": 4,
        "pitching competition": 4,
        "pitch competition": 4,
    },
    "FDP / Certification": {
        # FDP
        "fdp": 5,
        "faculty development program": 5,
        "faculty development programme": 5,
        "faculty workshop": 4,
        "faculty training": 4,
        "faculty seminar": 4,
        "staff development": 4,
        "staff training": 4,
        "professional development": 4,
        "teacher training": 4,
        "training for faculty": 5,
        # Certification
        "certification": 5,
        "certification program": 5,
        "certification course": 5,
        "certified": 4,
        "certificate course": 5,
        "certificate program": 5,
        "certificate of completion": 4,
        "online certification": 4,
        # NPTEL and similar
        "nptel": 5,
        "coursera": 4,
        "udemy": 4,
        "swayam": 5,
        "edx": 4,
        "mooc": 5,
        "massive open online course": 5,
        "online course": 3,
        "e-learning": 3,
        "e learning": 3,
        # Industry certification
        "aws certification": 5,
        "azure certification": 5,
        "google cloud certification": 5,
        "cisco certification": 5,
        "ccna": 5,
        "java certification": 4,
        "python certification": 4,
        "data science certification": 4,
        "machine learning certification": 4,
        "cybersecurity certification": 4,
        # MoU and collaboration
        "mou": 4,
        "memorandum of understanding": 4,
        "industry collaboration": 4,
        "industry academia": 4,
        "academia industry": 4,
        "industry tie-up": 4,
        "industry tie up": 4,
        "placement training": 4,
        "internship training": 4,
        "value added course": 5,
        "value-added course": 5,
        "bridge course": 4,
        "remedial course": 3,
    },
    "Other": {
        "general": 1,
        "orientation": 3,
        "induction": 3,
        "induction program": 3,
        "inauguration": 3,
        "inaugural": 3,
        "valedictory": 3,
        "farewell": 3,
        "cultural": 2,
        "cultural event": 3,
        "cultural fest": 3,
        "cultural program": 3,
        "sports": 2,
        "sports day": 3,
        "sports meet": 3,
        "annual sports": 3,
        "celebration": 2,
        "alumni meet": 3,
        "alumni day": 3,
        "alumni event": 3,
        "reunion": 2,
        "convocation": 3,
        "graduation day": 3,
        "annual day": 3,
        "college day": 3,
        "fresher party": 3,
        "freshers day": 3,
        "talent show": 2,
        "cultural show": 2,
        "exhibition": 2,
        "trade fair": 2,
        "seminar general": 1,
        "meeting": 1,
        "committee meeting": 1,
    },
}

# Classification Confidence Thresholds
CONFIDENCE_THRESHOLDS = {
    "HIGH": 0.80,    # >= 80%
    "MEDIUM": 0.50,  # 50% - 79%
    "LOW": 0.00,     # < 50%
}

# Ambiguity Detection Configuration
AMBIGUITY_CONFIG = {
    "MAX_SCORE_DIFFERENCE": 3,       # If diff between 1st and 2nd rank <= 3, flag ambiguous
    "MIN_CONFIDENCE_FOR_SURE": 0.60,
    "MIN_SCORE_THRESHOLD": 4,        # Below this, mark needs_review
}

# Default Report Settings
DEFAULT_REPORT_SETTINGS = {
    "institution_name": "Vidyavardhaka College of Engineering",
    "department_name": "Department of Computer Science & Engineering",
    "report_title": "Department Event Newsletter",
    "subtitle": "Comprehensive Academic & Co-Curricular Activity Report",
    "academic_year": "2026–2027",
    "reporting_period": "June 2026 – September 2026",
    "logo_path": None,
    "primary_color": "#1E3A8A", # Dark Navy
    "secondary_color": "#D97706", # Warm Amber
}

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"

# OCR Configuration
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
