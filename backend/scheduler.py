import os
import time
import tempfile
import atexit
from datetime import datetime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from pipeline import run_pipeline

LOCK_FILE = Path(tempfile.gettempdir()) / "startup_radar_scheduler.lock"

def run_sync_pipeline():
    print("Scheduler: Triggering automated synchronization run...")
    try:
        run_pipeline()
        print("Scheduler: Synchronization cycle successfully completed.")
    except Exception as e:
        print(f"Scheduler: Automated run encountered errors: {e}")

def release_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            print("Scheduler: Lock file released.")
    except Exception:
        pass

def start_scheduler():
    # Multi-worker safety check: prevent duplicate schedulers in Uvicorn processes
    if LOCK_FILE.exists():
        try:
            # Check modification time to prevent stale locks from crashed runs
            mtime = LOCK_FILE.stat().st_mtime
            if time.time() - mtime < 60:
                print("Scheduler: Active scheduler detected in another worker. Skipping startup.")
                return None
            else:
                release_lock()
        except Exception:
            pass

    try:
        LOCK_FILE.write_text(str(os.getpid()))
        atexit.register(release_lock)
    except Exception as e:
        print(f"Scheduler: Failed to acquire process lock: {e}")

    scheduler = BackgroundScheduler()
    # Runs the analytics sync process once every 6 hours, immediately starting the first run on launch
    scheduler.add_job(run_sync_pipeline, "interval", hours=6, next_run_time=datetime.utcnow())
    
    # Touch lock file every 30 seconds to show this scheduler is active
    def touch_lock():
        try:
            if LOCK_FILE.exists():
                LOCK_FILE.touch()
        except Exception:
            pass
    scheduler.add_job(touch_lock, "interval", seconds=30)
    
    scheduler.start()
    print("APScheduler Background Daemon started successfully. Active intervals: 6 Hours.")
    return scheduler
