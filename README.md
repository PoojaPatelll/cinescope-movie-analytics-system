# CineScope

A Streamlit dashboard combining live TMDB movie release data with Netflix
weekly Top 10 performance, backed by SQLite.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your real TMDB_API_KEY (get one free at themoviedb.org)
```

Place your Netflix Top 10 CSV at `data/netflix_top10.csv`, or use the
upload button on the **Show Analysis** page once the app is running.

Expected CSV columns (case-insensitive, spaces or underscores both fine):
`week, category, weekly_rank, show_title, season_title, weekly_hours_viewed
(or weekly_hour_viewed), runtime, weekly_views, cumulative_weeks_in_top_10
(or cumulative_week_in_top_10)`

## Run

```bash
streamlit run app.py
```

This starts the dashboard at `http://localhost:8501` and also starts a
background scheduler that automatically fetches fresh TMDB data every day
at 6:00 AM while the app is running. There's also a manual "Refresh TMDB
data now" button in the sidebar for on-demand fetches.

## Project structure

Every backend concern lives in its own module with independent,
individually-callable functions — none of them depend on Streamlit being
the caller, so they can be run from a script, a cron job, or a test.

| File | Responsibility |
|---|---|
| `database.py` | SQLite schema + every read/write query function |
| `tmdb_fetch.py` | TMDB API calls: trending, daily releases, weekly releases |
| `netflix_loader.py` | Loads/cleans the Netflix CSV into SQLite |
| `title_matcher.py` | Fuzzy-matches Netflix titles to TMDB records |
| `scheduler.py` | Background thread that triggers the 6 AM fetch |
| `theme.py` | Shared CSS/Plotly styling |
| `app.py` | Home page + sidebar controls |
| `pages/1_Daily_Releases.py` | Today's TMDB releases |
| `pages/2_Weekly_Releases.py` | This week's TMDB releases |
| `pages/3_Show_Analysis.py` | Netflix leaderboards, per-show trend charts, TMDB enrichment |

### Running pieces independently

Every module can be run on its own, e.g. for testing or cron:

```bash
python database.py          # (re)initialize schema
python netflix_loader.py path/to/file.csv
python tmdb_fetch.py         # runs all three TMDB fetches once
python title_matcher.py      # matches any newly-loaded Netflix titles to TMDB
```

## Performance notes

- SQLite runs in WAL mode so dashboard reads don't block the scheduler's writes.
- All TMDB/Netflix data fetches happen in the background or on explicit
  button click — page loads are pure reads from SQLite, never live API calls.
- Indexes on title/week/category columns keep the leaderboard and per-show
  history queries fast as data grows.
- TMDB-to-Netflix title matches are cached in `title_match_map` so the
  (slow, rate-limited) matching process runs once per title, not per page view.

## Known limitations

- TMDB matching uses the movie search endpoint, so Netflix **TV shows**
  often won't find a match (this is expected — TMDB's TV search API would
  need to be wired in separately to improve TV coverage).
- The "weekly release" window is defined as the current Mon–Sun calendar week.
