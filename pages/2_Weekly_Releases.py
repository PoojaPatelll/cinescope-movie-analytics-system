"""
pages/2_Weekly_Releases.py
-----------------------------
Shows movies releasing this calendar week (Mon-Sun), pulled from TMDB.
"""

import streamlit as st
import database as db
from theme import apply_theme, eyebrow

st.set_page_config(page_title="Weekly Releases · CineScope", page_icon="🎬", layout="wide")
apply_theme()
db.init_db()

eyebrow("CineScope · This Week")
st.title("Releasing This Week")

weekly = db.get_latest_tmdb_by_category("weekly_release")

if not weekly:
    st.info(
        "No weekly release data yet. Click **Refresh TMDB data now** in the sidebar "
        "on the Home page, or wait for the 6 AM automatic fetch."
    )
else:
    fetched_at = weekly[0]["fetched_at"]
    st.caption(f"Last updated: {fetched_at}")
    st.divider()

    sort_choice = st.radio(
        "Sort by", ["Popularity", "Release date"], horizontal=True, label_visibility="collapsed"
    )
    if sort_choice == "Release date":
        weekly = sorted(weekly, key=lambda m: m["release_date"] or "9999-99-99")

    cols = st.columns(3)
    for i, movie in enumerate(weekly):
        with cols[i % 3]:
            with st.container(border=True):
                if movie.get("poster_path"):
                    st.image(f"https://image.tmdb.org/t/p/w300{movie['poster_path']}")
                st.markdown(f"**{movie['title']}**")
                st.markdown(
                    f"<span class='cs-muted'>📅 {movie['release_date'] or 'TBA'} · "
                    f"⭐ {movie['vote_average'] or 'N/A'}</span>",
                    unsafe_allow_html=True,
                )
                if movie.get("overview"):
                    st.caption(movie["overview"][:140] + ("…" if len(movie["overview"]) > 140 else ""))
