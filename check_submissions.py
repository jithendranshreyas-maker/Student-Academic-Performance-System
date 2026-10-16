
from pathlib import Path
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv(dotenv_path=Path.cwd() / ".env")

con = mysql.connector.connect(
    host=os.environ["MYSQLHOST"],
    port=int(os.environ["MYSQLPORT"]),
    user=os.environ["MYSQLUSER"],
    password=os.environ["MYSQLPASSWORD"],
    database=os.environ["MYSQLDATABASE"],
    connection_timeout=10
)

try:

    cur = con.cursor()

    cur.execute("""
        ALTER TABLE student_academic_submissions
        MODIFY COLUMN student_id VARCHAR(20) NOT NULL
    """)

    con.commit()

    cur.execute("SHOW COLUMNS FROM student_academic_submissions LIKE 'student_id'")
    print("Updated column:", cur.fetchone())


finally:
    con.close()
