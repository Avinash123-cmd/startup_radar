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

def _is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
        except Exception:
            pass
        return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def start_scheduler():
    # Multi-worker safety check: prevent duplicate schedulers in Uvicorn processes
    if LOCK_FILE.exists():
        try:
            pid_str = LOCK_FILE.read_text().strip()
            if pid_str:
                pid = int(pid_str)
                if _is_process_alive(pid):
                    print(f"Scheduler: Active scheduler detected in another worker (PID {pid}). Skipping startup.")
                    return None
                else:
                    print(f"Scheduler: Stale lock file found (PID {pid} is not running). Releasing lock.")
                    release_lock()
            else:
                release_lock()
        except Exception:
            try:
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
