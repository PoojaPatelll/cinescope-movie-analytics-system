"""
tmdb_fetch.py
--------------
All TMDB API calls live here, each as an independent function.
Every function can be:
  - called directly from the Streamlit app (manual refresh button)
  - called from scheduler.py (automated 6am run)
  - run directly: `python tmdb_fetch.py` runs all fetches once, for testing

Requires TMDB_API_KEY in a .env file at the project root.
"""

import os
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

import database as db

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {"User-Agent": "CineScope/1.0"}
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3


def _now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get_with_retry(url: str, params: dict) -> dict | None:
    """Shared retry logic for any TMDB GET request."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[tmdb_fetch] API error {response.status_code} on attempt {attempt}")
        except requests.exceptions.RequestException as e:
            print(f"[tmdb_fetch] Connection error on attempt {attempt}: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None


def fetch_trending_movies() -> int:
    """
    Pulls today's trending movies and stores them.
    Returns the number of rows stored (0 on failure).
    """
    if not API_KEY:
        _log_and_print("fetch_trending_movies", "error", "TMDB_API_KEY missing from environment")
        return 0

    data = _get_with_retry(f"{BASE_URL}/trending/movie/day", {"api_key": API_KEY})
    if not data:
        _log_and_print("fetch_trending_movies", "error", "Failed after retries")
        return 0

    count = db.upsert_tmdb_movies(data.get("results", []), "trending_day", _now_iso())
    _log_and_print("fetch_trending_movies", "success", f"Stored {count} movies")
    return count


def fetch_daily_releases() -> int:
    """
    Pulls movies releasing today using TMDB's discover endpoint,
    filtered to today's date.
    """
    if not API_KEY:
        _log_and_print("fetch_daily_releases", "error", "TMDB_API_KEY missing from environment")
        return 0

    today = datetime.now().strftime("%Y-%m-%d")
    data = _get_with_retry(f"{BASE_URL}/discover/movie", {
        "api_key": API_KEY,
        "primary_release_date.gte": today,
        "primary_release_date.lte": today,
        "sort_by": "popularity.desc",
    })
    if not data:
        _log_and_print("fetch_daily_releases", "error", "Failed after retries")
        return 0

    count = db.upsert_tmdb_movies(data.get("results", []), "daily_release", _now_iso())
    _log_and_print("fetch_daily_releases", "success", f"Stored {count} movies releasing today")
    return count


def fetch_weekly_releases() -> int:
    """
    Pulls movies releasing in the current week (Mon-Sun) using discover.
    """
    if not API_KEY:
        _log_and_print("fetch_weekly_releases", "error", "TMDB_API_KEY missing from environment")
        return 0

    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    data = _get_with_retry(f"{BASE_URL}/discover/movie", {
        "api_key": API_KEY,
        "primary_release_date.gte": week_start.strftime("%Y-%m-%d"),
        "primary_release_date.lte": week_end.strftime("%Y-%m-%d"),
        "sort_by": "popularity.desc",
    })
    if not data:
        _log_and_print("fetch_weekly_releases", "error", "Failed after retries")
        return 0

    count = db.upsert_tmdb_movies(data.get("results", []), "weekly_release", _now_iso())
    _log_and_print("fetch_weekly_releases", "success", f"Stored {count} movies releasing this week")
    return count


def search_movie_by_title(title: str) -> dict | None:
    """
    Used by the title-matching module to look up a single TMDB movie by title.
    Returns the best (first) result, or None.
    """
    if not API_KEY:
        return None

    data = _get_with_retry(f"{BASE_URL}/search/movie", {"api_key": API_KEY, "query": title})
    if not data or not data.get("results"):
        return None
    return data["results"][0]


def run_all_daily_fetches() -> dict:
    """
    The single entry point the scheduler calls every day at 6am.
    Runs every fetch function independently - if one fails, the others still run.
    """
    results = {
        "trending": fetch_trending_movies(),
        "daily_releases": fetch_daily_releases(),
        "weekly_releases": fetch_weekly_releases(),
    }
    return results


def _log_and_print(task_name: str, status: str, message: str):
    print(f"[tmdb_fetch] {task_name}: {status} - {message}")
    try:
        db.log_fetch_run(task_name, status, message, _now_iso())
    except Exception as e:
        print(f"[tmdb_fetch] Warning: could not write to fetch_log: {e}")


if __name__ == "__main__":
    db.init_db()
    print("Running all TMDB fetches once for testing...")
    print(run_all_daily_fetches())
