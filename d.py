import csv
import os
import threading
import uuid
from datetime import datetime, timezone

LOG_COLUMNS = [
    "email",
    "message_id",
    "conversation_id",
    "Question",
    "answer",
    "app_name",
    "created_at",
    "user_name",
]

_write_lock = threading.Lock()


def _safe(value):
    """Convert to string and neutralise spreadsheet formula injection."""
    text = "" if value is None else str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        text = "'" + text
    return text


def log_chat_to_csv(
    question,
    answer,
    email="",
    user_name="",
    app_name="",
    conversation_id=None,
    message_id=None,
    created_at=None,
    log_file="chatbot_logs.csv",
):
    """
    Append one chatbot interaction to a CSV file.

    - Creates the file (and parent folders) with a header row if needed.
    - Handles commas, quotes, and newlines in questions/answers.
    - Thread-safe within a single process.

    Returns the row that was written (dict).
    """
    row = {
        "email": _safe(email),
        "message_id": message_id or str(uuid.uuid4()),
        "conversation_id": conversation_id or str(uuid.uuid4()),
        "Question": _safe(question),
        "answer": _safe(answer),
        "app_name": _safe(app_name),
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "user_name": _safe(user_name),
    }

    folder = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(folder, exist_ok=True)

    with _write_lock:
        needs_header = (not os.path.exists(log_file)) or os.path.getsize(log_file) == 0
        # utf-8-sig so Excel opens non-ASCII text correctly
        with open(log_file, "a", newline="", encoding="utf-8-sig" if needs_header else "utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=LOG_COLUMNS, quoting=csv.QUOTE_ALL)
            if needs_header:
                writer.writeheader()
            writer.writerow(row)

    return row


if __name__ == "__main__":
    log_chat_to_csv(
        question="What is our leave policy?",
        answer="Employees get 20 days,\nplus public holidays.",
        email="jane@example.com",
        user_name="Jane Doe",
        app_name="HR-Bot",
        conversation_id="conv-123",
    )
    print("Logged.")
