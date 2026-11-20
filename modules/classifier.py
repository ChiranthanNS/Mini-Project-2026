"""
Power-Enhanced Keyword Classification Engine v2.

Features:
- Full-text normalization with stemming (Porter algorithm, no NLTK needed)
- Negation detection: "no workshop", "not a seminar" → score zeroed
- Positional multi-layer weighting: Title > First-line > First-paragraph > Body
- Multi-word phrase priority: longer phrases matched before single words
- TF-IDF-inspired frequency saturation to prevent keyword stuffing
- Morphological root matching via built-in Porter Stemmer
- Cross-category disambiguation with score margin analysis
- Zero-dependency (pure Python + re)
"""

from typing import Dict, List, Tuple
import re
from config import CONFIDENCE_THRESHOLDS, AMBIGUITY_CONFIG
from modules.keyword_manager import KeywordManager


# ---------------------------------------------------------------------------
# Minimal built-in Porter Stemmer (pure Python, zero external deps)
# ---------------------------------------------------------------------------

class _PorterStemmer:
    """
    Stripped-down Porter Stemmer sufficient for English event vocabulary.
    Only implements the most common suffix rules.
    """

    STEP1A_RULES = [
        (r"sses$", "ss"), (r"ies$", "i"), (r"ss$", "ss"), (r"s$", ""),
    ]
    STEP1B_RULES = [
        (r"eed$", "ee"), (r"(?<=[aeiou].*)ed$", ""), (r"(?<=[aeiou].*)ing$", ""),
    ]
    STEP2_RULES = [
        (r"ational$", "ate"), (r"tional$", "tion"), (r"enci$", "ence"),
        (r"anci$", "ance"), (r"izer$", "ize"), (r"isation$", "ize"),
        (r"ization$", "ize"), (r"isation$", "ize"), (r"alism$", "al"),
        (r"ness$", ""), (r"ment$", ""), (r"ments$", ""), (r"ful$", ""),
        (r"fully$", ""), (r"less$", ""), (r"lessly$", ""), (r"ly$", ""),
        (r"ies$", "y"), (r"izes$", "ize"), (r"ising$", "ize"),
        (r"izing$", "ize"), (r"ers$", "er"), (r"ings$", "ing"),
        (r"ions$", "ion"), (r"ors$", "or"), (r"ors$", "or"),
    ]

    @classmethod
    def stem(cls, word: str) -> str:
        word = word.lower().strip()
        if len(word) <= 3:
            return word
        for pattern, replacement in cls.STEP1A_RULES:
            if re.search(pattern, word):
                word = re.sub(pattern, replacement, word)
                break
        for pattern, replacement in cls.STEP1B_RULES:
            if re.search(pattern, word):
                word = re.sub(pattern, replacement, word)
                break
        for pattern, replacement in cls.STEP2_RULES:
            if re.search(pattern, word):
                word = re.sub(pattern, replacement, word)
                break
        return word

    @classmethod
    def stem_phrase(cls, phrase: str) -> str:
        """Stem each word in a phrase and rejoin."""
        return " ".join(cls.stem(w) for w in phrase.split())


_stemmer = _PorterStemmer()


# ---------------------------------------------------------------------------
# Negation Window
# ---------------------------------------------------------------------------

NEGATION_WORDS = frozenset([
    "no", "not", "without", "none", "neither", "nor", "never",
    "hardly", "barely", "scarcely", "except", "excluding", "non",
])

# How many tokens after a negation word to suppress (sliding window)
NEGATION_WINDOW = 4


# Clause-ending punctuation marks
CLAUSE_BOUNDARIES = frozenset([".", ";", "!", "?"])


def _apply_negation_mask_to_text(text: str) -> str:
    """
    Apply negation masking to text, respecting sentence/clause boundaries.
    Any tokens following a negation word within the same clause (up to 8 tokens)
    are replaced with '__neg__'.
    """
    if not text:
        return ""
    
    # Split text into sentences/clauses
    clauses = re.split(r'([.;!?]+)', text)
    result_clauses = []
    
    for clause in clauses:
        if not clause or clause in ".;!?":
            result_clauses.append(clause)
            continue
            
        norm_clause = re.sub(r"[^a-z0-9\-\s]", " ", clause.lower())
        norm_clause = re.sub(r"\s+", " ", norm_clause).strip()
        tokens = norm_clause.split()
        
        masked_tokens = []
        neg_countdown = 0
        for tok in tokens:
            if tok in NEGATION_WORDS:
                neg_countdown = 8  # Cover entire coordinate phrase e.g. "no workshop or seminar"
                masked_tokens.append("__neg__")
            elif neg_countdown > 0:
                masked_tokens.append("__neg__")
                neg_countdown -= 1
            else:
                masked_tokens.append(tok)
                
        result_clauses.append(" ".join(masked_tokens))
        
    return " ".join(result_clauses)


# ---------------------------------------------------------------------------
# Text Layers — split input into positional zones for weighted scoring
# ---------------------------------------------------------------------------

def _extract_layers(text: str) -> Dict[str, str]:
    """
    Split raw text into positional layers for weight differentiation.
    Returns:
        title_line: very first non-empty line (highest weight)
        first_para: lines 2–4 of non-empty content (medium-high weight)
        body: remainder
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return {"title_line": "", "first_para": "", "body": ""}

    title_line = lines[0]
    first_para = " ".join(lines[1:4]) if len(lines) > 1 else ""
    body = " ".join(lines[4:]) if len(lines) > 4 else ""

    return {"title_line": title_line, "first_para": first_para, "body": body}


# ---------------------------------------------------------------------------
# Main Classifier
# ---------------------------------------------------------------------------

class EventClassifier:
    """
    Power-enhanced event classifier using weighted keyword scoring,
    stemming, negation detection, and positional layer weighting.
    """

    # Layer weights for scoring (title gets maximum signal)
    LAYER_WEIGHTS = {
        "title_line": 4.0,
        "first_para": 2.0,
        "body":        1.0,
    }

    def __init__(self, keyword_manager: KeywordManager):
        self.km = keyword_manager
        # Pre-compile stemmed keyword patterns for all categories
        self._compiled: Dict[str, List[Tuple[re.Pattern, str, int, int]]] = {}
        self._build_patterns()

    def _build_patterns(self):
        """
        Pre-compile regex patterns for all keywords.
        Each pattern entry: (compiled_pattern, original_kw, weight, num_words)
        Sorted longest-phrase-first for greedy multi-word matching.
        """
        self._compiled = {}
        for cat in self.km.get_categories():
            kw_dict = self.km.get_keywords(cat)
            entries = []
            for kw, weight in kw_dict.items():
                kw_norm = self._normalize(kw)
                if not kw_norm:
                    continue
                num_words = len(kw_norm.split())
                # Build pattern that handles plural/verb forms at the END of phrase
                pattern_str = r"\b" + re.escape(kw_norm) + r"(?:s|es|ing|ed|ion|ions|er|ers|ment|ments|al|ally|ity|ies)?\b"
                try:
                    compiled = re.compile(pattern_str, re.IGNORECASE)
                    entries.append((compiled, kw, weight, num_words))
                except re.error:
                    continue
            # Sort: longer phrases first (greedy matching preference)
            entries.sort(key=lambda x: x[3], reverse=True)
            self._compiled[cat] = entries

    def _normalize(self, text: str) -> str:
        """
        Normalize text: lowercase, strip punctuation, collapse whitespace.
        Does NOT stem — stemmed matching is done separately via pattern.
        """
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\-\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _tokenize(self, text: str) -> List[str]:
        return self._normalize(text).split()

    def _score_layer(
        self,
        layer_text: str,
        cat: str,
        layer_weight: float,
    ) -> Tuple[float, List[str]]:
        """
        Score a single text layer against one category.
        Returns (total_weighted_score, list_of_matched_keywords).
        """
        if not layer_text:
            return 0.0, []

        clean_text = _apply_negation_mask_to_text(layer_text)

        entries = self._compiled.get(cat, [])
        matched = []
        total_score = 0.0

        # Track already-matched spans to avoid double-counting sub-phrases
        matched_spans: List[Tuple[int, int]] = []

        for compiled_pat, orig_kw, weight, num_words in entries:
            for m in compiled_pat.finditer(clean_text):
                start, end = m.start(), m.end()

                # Skip if negated token is in this span
                if "__neg__" in clean_text[start:end]:
                    continue

                # Skip if already covered by a longer phrase match
                overlaps = any(
                    not (end <= ms or start >= me)
                    for ms, me in matched_spans
                )
                if overlaps:
                    continue

                matched_spans.append((start, end))
                # Frequency saturation: each additional hit of the same keyword yields diminishing return
                hit_count = sum(1 for kw in matched if kw == orig_kw)
                saturation = 1.0 / (1 + hit_count * 0.5)

                score = weight * layer_weight * saturation
                total_score += score
                matched.append(orig_kw)

        return total_score, matched

    def classify_event(self, event_data: Dict) -> Dict:
        """
        Classify a single event. Updates and returns the event dictionary with:
        - category: str
        - confidence: float (0.0 to 1.0)
        - confidence_level: "HIGH" | "MEDIUM" | "LOW"
        - classification_source: "keyword"
        - needs_review: bool
        - suggested_categories: List[str]
        - matched_keywords: List[str]
        - category_scores: Dict[str, float]
        """
        event_name = event_data.get("event_name", "")
        description = event_data.get("description", "")
        combined_full = f"{event_name}\n{description}"

        # --- Extract positional text layers ---
        # Event name is always "title", description broken into first_para + body
        title_text = event_name
        desc_layers = _extract_layers(description)

        # Layer 1: Title (event name)
        # Layer 2: First paragraph of description
        # Layer 3: Body of description
        layers = {
            "title_line": title_text,
            "first_para": desc_layers["title_line"] + " " + desc_layers["first_para"],
            "body": desc_layers["body"],
        }

        category_scores: Dict[str, float] = {}
        all_matched_kws: Dict[str, List[str]] = {}

        for cat in self.km.get_categories():
            cat_score = 0.0
            cat_matched = []

            for layer_name, layer_text in layers.items():
                lw = self.LAYER_WEIGHTS[layer_name]
                score, matched = self._score_layer(layer_text, cat, lw)
                cat_score += score
                cat_matched.extend(matched)

            # Deduplicate matched keywords while preserving first occurrence order
            seen = set()
            deduped = []
            for kw in cat_matched:
                if kw not in seen:
                    seen.add(kw)
                    deduped.append(kw)

            category_scores[cat] = round(cat_score, 2)
            all_matched_kws[cat] = deduped

        # --- Rank and pick best category ---
        ranked = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = ranked[0]
        second_cat, second_score = ranked[1] if len(ranked) > 1 else ("Other", 0.0)

        # --- Confidence and ambiguity calculation ---
        needs_review = False
        suggested_cats = []

        if top_score <= 0:
            assigned_category = "Other"
            confidence = 0.20
            confidence_level = "LOW"
            needs_review = True
            suggested_cats = [c for c in self.km.get_categories() if c != "Other"][:3]
        else:
            assigned_category = top_cat

            # Dominance ratio: how much better is #1 vs #2?
            dominance = top_score / (top_score + second_score) if (top_score + second_score) > 0 else 0.6

            # Magnitude: absolute evidence strength (saturates at score ~20)
            magnitude = min(1.0, top_score / 20.0)

            # Combined confidence
            raw_confidence = (0.55 * dominance) + (0.45 * magnitude)
            confidence = round(max(0.30, min(0.97, raw_confidence)), 2)

            # Ambiguity: close score margin
            score_diff = top_score - second_score
            if second_score > 0 and score_diff <= AMBIGUITY_CONFIG["MAX_SCORE_DIFFERENCE"]:
                needs_review = True
                suggested_cats = [top_cat, second_cat]

            # Ambiguity: weak absolute score
            if top_score < AMBIGUITY_CONFIG["MIN_SCORE_THRESHOLD"]:
                needs_review = True
                suggested_cats = [c for c, s in ranked if s > 0][:3]
                if not suggested_cats:
                    suggested_cats = [top_cat, second_cat]

            # Confidence level label
            if confidence >= CONFIDENCE_THRESHOLDS["HIGH"]:
                confidence_level = "HIGH"
            elif confidence >= CONFIDENCE_THRESHOLDS["MEDIUM"]:
                confidence_level = "MEDIUM"
            else:
                confidence_level = "LOW"

        # --- Write results back to event record ---
        event_data["category"] = assigned_category
        event_data["confidence"] = confidence
        event_data["confidence_level"] = confidence_level
        event_data["classification_source"] = "keyword"
        event_data["needs_review"] = needs_review
        event_data["suggested_categories"] = suggested_cats
        event_data["matched_keywords"] = all_matched_kws.get(assigned_category, [])
        event_data["category_scores"] = {k: v for k, v in category_scores.items()}

        return event_data

    def reclassify_with_new_keywords(self, event_data: Dict) -> Dict:
        """Force rebuild of patterns then reclassify. Used after keyword manager updates."""
        self._build_patterns()
        return self.classify_event(event_data)
