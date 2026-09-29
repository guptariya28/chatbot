import sqlite3

DB_PATH = "chat_history.db"


def read_all_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM chat_history")
    rows = cursor.fetchall()

    conn.close()

    return rows


def delete_record(record_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM chat_history WHERE id = ?",
        (record_id,)
    )

    conn.commit()
    conn.close()

    return f"Record {record_id} deleted successfully"
