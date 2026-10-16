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

try:
    cursor.execute("""
        SELECT
            ml.OBJECT_TYPE,
            ml.OBJECT_SCHEMA,
            ml.OBJECT_NAME,
            ml.LOCK_TYPE,
            ml.LOCK_DURATION,
            ml.LOCK_STATUS,
            t.PROCESSLIST_ID,
            t.PROCESSLIST_USER,
            t.PROCESSLIST_COMMAND,
            t.PROCESSLIST_TIME,
            t.PROCESSLIST_STATE,
            t.PROCESSLIST_INFO
        FROM performance_schema.metadata_locks AS ml
        LEFT JOIN performance_schema.threads AS t
            ON ml.OWNER_THREAD_ID = t.THREAD_ID
        WHERE ml.OBJECT_SCHEMA = DATABASE()
          AND ml.OBJECT_NAME = 'overall_prediction_history'
    """)

    rows = cursor.fetchall()

    if not rows:
        print("No metadata-lock records visible.")
    else:
        for row in rows:
            print("-" * 50)
            for name, value in zip(
                [
                    "Object type", "Schema", "Object", "Lock type",
                    "Duration", "Lock status", "Process ID", "User",
                    "Command", "Time", "State", "SQL"
                ],
                row
            ):
                print(f"{name}: {value}")

except mysql.connector.Error as error:
    print("Diagnostic query unavailable:", error)

finally:
    cursor.close()
    connection.close()
