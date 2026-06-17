"""
pages/3_Show_Analysis.py
----------------------------
Netflix Top 10 analysis: per-show trend charts, cumulative leaderboards,
and (where matched) TMDB enrichment - poster/rating shown alongside the
Netflix viewing stats for the same title.

Also hosts the CSV upload control, since this is the natural home for
"load/reload Netflix data" from a user's perspective.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

import database as db
from theme import apply_theme, eyebrow, PLOTLY_TEMPLATE
from netflix_loader import load_netflix_csv, DEFAULT_CSV_PATH
from title_matcher import get_enriched_show_info, match_all_unmatched_titles
import os

st.set_page_config(page_title="Show Analysis · CineScope", page_icon="📊", layout="wide")
apply_theme()
db.init_db()

eyebrow("CineScope · Netflix Top 10")
st.title("Show Analysis")

# ---------------------------------------------------------------------------
# Data loading controls
# ---------------------------------------------------------------------------

with st.expander("📥 Load / refresh Netflix CSV data", expanded=not db.get_all_show_titles()):
    st.caption(
        f"Default location checked: `{DEFAULT_CSV_PATH}`. "
        "Upload a file below to load from somewhere else."
    )
    uploaded = st.file_uploader("Upload Netflix Top 10 CSV", type=["csv"])

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Load from default path", use_container_width=True):
            try:
                count = load_netflix_csv(DEFAULT_CSV_PATH)
                st.success(f"Loaded {count} rows.")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    with col_b:
        if uploaded is not None and st.button("Load uploaded file", use_container_width=True):
            tmp_path = os.path.join("data", "_uploaded_netflix.csv")
            with open(tmp_path, "wb") as f:
                f.write(uploaded.getbuffer())
            try:
                count = load_netflix_csv(tmp_path)
                st.success(f"Loaded {count} rows.")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    if st.button("🔗 Match Netflix titles to TMDB (posters & ratings)"):
        with st.spinner("Matching titles against TMDB..."):
            matched = match_all_unmatched_titles()
        st.success(f"Matched {matched} new titles.")
        st.rerun()

show_titles = db.get_all_show_titles()

if not show_titles:
    st.info("No Netflix data loaded yet. Use the panel above to load your CSV.")
    st.stop()

st.divider()

# ---------------------------------------------------------------------------
# Leaderboard - cumulative views across all weeks
# ---------------------------------------------------------------------------

eyebrow("Overall")
st.subheader("Top shows by cumulative views")

leaderboard = db.get_top_shows_by_cumulative_views(limit=15)
lb_df = pd.DataFrame(leaderboard)

if not lb_df.empty:
    fig = px.bar(
        lb_df.sort_values("total_views"),
        x="total_views", y="show_title", orientation="h",
        labels={"total_views": "Total Views", "show_title": ""},
        text="weeks_tracked",
    )
    fig.update_traces(marker_color="#e8a33d", texttemplate="%{text} wks", textposition="outside")
    fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=480, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Per-show deep dive
# ---------------------------------------------------------------------------

eyebrow("Deep Dive")
st.subheader("Individual show trends")

selected_show = st.selectbox("Choose a show", show_titles)

history = db.get_show_history(selected_show)
hist_df = pd.DataFrame(history)

enrichment = get_enriched_show_info(selected_show)

info_col, chart_col = st.columns([1, 2], gap="large")

with info_col:
    if enrichment and enrichment.get("tmdb_id"):
        tmdb_movies = db.get_latest_tmdb_by_category("trending_day") + \
                      db.get_latest_tmdb_by_category("daily_release") + \
                      db.get_latest_tmdb_by_category("weekly_release")
        poster = next((m["poster_path"] for m in tmdb_movies if m["id"] == enrichment["tmdb_id"]), None)
        if poster:
            st.image(f"https://image.tmdb.org/t/p/w300{poster}")
        st.markdown(f"**TMDB match:** {enrichment['tmdb_title']}")
        st.caption(f"Match confidence: {enrichment['match_score']:.0f}%")
    else:
        st.caption("No TMDB match found for this title yet. Try the matching button above "
                   "(TV shows often won't match since TMDB movie search only covers films).")

    if not hist_df.empty:
        st.metric("Weeks in Top 10", int(hist_df["cumulative_weeks_in_top_10"].max()))
        st.metric("Total views (tracked period)", f"{hist_df['weekly_views'].sum():,.0f}")
        st.metric("Total hours viewed", f"{hist_df['weekly_hours_viewed'].sum():,.0f}")
        st.metric("Best rank achieved", int(hist_df["weekly_rank"].min()))

with chart_col:
    if not hist_df.empty:
        rank_fig = px.line(
            hist_df, x="week", y="weekly_rank", markers=True,
            labels={"weekly_rank": "Rank", "week": "Week"},
        )
        rank_fig.update_yaxes(autorange="reversed")  # rank 1 should be at the top
        rank_fig.update_traces(line_color="#e8a33d")
        rank_fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=260, title="Weekly rank over time")
        st.plotly_chart(rank_fig, use_container_width=True)

        views_fig = px.bar(
            hist_df, x="week", y="weekly_views",
            labels={"weekly_views": "Views", "week": "Week"},
        )
        views_fig.update_traces(marker_color="#5fb87a")
        views_fig.update_layout(**PLOTLY_TEMPLATE["layout"], height=260, title="Weekly views")
        st.plotly_chart(views_fig, use_container_width=True)
    else:
        st.info("No history found for this show.")
