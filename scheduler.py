"""
scheduler.py
--------------
Runs a background thread inside the Streamlit app that triggers the TMDB
fetch automatically once a day at 6:00 AM.

Important Streamlit-specific detail: Streamlit re-runs your script on every
interaction, which would normally restart the scheduler thread over and over.
We guard against that with a module-level flag, so the background thread is
only ever started once per server process, no matter how many times
Streamlit re-executes app.py.
"""

import threading
import time
import schedule
from datetime import datetime, timezone

import database as db
from tmdb_fetch import run_all_daily_fetches

_scheduler_started = False
_scheduler_lock = threading.Lock()


def _job():
    print(f"[scheduler] Running scheduled 6am TMDB fetch at {datetime.now()}")
    try:
        results = run_all_daily_fetches()
        print(f"[scheduler] Fetch complete: {results}")
    except Exception as e:
        db.log_fetch_run("scheduled_fetch", "error", str(e),
                          datetime.now(timezone.utc).isoformat(timespec="seconds"))
        print(f"[scheduler] Fetch failed: {e}")


def _run_pending_loop():
    schedule.every().day.at("06:00").do(_job)
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30s - plenty granular for a once-a-day job


def start_scheduler_once():
    """
    Call this once from app.py at startup.
    Thread-safe and idempotent: safe to call on every Streamlit re-run.
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return False  # already running, nothing to do
        thread = threading.Thread(target=_run_pending_loop, daemon=True)
        thread.start()
        _scheduler_started = True
        print("[scheduler] Background scheduler started - daily TMDB fetch set for 06:00")
        return True


def is_scheduler_running() -> bool:
    return _scheduler_started


if __name__ == "__main__":
    # For manual testing outside Streamlit
    start_scheduler_once()
    print("Scheduler running standalone. Press Ctrl+C to stop.")
    while True:
        time.sleep(60)
