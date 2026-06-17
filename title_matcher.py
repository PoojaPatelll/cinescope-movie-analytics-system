"""
title_matcher.py
-------------------
Links Netflix show_title values to TMDB records, so the dashboard can show
TMDB posters/ratings alongside Netflix viewing stats for the same title.

Why this needs care:
- Netflix titles include season info baked into season_title
  (e.g. "The Crown: Season 6") while show_title is usually the clean series name.
- TMDB's /search/movie endpoint only searches movies, not TV - many Netflix
  Top 10 entries are TV shows. We try movie search first; anything below the
  match threshold is left unmatched rather than guessed at, since a wrong
  match is worse than no match for an analytics dashboard.
- Matches are cached in the title_match_map table so this expensive process
  (1 TMDB API call per unique title) only runs once per show, not every page load.

Run standalone to match every currently-unmatched Netflix title:
    python title_matcher.py
"""

from datetime import datetime, timezone
from rapidfuzz import fuzz

import database as db
from tmdb_fetch import search_movie_by_title

MATCH_THRESHOLD = 75  # 0-100 similarity score; below this we store no match


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def match_single_title(show_title: str) -> dict | None:
    """
    Looks up one Netflix show_title against TMDB, scores the similarity,
    and caches the result (even a "no match") so we don't re-query TMDB
    for the same title again.
    Returns the match dict, or None if no acceptable match was found.
    """
    candidate = search_movie_by_title(show_title)

    if not candidate:
        db.save_title_match(show_title, None, None, 0.0, _now_iso())
        return None

    score = fuzz.ratio(show_title.lower(), candidate.get("title", "").lower())

    if score < MATCH_THRESHOLD:
        db.save_title_match(show_title, None, None, score, _now_iso())
        return None

    db.save_title_match(show_title, candidate["id"], candidate.get("title"), score, _now_iso())
    return {
        "show_title": show_title,
        "tmdb_id": candidate["id"],
        "tmdb_title": candidate.get("title"),
        "match_score": score,
        "poster_path": candidate.get("poster_path"),
        "vote_average": candidate.get("vote_average"),
        "overview": candidate.get("overview"),
    }


def match_all_unmatched_titles() -> int:
    """
    Finds every Netflix show_title that doesn't yet have a row in title_match_map
    and attempts to match it. Safe to re-run anytime new CSV data is loaded -
    already-matched titles are skipped automatically.
    """
    unmatched = db.get_unmatched_show_titles()
    matched_count = 0

    for title in unmatched:
        result = match_single_title(title)
        if result:
            matched_count += 1
            print(f"[title_matcher] Matched '{title}' -> '{result['tmdb_title']}' (score={result['match_score']:.0f})")
        else:
            print(f"[title_matcher] No confident match for '{title}'")

    print(f"[title_matcher] Done: {matched_count}/{len(unmatched)} titles matched")
    return matched_count


def get_enriched_show_info(show_title: str) -> dict | None:
    """
    Used by the Streamlit UI: given a Netflix show_title, returns cached
    TMDB enrichment info if a match exists, otherwise None.
    Does NOT call the TMDB API - this is a fast, read-only lookup for page rendering.
    """
    match = db.get_title_match(show_title)
    if not match or not match.get("tmdb_id"):
        return None
    return match


if __name__ == "__main__":
    db.init_db()
    match_all_unmatched_titles()
