import atexit
import fcntl
import logging
import os
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(process)d] %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("app")

LOCK_PATH = "/tmp/apscheduler.lock"
RETRY_SECONDS = 300  # how often non-owner workers re-check the lock

app = Flask(__name__)

_scheduler = None      # set only in the worker that owns the lock
_lock_file = None      # must stay referenced or the flock is released
_next_attempt = 0.0    # monotonic time of next allowed lock attempt
_state_lock = threading.Lock()


# --------------------------------------------------------------------------
# Your job
# --------------------------------------------------------------------------
def nightly_job():
    log.info("nightly_job started (pid=%s)", os.getpid())
    try:
        # TODO: put your real work here
        pass
        log.info("nightly_job finished")
    except Exception:
        log.exception("nightly_job failed")


# --------------------------------------------------------------------------
# Scheduler startup (one worker wins the file lock)
# --------------------------------------------------------------------------
def try_start_scheduler():
    """Return True if this worker owns the scheduler. Cheap to call often."""
    global _scheduler, _lock_file, _next_attempt

    if _scheduler is not None:
        return True
    if time.monotonic() < _next_attempt:
        return False

    with _state_lock:
        if _scheduler is not None:
            return True
        if time.monotonic() < _next_attempt:
            return False

        lock = open(LOCK_PATH, "w")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            _next_attempt = time.monotonic() + RETRY_SECONDS
            return False

        _lock_file = lock
        sched = BackgroundScheduler(timezone="UTC")
        sched.add_job(
            nightly_job,
            trigger="cron",
            hour=2,
            minute=0,
            id="nightly",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        sched.start()
        _scheduler = sched
        atexit.register(_shutdown)
        log.info("Scheduler started in pid=%s", os.getpid())
        return True


def _shutdown():
    global _scheduler, _lock_file
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    if _lock_file is not None:
        try:
            fcntl.flock(_lock_file, fcntl.LOCK_UN)
            _lock_file.close()
        except Exception:
            pass
        _lock_file = None


# Try at import time (each gunicorn worker imports the app, no --preload),
# and retry lazily on requests in case the owner worker dies.
try_start_scheduler()


@app.before_request
def ensure_scheduler():
    try_start_scheduler()


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return "ok"


@app.route("/scheduler-status")
def scheduler_status():
    return jsonify(
        pid=os.getpid(),
        owns_scheduler=_scheduler is not None,
        jobs=[
            {"id": j.id, "next_run": str(j.next_run_time)}
            for j in (_scheduler.get_jobs() if _scheduler else [])
        ],
    )


if __name__ == "__main__":
    app.run(debug=False)
 
