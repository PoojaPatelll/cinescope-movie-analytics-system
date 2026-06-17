"""
app.py
--------
CineScope - main Streamlit entry point.

Run with: streamlit run app.py

This file only handles: page config, theme, starting the background
scheduler once, and the Home overview. The Daily Releases, Weekly Releases,
and Show Analysis views live in pages/ as separate Streamlit pages -
each one calls into database.py / tmdb_fetch.py / title_matcher.py directly,
so none of the actual logic is duplicated here.
"""

import streamlit as st
from datetime import datetime

import database as db
from theme import apply_theme, eyebrow
from scheduler import start_scheduler_once, is_scheduler_running

st.set_page_config(
    page_title="CineScope",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
db.init_db()
start_scheduler_once()  # idempotent - safe on every Streamlit re-run

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

eyebrow("CineScope · Movie & Netflix Analytics")
st.title("Tonight's Lineup")
st.caption(
    "Live TMDB releases and Netflix Top 10 performance, refreshed automatically every day at 6:00 AM."
)

st.divider()

# ---------------------------------------------------------------------------
# Top-line metrics
# ---------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

netflix_shows = db.get_all_show_titles()
latest_week_rows = db.get_latest_week_top10()
daily_tmdb = db.get_latest_tmdb_by_category("daily_release")
trending_tmdb = db.get_latest_tmdb_by_category("trending_day")

with col1:
    st.metric("Shows tracked (Netflix)", len(netflix_shows))
with col2:
    st.metric("In this week's Top 10", len(latest_week_rows))
with col3:
    st.metric("Releasing today (TMDB)", len(daily_tmdb))
with col4:
    st.metric("Trending today (TMDB)", len(trending_tmdb))

st.divider()

# ---------------------------------------------------------------------------
# Quick glance: this week's Netflix top 10 + today's trending
# ---------------------------------------------------------------------------

left, right = st.columns(2, gap="large")

with left:
    eyebrow("Netflix · This Week")
    st.subheader("Top 10 right now")
    if latest_week_rows:
        for row in latest_week_rows[:10]:
            rcol1, rcol2 = st.columns([1, 8])
            with rcol1:
                st.markdown(f"<div class='cs-rank'>{row['weekly_rank']}</div>", unsafe_allow_html=True)
            with rcol2:
                st.markdown(f"**{row['show_title']}**")
                st.markdown(
                    f"<span class='cs-muted'>{row['category']} · "
                    f"{row['cumulative_weeks_in_top_10']} weeks in Top 10</span>",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No Netflix data loaded yet. Load your CSV from the Show Analysis page.")

with right:
    eyebrow("TMDB · Trending Today")
    st.subheader("What everyone's watching")
    if trending_tmdb:
        for movie in trending_tmdb[:10]:
            st.markdown(f"**{movie['title']}**")
            st.markdown(
                f"<span class='cs-muted'>⭐ {movie['vote_average']:.1f} · "
                f"Released {movie['release_date'] or 'TBA'}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("")
    else:
        st.info("No TMDB data fetched yet. Use 'Refresh Now' in the sidebar.")

# ---------------------------------------------------------------------------
# Sidebar - manual controls (every backend function independently triggerable)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### Data Controls")

    scheduler_status = "🟢 Running" if is_scheduler_running() else "🔴 Not running"
    st.caption(f"Background scheduler: {scheduler_status}")
    st.caption("Next automatic TMDB fetch: daily at 06:00")

    st.markdown("---")

    if st.button("🔄 Refresh TMDB data now", use_container_width=True):
        with st.spinner("Fetching trending, daily, and weekly releases..."):
            import tmdb_fetch
            results = tmdb_fetch.run_all_daily_fetches()
        st.success(f"Done: {results}")
        st.rerun()

    st.markdown("---")
    st.markdown("### Recent fetch activity")
    logs = db.get_recent_fetch_logs(limit=5)
    if logs:
        for log in logs:
            icon = "✅" if log["status"] == "success" else "❌"
            st.caption(f"{icon} {log['task_name']} · {log['run_at'][:16]}")
    else:
        st.caption("No fetches recorded yet.")

    st.markdown("---")
    st.caption(f"Page loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
