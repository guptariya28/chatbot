import csv
import os
import tempfile
import threading
from datetime import datetime, timezone

FEEDBACK_COLUMNS = ["message_id", "feedback", "rating", "created_at"]

_write_lock = threading.Lock()


def _safe(value):
    """Convert to string and neutralise spreadsheet formula injection."""
    text = "" if value is None else str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        text = "'" + text
    return text


def upsert_feedback_to_csv(
    message_id,
    feedback=None,
    rating=None,
    created_at=None,
    feedback_file="chatbot_feedback.csv",
):
    """
    Insert feedback for a message, or update it if message_id already exists.

    - If message_id exists: the row is updated. Any of feedback/rating passed
      as None keeps its existing value; created_at is refreshed.
    - If not: a new row is appended.
    - Creates the file with a header row if needed.
    - Rewrites via a temp file + os.replace, so a crash can't corrupt the CSV.
    - Thread-safe within a single process.

    Returns the row that was saved (dict).
    """
    if not message_id:
        raise ValueError("message_id is required")

    message_id = str(message_id)
    now = created_at or datetime.now(timezone.utc).isoformat()

    folder = os.path.dirname(os.path.abspath(feedback_file))
    os.makedirs(folder, exist_ok=True)

    with _write_lock:
        rows = []
        if os.path.exists(feedback_file) and os.path.getsize(feedback_file) > 0:
            with open(feedback_file, "r", newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))

        saved = None
        for row in rows:
            if row.get("message_id") == message_id:
                if feedback is not None:
                    row["feedback"] = _safe(feedback)
                if rating is not None:
                    row["rating"] = _safe(rating)
                row["created_at"] = now
                saved = row
                break

        if saved is None:
            saved = {
                "message_id": message_id,
                "feedback": _safe(feedback),
                "rating": _safe(rating),
                "created_at": now,
            }
            rows.append(saved)

        # Write to a temp file in the same folder, then atomically swap it in
        fd, tmp_path = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f, fieldnames=FEEDBACK_COLUMNS, quoting=csv.QUOTE_ALL
                )
                writer.writeheader()
                writer.writerows(rows)
            os.replace(tmp_path, feedback_file)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    return saved


if __name__ == "__main__":
    upsert_feedback_to_csv("msg-1", feedback="Helpful answer", rating=5)
    upsert_feedback_to_csv("msg-1", feedback="Actually, missing some detail", rating=3)  # updates
    upsert_feedback_to_csv("msg-2", feedback="Wrong answer", rating=1)  # inserts
    print("Done.")
