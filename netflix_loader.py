import sys
import os
import pandas as pd
import database as db

DEFAULT_CSV_PATH = r"C:\Users\Upendra\OneDrive\Desktop\new_cinescope\data\netflix_data.csv"

# Expected source columns -> our internal column names
COLUMN_MAP = {
    "week": "week",
    "category": "category",
    "weekly_rank": "weekly_rank",
    "show_title": "show_title",
    "season_title": "season_title",
    "weekly_hours_viewed": "weekly_hours_viewed",
    "weekly_hour_viewed": "weekly_hours_viewed",   # tolerate the singular variant
    "runtime": "runtime",
    "weekly_views": "weekly_views",
    "cumulative_weeks_in_top_10": "cumulative_weeks_in_top_10",
    "cumulative_week_in_top_10": "cumulative_weeks_in_top_10",  # tolerate singular variant
}

REQUIRED_COLUMNS = [
    "week", "category", "weekly_rank", "show_title", "season_title",
    "weekly_hours_viewed", "runtime", "weekly_views", "cumulative_weeks_in_top_10",
]


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Strips commas/whitespace from numeric-looking columns and coerces to numbers."""
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def load_netflix_csv(csv_path: str = DEFAULT_CSV_PATH) -> int:
    """
    Reads the CSV, normalizes columns, cleans data types, and bulk-upserts into SQLite.
    Returns the number of rows loaded. Raises a clear error if the file or columns
    don't match expectations, rather than silently loading bad data.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Netflix CSV not found at: {csv_path}\n"
            f"Place your file there, or call load_netflix_csv('your/path.csv')."
        )

    df = pd.read_csv(csv_path, encoding="latin-1")

    # Normalize column names: lowercase, strip, spaces -> underscores
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    df = df.rename(columns=COLUMN_MAP)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing expected columns: {missing}\n"
            f"Columns found: {list(df.columns)}"
        )

    # Keep only the columns we need, in the right order
    df = df[REQUIRED_COLUMNS].copy()

    # Clean types
    df["week"] = df["week"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["show_title"] = df["show_title"].astype(str).str.strip()
    df["season_title"] = df["season_title"].astype(str).str.strip()

    for col in ["weekly_rank", "cumulative_weeks_in_top_10"]:
        df[col] = _clean_numeric(df[col])

    for col in ["weekly_hours_viewed", "runtime", "weekly_views"]:
        df[col] = _clean_numeric(df[col])

    # Drop rows with no show title - useless without it
    df = df.dropna(subset=["show_title"])
    df = df[df["show_title"].str.lower() != "nan"]

    # Convert to plain Python types for sqlite3. We deliberately avoid
    # pandas' nullable Int64 dtype here - sqlite3 doesn't know how to bind
    # it and silently stores it as a BLOB of raw bytes instead of an integer,
    # which then breaks every numeric query (sorting, MIN/MAX, comparisons)
    # downstream. Plain Python int/float/None round-trips correctly.
    def to_native(value):
        if pd.isna(value):
            return None
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value

    rows = [
        tuple(to_native(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    db.init_db()
    count = db.upsert_netflix_rows(rows)
    print(f"[netflix_loader] Loaded {count} rows from {csv_path}")
    return count


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    load_netflix_csv(path)
