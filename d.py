import csv


def push_csv_to_db(csv_file, table_name, columns):
    conn = None
    cursor = None

    try:
        # 1. Read CSV
        with open(csv_file, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            rows = list(reader)

        if not rows:
            print(f"{csv_file} is empty.")
            return

        # 2. Get DB connection
        conn = get_connection()
        cursor = conn.cursor()

        # 3. Create INSERT query
        column_names = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders})
        """

        # 4. Prepare values from CSV
        values = [
            tuple(row[column] for column in columns)
            for row in rows
        ]

        # 5. Insert all rows
        cursor.executemany(query, values)

        conn.commit()

        print(f"{len(rows)} rows inserted into {table_name}")

        # 6. Empty CSV but KEEP headers
        with open(csv_file, "w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(columns)

        print(f"{csv_file} cleared successfully.")

    except Exception as e:
        if conn:
            conn.rollback()

        print("Error:", e)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
