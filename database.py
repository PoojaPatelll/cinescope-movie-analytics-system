import sqlite3
import os
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "cinescope.db")

os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_connection():
    """
    Context-managed SQLite connection.
    Using a context manager everywhere guarantees the connection
    is always closed, even if a query raises an error.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    # Performance pragmas - safe defaults for a read-heavy analytics app
    conn.execute("PRAGMA journal_mode = WAL;")       # readers don't block writers
    conn.execute("PRAGMA synchronous = NORMAL;")      # good durability/speed tradeoff with WAL
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Creates all tables and indexes if they don't already exist.
    Safe to call every time the app starts.
    """
    with get_connection() as conn:
        cur = conn.cursor()

        # TMDB movies - trending / daily / weekly release pulls
        # TMDB movies - trending / daily / weekly release pulls
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tmdb_movies (
                id INTEGER,                             -- Changed from INTEGER PRIMARY KEY to just INTEGER
                title TEXT NOT NULL,
                original_title TEXT,
                release_date TEXT,
                popularity REAL,
                vote_average REAL,
                vote_count INTEGER,
                overview TEXT,
                poster_path TEXT,
                source_category TEXT,                    -- 'trending_day' | 'daily_release' | 'weekly_release'
                fetched_at TEXT NOT NULL,                 -- timestamp of this fetch
                PRIMARY KEY(id, source_category, fetched_at) -- Defines the true composite identifier
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tmdb_title ON tmdb_movies(title);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tmdb_release_date ON tmdb_movies(release_date);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tmdb_category ON tmdb_movies(source_category);")

        # Netflix weekly Top 10 data (from CSV)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS netflix_top10 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week TEXT NOT NULL,
                category TEXT,
                weekly_rank INTEGER,
                show_title TEXT NOT NULL,
                season_title TEXT,
                weekly_hours_viewed REAL,
                runtime REAL,
                weekly_views REAL,
                cumulative_weeks_in_top_10 INTEGER,
                UNIQUE(week, show_title, season_title, category)
            );
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_netflix_title ON netflix_top10(show_title);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_netflix_week ON netflix_top10(week);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_netflix_category ON netflix_top10(category);")

        # Maps a Netflix show_title to a TMDB id, so we don't have to
        # re-run fuzzy matching every page load.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS title_match_map (
                show_title TEXT PRIMARY KEY,
                tmdb_id INTEGER,
                tmdb_title TEXT,
                match_score REAL,
                matched_at TEXT
            );
        """)

        # Tracks scheduler / fetch run history (useful for debugging "did 6am run today?")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS fetch_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                status TEXT NOT NULL,        -- 'success' | 'error'
                message TEXT,
                run_at TEXT NOT NULL
            );
        """)

    print(f"Database initialized at {DB_PATH}")


# ---------------------------------------------------------------------------
# TMDB movie functions
# ---------------------------------------------------------------------------

def upsert_tmdb_movies(movies: list[dict], source_category: str, fetched_at: str):
    """
    Insert/update a batch of TMDB movie dicts.
    Uses TMDB's own numeric id as the natural key (more reliable than title).
    """
    if not movies:
        return 0

    rows = [
        (
            m.get("id"),
            m.get("title") or m.get("name"),
            m.get("original_title") or m.get("original_name"),
            m.get("release_date") or m.get("first_air_date"),
            m.get("popularity"),
            m.get("vote_average"),
            m.get("vote_count"),
            m.get("overview"),
            m.get("poster_path"),
            source_category,
            fetched_at,
        )
        for m in movies
        if m.get("id") is not None
    ]

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO tmdb_movies (
                id, title, original_title, release_date, popularity,
                vote_average, vote_count, overview, poster_path,
                source_category, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id, source_category, fetched_at) DO UPDATE SET
                title=excluded.title,
                popularity=excluded.popularity,
                vote_average=excluded.vote_average,
                vote_count=excluded.vote_count;
        """, rows)

    return len(rows)


def get_latest_tmdb_by_category(category: str, limit: int = 50):
    """Fetch the most recent batch of TMDB rows for a given source_category."""
    with get_connection() as conn:
        latest_fetch = conn.execute("""
            SELECT MAX(fetched_at) AS latest FROM tmdb_movies WHERE source_category = ?
        """, (category,)).fetchone()["latest"]

        if not latest_fetch:
            return []

        rows = conn.execute("""
            SELECT * FROM tmdb_movies
            WHERE source_category = ? AND fetched_at = ?
            ORDER BY popularity DESC
            LIMIT ?
        """, (category, latest_fetch, limit)).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Netflix Top 10 functions
# ---------------------------------------------------------------------------

def upsert_netflix_rows(rows: list[tuple]):
    """
    Bulk insert Netflix Top 10 rows.
    Each tuple must match column order:
    (week, category, weekly_rank, show_title, season_title,
     weekly_hours_viewed, runtime, weekly_views, cumulative_weeks_in_top_10)
    """
    if not rows:
        return 0

    with get_connection() as conn:
        conn.executemany("""
            INSERT INTO netflix_top10 (
                week, category, weekly_rank, show_title, season_title,
                weekly_hours_viewed, runtime, weekly_views, cumulative_weeks_in_top_10
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(week, show_title, season_title, category) DO UPDATE SET
                weekly_rank=excluded.weekly_rank,
                weekly_hours_viewed=excluded.weekly_hours_viewed,
                weekly_views=excluded.weekly_views,
                cumulative_weeks_in_top_10=excluded.cumulative_weeks_in_top_10;
        """, rows)

    return len(rows)


def get_all_show_titles():
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT show_title FROM netflix_top10 ORDER BY show_title;").fetchall()
        return [r["show_title"] for r in rows]


def get_show_history(show_title: str):
    """All weekly rows for a single show, ordered by week - used for trend charts."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM netflix_top10
            WHERE show_title = ?
            ORDER BY week ASC;
        """, (show_title,)).fetchall()
        return [dict(r) for r in rows]


def get_latest_week_top10(category: str | None = None):
    with get_connection() as conn:
        latest_week = conn.execute("SELECT MAX(week) AS w FROM netflix_top10").fetchone()["w"]
        if not latest_week:
            return []
        if category:
            rows = conn.execute("""
                SELECT * FROM netflix_top10
                WHERE week = ? AND category = ?
                ORDER BY weekly_rank ASC;
            """, (latest_week, category)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM netflix_top10
                WHERE week = ?
                ORDER BY category, weekly_rank ASC;
            """, (latest_week,)).fetchall()
        return [dict(r) for r in rows]


def get_top_shows_by_cumulative_views(limit: int = 20):
    """Aggregated leaderboard - one row per show, summed across all weeks."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT
                show_title,
                MAX(category) AS category,
                SUM(weekly_views) AS total_views,
                SUM(weekly_hours_viewed) AS total_hours_viewed,
                MAX(cumulative_weeks_in_top_10) AS weeks_in_top_10,
                COUNT(DISTINCT week) AS weeks_tracked
            FROM netflix_top10
            GROUP BY show_title
            ORDER BY total_views DESC
            LIMIT ?;
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Title matching (Netflix <-> TMDB)
# ---------------------------------------------------------------------------

def save_title_match(show_title: str, tmdb_id: int | None, tmdb_title: str | None,
                      match_score: float, matched_at: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO title_match_map (show_title, tmdb_id, tmdb_title, match_score, matched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(show_title) DO UPDATE SET
                tmdb_id=excluded.tmdb_id,
                tmdb_title=excluded.tmdb_title,
                match_score=excluded.match_score,
                matched_at=excluded.matched_at;
        """, (show_title, tmdb_id, tmdb_title, match_score, matched_at))


def get_title_match(show_title: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM title_match_map WHERE show_title = ?;", (show_title,)
        ).fetchone()
        return dict(row) if row else None


def get_unmatched_show_titles():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT DISTINCT n.show_title
            FROM netflix_top10 n
            LEFT JOIN title_match_map m ON n.show_title = m.show_title
            WHERE m.show_title IS NULL;
        """).fetchall()
        return [r["show_title"] for r in rows]


# ---------------------------------------------------------------------------
# Fetch log (for visibility into the scheduler)
# ---------------------------------------------------------------------------

def log_fetch_run(task_name: str, status: str, message: str, run_at: str):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO fetch_log (task_name, status, message, run_at)
            VALUES (?, ?, ?, ?);
        """, (task_name, status, message, run_at))


def get_recent_fetch_logs(limit: int = 20):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM fetch_log ORDER BY id DESC LIMIT ?;
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
