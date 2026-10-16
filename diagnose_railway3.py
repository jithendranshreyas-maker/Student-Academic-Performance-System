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

cursor.execute("DESCRIBE sys.schema_table_lock_waits")

for row in cursor.fetchall():
    print(row[0], "|", row[1])

cursor.close()
connection.close()
