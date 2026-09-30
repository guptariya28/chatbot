def parse_timestamp(value):
    """
    Convert CSV timestamp to a datetime object for MySQL.
    """

    if not value:
        return datetime.now()

    value = str(value).strip()

    try:
        # Handles ISO format:
        # 2026-09-30T06:30:00+00:00
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))

        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)

        return dt

    except ValueError:
        # Handles:
        # 2026-09-30 12:00:00
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def push_csv_to_db(csv_path, table_name, columns, lock):

    with lock:

        # Check if CSV exists
        if not os.path.exists(csv_path):
            print(f"CSV not found: {csv_path}")
            return

        # Read CSV
        try:
            with open(
                csv_path,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as f:
                rows = list(csv.DictReader(f))

        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

        if not rows:
            print(f"No data in {csv_path}")
            return

        # Create generic INSERT query
        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
            INSERT INTO {table_name}
            ({column_names})
            VALUES ({placeholders})
        """

        failed_rows = []
        success_count = 0
        failed_count = 0

        # Process each row separately
        for row in rows:

            conn = None
            cursor = None

            try:
                conn = db_pool.get_connection()
                cursor = conn.cursor()

                values = []

                for column in columns:

                    value = row.get(column)

                    # Convert created_at timestamp
                    if column == "created_at":
                        value = parse_timestamp(value)

                    values.append(value)

                cursor.execute(query, tuple(values))

                conn.commit()

                success_count += 1

            except Exception as e:

                if conn:
                    conn.rollback()

                failed_rows.append(row)
                failed_count += 1

                print(
                    f"Failed row "
                    f"message_id={row.get('message_id')} "
                    f"Error: {e}"
                )

            finally:

                if cursor:
                    cursor.close()

                if conn:
                    conn.close()

        # Rewrite CSV
        # Only failed rows will remain
        try:
            with open(
                csv_path,
                "w",
                newline="",
                encoding="utf-8-sig"
            ) as f:

                writer = csv.DictWriter(
                    f,
                    fieldnames=columns,
                    quoting=csv.QUOTE_ALL
                )

                writer.writeheader()

                if failed_rows:
                    writer.writerows(failed_rows)

        except Exception as e:
            print(f"Error rewriting CSV: {e}")

        print(
            f"{table_name} completed | "
            f"Success: {success_count} | "
            f"Failed: {failed_count}"
        )


def push_logs_to_db():

    push_csv_to_db(
        csv_path=CHAT_LOG_FILE_PATH,
        table_name="FINANCE_CHAT_LOGS",
        columns=CHAT_LOG_COLUMNS,
        lock=_log_write_lock
    )

    push_csv_to_db(
        csv_path=FEEDBACK_LOG_FILE_PATH,
        table_name="FINANCE_FEEDBACK_LOGS",
        columns=FEEDBACK_COLUMNS,
        lock=_feedback_write_lock
    )
