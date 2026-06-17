"""
pages/1_Daily_Releases.py
----------------------------
Shows movies releasing today, pulled from TMDB. Pure read from SQLite -
no API calls happen on page load, only on explicit refresh.
"""

import streamlit as st
import database as db
from theme import apply_theme, eyebrow

st.set_page_config(page_title="Daily Releases · CineScope", page_icon="🎬", layout="wide")
apply_theme()
db.init_db()

eyebrow("CineScope · Today")
st.title("Releasing Today")

daily = db.get_latest_tmdb_by_category("daily_release")

if not daily:
    st.info(
        "No daily release data yet. Click **Refresh TMDB data now** in the sidebar "
        "on the Home page, or wait for the 6 AM automatic fetch."
    )
else:
    fetched_at = daily[0]["fetched_at"]
    st.caption(f"Last updated: {fetched_at}")
    st.divider()

    cols = st.columns(3)
    for i, movie in enumerate(daily):
        with cols[i % 3]:
            with st.container(border=True):
                if movie.get("poster_path"):
                    st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}")
                st.markdown(f"**{movie['title']}**")
                st.markdown(
                    f"<span class='cs-muted'>⭐ {movie['vote_average'] or 'N/A'} · "
                    f"{movie['vote_count'] or 0} votes</span>",
                    unsafe_allow_html=True,
                )
                if movie.get("overview"):
                    st.caption(movie["overview"][:140] + ("…" if len(movie["overview"]) > 140 else ""))
