def push_csv_to_db(csv_path, table_name, columns, lock):
    """
    Push all CSV records to MySQL.
    If DB insert succeeds, clear the CSV but keep its header.
    """

    conn = None
    cursor = None

    with lock:
        try:
            # -------------------------
            # 1. Check CSV exists
            # -------------------------
            if not os.path.exists(csv_path):
                print(f"CSV file not found: {csv_path}")
                return

            # -------------------------
            # 2. Read CSV
            # -------------------------
            with open(
                csv_path,
                "r",
                newline="",
                encoding="utf-8-sig"
            ) as f:

                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                print(f"No data to push from {csv_path}")
                return

            # -------------------------
            # 3. Get DB connection
            # -------------------------
            conn = get_connection()
            cursor = conn.cursor()

            # -------------------------
            # 4. Prepare INSERT
            # -------------------------
            column_names = ", ".join(columns)

            placeholders = ", ".join(
                ["%s"] * len(columns)
            )

            query = f"""
                INSERT INTO {table_name}
                ({column_names})
                VALUES ({placeholders})
            """

            # -------------------------
            # 5. Prepare CSV values
            # -------------------------
            values = [
                tuple(row.get(column) for column in columns)
                for row in rows
            ]

            # -------------------------
            # 6. Insert into DB
            # -------------------------
            cursor.executemany(query, values)

            conn.commit()

            print(
                f"{len(rows)} records inserted into {table_name}"
            )

            # -------------------------
            # 7. Clear CSV
            # Keep header
            # -------------------------
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

            print(f"CSV cleared: {csv_path}")

        except Exception as e:

            if conn:
                conn.rollback()

            print(
                f"Failed to push {csv_path} to DB:",
                e
            )

        finally:

            if cursor:
                cursor.close()

            if conn:
                conn.close()
