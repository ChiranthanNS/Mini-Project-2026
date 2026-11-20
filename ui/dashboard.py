"""
Dashboard UI Module.
Displays real-time metrics, category breakdown counters, and dynamic Plotly pie/bar charts
generated strictly from the CURRENT FINAL APPROVED EVENT STATE.
"""

from typing import Dict, List, Callable
import streamlit as st
import plotly.express as px
from modules.statistics import StatisticsEngine
from modules.keyword_manager import KeywordManager


def render_dashboard_page(
    events: List[Dict],
    km: KeywordManager,
    on_proceed_to_pdf_callback: Callable[[], None],
    on_back_to_review_callback: Callable[[], None],
):
    """Render the Live Analytics Dashboard."""
    st.markdown(
        """
        <div style="margin-bottom: 1.5rem;">
            <h2 style="color: #1E3A8A; font-weight: 700; margin-bottom: 2px;">
                Executive Dashboard & Analytics
            </h2>
            <p style="color: #64748B; font-size: 0.95rem;">
                Real-time event distribution and quality metrics generated strictly from your approved event data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not events:
        st.warning("No events available to display in dashboard.")
        return

    categories = km.get_categories()
    stats = StatisticsEngine.get_summary_stats(events, categories)
    total_events = stats["total_events"]
    cat_counts = stats["category_counts"]

    # 1. KPI Top Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.metric("Total Events Documented", total_events)
    with kpi2:
        active_cats = sum(1 for c, cnt in cat_counts.items() if cnt > 0)
        st.metric("Active Categories", active_cats)
    with kpi3:
        high_conf = stats["confidence_counts"].get("HIGH", 0)
        high_pct = int((high_conf / total_events) * 100) if total_events > 0 else 0
        st.metric("High Confidence Events", f"{high_pct}% ({high_conf})")
    with kpi4:
        st.metric("Photographs Attached", f"{stats['events_with_photos']}/{total_events}")

    st.markdown("<br/>", unsafe_allow_html=True)

    # 2. Charts Row
    chart_col1, chart_col2 = st.columns([1.2, 1])

    with chart_col1:
        st.markdown("#### 🥧 Category Distribution (Pie Chart)")
        plotly_fig = StatisticsEngine.create_plotly_pie_chart(cat_counts, color_map=km.colors)
        st.plotly_chart(plotly_fig, use_container_width=True)

    with chart_col2:
        st.markdown("#### 📊 Event Counts by Category")
        # Horizontal Bar Chart
        active_items = [(cat, cnt) for cat, cnt in cat_counts.items() if cnt > 0]
        if active_items:
            cat_names = [item[0] for item in active_items]
            counts = [item[1] for item in active_items]
            colors_list = [km.get_color(c) for c in cat_names]

            import plotly.graph_objects as go
            bar_fig = go.Figure(
                go.Bar(
                    x=counts,
                    y=cat_names,
                    orientation="h",
                    marker_color=colors_list,
                    text=counts,
                    textposition="auto",
                )
            )
            bar_fig.update_layout(
                height=350,
                margin=dict(t=20, b=20, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Number of Events",
            )
            st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No active events to chart.")

    # 3. Category Breakdown Metrics
    st.markdown("#### 📑 Category Breakdown Summary")
    grid_cols = st.columns(4)
    for idx, (cat, cnt) in enumerate(cat_counts.items()):
        col_idx = idx % 4
        with grid_cols[col_idx]:
            cat_color = km.get_color(cat)
            pct = stats["category_percentages"].get(cat, 0.0)
            st.markdown(
                f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 4px solid {cat_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px;">
                    <div style="font-size: 0.8rem; font-weight: 700; color: #475569; text-transform: uppercase;">{cat}</div>
                    <div style="font-size: 1.3rem; font-weight: 700; color: #0F172A;">{cnt} <span style="font-size: 0.85rem; font-weight: 400; color: #64748B;">({pct}%)</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br/>", unsafe_allow_html=True)

    # 4. Action Buttons
    nav1, nav2, nav3 = st.columns([2, 1, 2])
    with nav1:
        if st.button("← Back to Review & Arrange", use_container_width=True):
            on_back_to_review_callback()

    with nav3:
        if st.button("Proceed to Report Settings & PDF Generation →", type="primary", use_container_width=True):
            on_proceed_to_pdf_callback()
