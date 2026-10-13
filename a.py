
import os
from dotenv import load_dotenv
from hdbcli import dbapi

load_dotenv()


def connect_to_hana():
    conn = None
    cursor = None

    try:
        # Connect to SAP HANA
        conn = dbapi.connect(
            address=os.getenv("HANA_HOST"),
            port=int(os.getenv("HANA_PORT")),
            user=os.getenv("HANA_USER"),
            password=os.getenv("HANA_PASSWORD")
        )

        print("Successfully connected to SAP HANA!")

        # Execute a test query
        cursor = conn.cursor()
        cursor.execute("SELECT CURRENT_USER FROM DUMMY")

        result = cursor.fetchone()
        print("Connected database user:", result[0])

        return True

    except Exception as e:
        print("Failed to connect to SAP HANA:", e)
        return False

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    connect_to_hana()
