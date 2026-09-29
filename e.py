import mysql.connector
from mysql.connector import pooling

db_pool = pooling.MySQLConnectionPool(
    pool_name="rag_chatbot_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="your_password",
    database="rag_chatbot"
)


def test_connection():
    conn = None
    cursor = None

    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1;")
        result = cursor.fetchone()

        print("Database connection successful!")
        print("Result:", result)

    except mysql.connector.Error as e:
        print("Database connection failed:", e)

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


test_connection()
