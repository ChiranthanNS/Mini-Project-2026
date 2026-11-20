"""
Keyword and Category Management Module.
Provides functions to manage categories, keywords, weights, and configurations.
"""

from typing import Dict, List, Optional
import copy
from config import DEFAULT_CATEGORIES, DEFAULT_KEYWORDS, CATEGORY_COLORS


class KeywordManager:
    """Manages event categories, keywords, and their scoring weights."""

    def __init__(
        self,
        categories: Optional[List[str]] = None,
        keywords: Optional[Dict[str, Dict[str, int]]] = None,
        colors: Optional[Dict[str, str]] = None,
    ):
        self.categories: List[str] = list(categories) if categories is not None else list(DEFAULT_CATEGORIES)
        self.keywords: Dict[str, Dict[str, int]] = (
            copy.deepcopy(keywords) if keywords is not None else copy.deepcopy(DEFAULT_KEYWORDS)
        )
        self.colors: Dict[str, str] = dict(colors) if colors is not None else dict(CATEGORY_COLORS)
        self._ensure_integrity()

    def _ensure_integrity(self) -> None:
        """Ensure all categories exist in the keywords and colors mapping."""
        for cat in self.categories:
            if cat not in self.keywords:
                self.keywords[cat] = {}
            if cat not in self.colors:
                # Assign a pleasant fallback color
                self.colors[cat] = "#4B5563"

    def get_categories(self) -> List[str]:
        """Return list of current categories."""
        return list(self.categories)

    def add_category(self, category_name: str, color: Optional[str] = None) -> bool:
        """Add a new category."""
        clean_name = category_name.strip()
        if not clean_name or clean_name in self.categories:
            return False
        self.categories.append(clean_name)
        self.keywords[clean_name] = {}
        self.colors[clean_name] = color or "#6366F1"
        return True

    def remove_category(self, category_name: str) -> bool:
        """Remove an existing category (cannot remove 'Other')."""
        if category_name in self.categories and category_name != "Other":
            self.categories.remove(category_name)
            self.keywords.pop(category_name, None)
            self.colors.pop(category_name, None)
            return True
        return False

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """Rename an existing category."""
        new_clean = new_name.strip()
        if not new_clean or old_name not in self.categories or new_clean in self.categories:
            return False

        idx = self.categories.index(old_name)
        self.categories[idx] = new_clean

        if old_name in self.keywords:
            self.keywords[new_clean] = self.keywords.pop(old_name)
        else:
            self.keywords[new_clean] = {}

        if old_name in self.colors:
            self.colors[new_clean] = self.colors.pop(old_name)
        else:
            self.colors[new_clean] = "#6366F1"

        return True

    def get_keywords(self, category: str) -> Dict[str, int]:
        """Return dictionary of keywords and their weights for a category."""
        return dict(self.keywords.get(category, {}))

    def set_keyword(self, category: str, keyword: str, weight: int) -> bool:
        """Add or update a keyword with its weight in a category."""
        clean_kw = keyword.strip().lower()
        if not clean_kw or category not in self.keywords:
            return False
        self.keywords[category][clean_kw] = max(1, int(weight))
        return True

    def remove_keyword(self, category: str, keyword: str) -> bool:
        """Remove a keyword from a category."""
        clean_kw = keyword.strip().lower()
        if category in self.keywords and clean_kw in self.keywords[category]:
            del self.keywords[category][clean_kw]
            return True
        return False

    def get_color(self, category: str) -> str:
        """Get hex color associated with category."""
        return self.colors.get(category, "#4B5563")

    def to_dict(self) -> dict:
        """Serialize configuration to a dictionary."""
        return {
            "categories": self.categories,
            "keywords": self.keywords,
            "colors": self.colors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KeywordManager":
        """Instantiate KeywordManager from a dictionary."""
        return cls(
            categories=data.get("categories"),
            keywords=data.get("keywords"),
            colors=data.get("colors"),
        )

    def reset_to_defaults(self) -> None:
        """Reset categories and keywords to default configuration."""
        self.categories = list(DEFAULT_CATEGORIES)
        self.keywords = copy.deepcopy(DEFAULT_KEYWORDS)
        self.colors = dict(CATEGORY_COLORS)
        self._ensure_integrity()
