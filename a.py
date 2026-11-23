import os
import mysql.connector

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)
cur = conn.cursor()

cur.execute("SELECT * FROM chat_logs")
for row in cur.fetchall():
    print(row)

conn.close()
