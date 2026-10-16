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

cursor = connection.cursor(dictionary=True)

cursor.execute("""
    SELECT user_id, username, email, role, is_active
    FROM user_accounts
    ORDER BY user_id
""")

for user in cursor.fetchall():
    print(user)

cursor.close()
connection.close()

