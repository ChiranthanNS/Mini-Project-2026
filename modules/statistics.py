"""
Statistics and Visualization Module.
Calculates category-wise counts and metrics strictly from the CURRENT APPROVED STATE.
Generates Plotly interactive charts for UI and publication-quality Matplotlib figures for the PDF.
"""

from pathlib import Path
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from config import CATEGORY_COLORS


class StatisticsEngine:
    """Computes event metrics and generates charts based on final event state."""

    @staticmethod
    def get_category_counts(events: List[Dict], categories: List[str]) -> Dict[str, int]:
        """Compute event count per category from current active event state."""
        counts = {cat: 0 for cat in categories}
        for ev in events:
            cat = ev.get("category", "Other")
            if cat in counts:
                counts[cat] += 1
            else:
                counts[cat] = counts.get(cat, 0) + 1
        return counts

    @classmethod
    def get_summary_stats(cls, events: List[Dict], categories: List[str]) -> Dict:
        """Calculate comprehensive summary statistics."""
        total = len(events)
        cat_counts = cls.get_category_counts(events, categories)
        
        percentages = {}
        for cat, cnt in cat_counts.items():
            percentages[cat] = round((cnt / total * 100), 1) if total > 0 else 0.0

        conf_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        needs_review_cnt = 0
        events_with_photos = 0

        for ev in events:
            level = ev.get("confidence_level", "LOW")
            if level in conf_counts:
                conf_counts[level] += 1
            if ev.get("needs_review", False):
                needs_review_cnt += 1
            if ev.get("images") and len(ev["images"]) > 0:
                events_with_photos += 1

        return {
            "total_events": total,
            "category_counts": cat_counts,
            "category_percentages": percentages,
            "confidence_counts": conf_counts,
            "needs_review_count": needs_review_cnt,
            "events_with_photos": events_with_photos,
            "events_without_photos": total - events_with_photos,
        }

    @staticmethod
    def create_plotly_pie_chart(
        category_counts: Dict[str, int],
        color_map: Optional[Dict[str, str]] = None,
    ) -> go.Figure:
        """Create an interactive Plotly donut chart for the Streamlit dashboard."""
        non_zero = {k: v for k, v in category_counts.items() if v > 0}
        if not non_zero:
            fig = go.Figure()
            fig.add_annotation(
                text="No events available to chart",
                showarrow=False,
                font=dict(size=16, color="#6B7280"),
            )
            fig.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20))
            return fig

        labels = list(non_zero.keys())
        values = list(non_zero.values())
        colors = [color_map.get(lbl, CATEGORY_COLORS.get(lbl, "#6366F1")) for lbl in labels] if color_map else None

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.45,
                    textinfo="label+percent",
                    marker=dict(colors=colors, line=dict(color="#FFFFFF", width=2)),
                    hoverinfo="label+value+percent",
                )
            ]
        )
        fig.update_layout(
            title=dict(text="Event Distribution by Category", x=0.5, font=dict(size=18, family="sans-serif")),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            margin=dict(t=40, b=40, l=20, r=20),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    @staticmethod
    def generate_matplotlib_pie_chart(
        category_counts: Dict[str, int],
        output_path: Path,
        color_map: Optional[Dict[str, str]] = None,
    ) -> Optional[Path]:
        """
        Generate a publication-quality Matplotlib pie chart image saved to output_path.
        Used directly in ReportLab PDF generation.
        """
        non_zero = {k: v for k, v in category_counts.items() if v > 0}
        if not non_zero:
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)

        labels = list(non_zero.keys())
        values = list(non_zero.values())
        colors = [color_map.get(lbl, CATEGORY_COLORS.get(lbl, "#3B82F6")) for lbl in labels] if color_map else None

        fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=300)
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2),
            pctdistance=0.75,
        )

        plt.setp(texts, size=10, weight="bold", color="#1F2937")
        plt.setp(autotexts, size=9, weight="bold", color="#111827")
        ax.set_title("Event Distribution by Category", fontsize=14, weight="bold", pad=20, color="#111827")
        plt.tight_layout()

        fig.savefig(output_path, format="png", bbox_inches="tight", dpi=300, facecolor="white")
        plt.close(fig)

        return output_path
