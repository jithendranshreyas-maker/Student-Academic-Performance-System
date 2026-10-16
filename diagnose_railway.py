import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

try:
    print("1. Connecting...", flush=True)

    connection = mysql.connector.connect(
        host=os.environ["MYSQLHOST"],
        port=int(os.environ["MYSQLPORT"]),
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"],
        connection_timeout=10,
    )

    print("2. Connected!", flush=True)
    cursor = connection.cursor()

    print("3. Checking target table...", flush=True)
    cursor.execute("""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'overall_prediction_history'
    """)
    print("Table:", cursor.fetchone(), flush=True)

    print("4. Checking active database operations...", flush=True)
    cursor.execute("SHOW FULL PROCESSLIST")
    for row in cursor.fetchall():
        print(
            "Process ID:", row[0],
            "| Command:", row[4],
            "| State:", row[6],
            "| Info:", str(row[7])[:120],
            flush=True
        )

    cursor.close()
    connection.close()
    print("5. Diagnostic complete.", flush=True)

except Exception as error:
    print("Diagnostic error:", type(error).__name__, str(error), flush=True)
