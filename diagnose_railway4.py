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
        waiting_account,
        waiting_query_secs,
        waiting_query,
        blocking_pid,
        blocking_account,
        blocking_lock_duration,
        sql_kill_blocking_query,
        sql_kill_blocking_connection
    FROM sys.schema_table_lock_waits
    WHERE object_schema = DATABASE()
      AND object_name = 'overall_prediction_history'
""")

rows = cursor.fetchall()

if not rows:
    print("No current lock waits found.")
else:
    for row in rows:
        print("Waiting process:", row[0])
        print("Waiting account:", row[1])
        print("Wait duration (seconds):", row[2])
        print("Waiting SQL:", row[3])
        print("Blocking process:", row[4])
        print("Blocking account:", row[5])
        print("Blocking lock duration:", row[6])
        print("Suggested kill-query command:", row[7])
        print("Suggested kill-connection command:", row[8])
        print("-" * 50)

cursor.close()
connection.close()
