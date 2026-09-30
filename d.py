def create_tables():
    conn = None
    cursor = None
 
    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id  CHAR(8)      NOT NULL,
                convo_id    CHAR(8)      NOT NULL,
                user_email  VARCHAR(255) NOT NULL,
                user_name   VARCHAR(150) NOT NULL,
                app_name    VARCHAR(20)  NOT NULL,
                question    LONGTEXT     NOT NULL,
                answer      LONGTEXT     NOT NULL,
                created_at  TIMESTAMP    NOT NULL
            ) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_feedback (
                message_id  CHAR(8)      NOT NULL,
                feedback    TEXT         NULL,
                rating      ENUM('thumbs_up', 'thumbs_down') NOT NULL,
                created_at  TIMESTAMP    NOT NULL
            ) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """)
 
        conn.commit()
        print("Tables created successfully!")
 
    except mysql.connector.Error as e:
        print("Table creation failed:", e)
 
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
 
create_tables()
 
