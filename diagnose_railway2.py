import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

connection = mysql.connector.connect(
    host=os.environ["MYSQLHOST"],
    port=int(os.environ["MYSQLPORT"]),
    user=os.environ["MYSQLUSER"],
    password=os.environ["MYSQLPASSWORD"],
    database=os.environ["MYSQLDATABASE"],
    connection_timeout=10,
)

cursor = connection.cursor()

cursor.execute("""
    SELECT
        waiting_pid,
        waiting_query,
        blocking_pid,
        blocking_query
    FROM sys.schema_table_lock_waits
    WHERE object_schema = DATABASE()
      AND object_name = 'overall_prediction_history'
""")

rows = cursor.fetchall()

if rows:
    for row in rows:
        print("Waiting process ID:", row[0])
        print("Waiting query:", row[1])
        print("Blocking process ID:", row[2])
        print("Blocking query:", row[3])
        print("-" * 40)
else:
    print("No blocker details returned.")

cursor.close()
connection.close()
