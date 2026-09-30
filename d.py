import csv
import os
import fcntl
from datetime import datetime, timezone

from csv_logger import (
    CHAT_LOG_FILE_PATH,
    FEEDBACK_LOG_FILE_PATH,
    CHAT_LOG_COLUMNS,
    FEEDBACK_COLUMNS
)

from db_connection import db_pool   # change based on your DB file name


def parse_timestamp(value):
    """
    Convert timestamp from CSV into a MySQL-compatible datetime.
    """

    if not value:
        return datetime.now(timezone.utc).replace(tzinfo=None)

    value = str(value).strip()

    try:
        # Handles:
        # 2026-09-30T06:30:00+00:00
        # 2026-09-30T06:30:00Z
        # 2026-09-30 12:00:00
        dt = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

        # Convert timezone-aware datetime to UTC
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

        return dt

    except ValueError:
        raise ValueError(
            f"Invalid timestamp format: {value}"
        )


def push_csv_to_db(csv_path, table_name, columns):
    """
    Push CSV rows into MySQL.

    - Uses file locking for Flask + cron process safety
    - Processes rows individually
    - One failed row does not stop other rows
    - Successful rows are removed from CSV
    - Failed rows remain in CSV
    - CSV header is preserved
    """

    if not os.path.exists(csv_path):
        print(f"CSV not found: {csv_path}")
        return

    conn = None
    cursor = None

    # r+ allows us to read and rewrite the same file
    with open(
        csv_path,
        "r+",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        # ---------------------------------
        # Acquire exclusive OS-level lock
        # ---------------------------------
        fcntl.flock(
            csv_file.fileno(),
            fcntl.LOCK_EX
        )

        try:

            # ---------------------------------
            # Read CSV
            # ---------------------------------

            csv_file.seek(0)

            reader = csv.DictReader(csv_file)

            rows = list(reader)

            if not rows:
                print(f"No data in {csv_path}")
                return

            # ---------------------------------
            # Build generic INSERT
            # ---------------------------------

            column_names = ", ".join(columns)

            placeholders = ", ".join(
                ["%s"] * len(columns)
            )

            query = f"""
                INSERT INTO {table_name}
                ({column_names})
                VALUES ({placeholders})
            """

            failed_rows = []

            success_count = 0
            failed_count = 0

            # ---------------------------------
            # Get ONE DB connection
            # ---------------------------------

            conn = db_pool.get_connection()
            cursor = conn.cursor()

            # ---------------------------------
            # Process each row
            # ---------------------------------

            for row in rows:

                try:

                    values = []

                    for column in columns:

                        value = row.get(column)

                        # Handle timestamp
                        if column == "created_at":
                            value = parse_timestamp(value)

                        values.append(value)

                    # -------------------------
                    # Insert one row
                    # -------------------------

                    cursor.execute(
                        query,
                        tuple(values)
                    )

                    conn.commit()

                    success_count += 1

                except Exception as e:

                    # Rollback ONLY current row
                    conn.rollback()

                    failed_rows.append(row)

                    failed_count += 1

                    print(
                        f"FAILED | "
                        f"message_id={row.get('message_id')} | "
                        f"error={e}"
                    )

            # ---------------------------------
            # Rewrite CSV
            # ---------------------------------
            # Keep only failed rows

            csv_file.seek(0)

            writer = csv.DictWriter(
                csv_file,
                fieldnames=columns,
                quoting=csv.QUOTE_ALL
            )

            writer.writeheader()

            if failed_rows:
                writer.writerows(failed_rows)

            # Remove old leftover content
            csv_file.truncate()

            csv_file.flush()

            # Force OS to write changes
            os.fsync(csv_file.fileno())

            print(
                f"{table_name} completed | "
                f"Success: {success_count} | "
                f"Failed: {failed_count}"
            )

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                f"Error processing {csv_path}: {e}"
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()

            # Release file lock
            fcntl.flock(
                csv_file.fileno(),
                fcntl.LOCK_UN
            )


def main():

    # ---------------------------------
    # Chat logs
    # ---------------------------------

    push_csv_to_db(
        csv_path=CHAT_LOG_FILE_PATH,
        table_name="FINANCE_CHAT_LOGS",
        columns=CHAT_LOG_COLUMNS
    )

    # ---------------------------------
    # Feedback logs
    # ---------------------------------

    push_csv_to_db(
        csv_path=FEEDBACK_LOG_FILE_PATH,
        table_name="FINANCE_FEEDBACK_LOGS",
        columns=FEEDBACK_COLUMNS
    )


if __name__ == "__main__":
    main()
