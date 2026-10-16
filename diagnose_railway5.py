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
    SELECT TABLE_NAME
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN (
          'overall_prediction_history',
          'overall_prediction_subjects',
          'predictions',
          'prediction_feedback'
      )
""")

print("Existing prediction tables:")
for row in cursor.fetchall():
    print("-", row[0])

print("\nCurrent CREATE TABLE operations:")
cursor.execute("SHOW FULL PROCESSLIST")
for row in cursor.fetchall():
    if row[4] == "Query" and row[7] and "CREATE TABLE" in row[7].upper():
        print("Process:", row[0], "| State:", row[6], "| SQL:", row[7][:100])

cursor.close()
connection.close()
print("\nCheck complete.")
