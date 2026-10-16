import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

load_dotenv(dotenv_path=Path.cwd() / ".env")

with open("students_5_years.csv", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 1000:
    raise SystemExit(f"Expected 1000 students, found {len(rows)}. Cancelled.")

ids = [row["Student_ID"].strip() for row in rows]
if len(ids) != len(set(ids)):
    raise SystemExit("Duplicate student IDs in CSV. Cancelled.")

try:
    con = mysql.connector.connect(
        host=os.environ["MYSQLHOST"],
        port=int(os.environ["MYSQLPORT"]),
        user=os.environ["MYSQLUSER"],
        password=os.environ["MYSQLPASSWORD"],
        database=os.environ["MYSQLDATABASE"],
        connection_timeout=10
    )
    print("Database connection successful.")
except mysql.connector.Error as e:
    print("Database connection failed:", type(e).__name__)
    print("Error code:", e.errno)
    raise SystemExit("Import cancelled. No rows were inserted.")

try:
    cur = con.cursor()
    cur.execute("SELECT student_id FROM students")
    existing_ids = {str(row[0]) for row in cur.fetchall()}

    conflicts = existing_ids.intersection(ids)
    if conflicts:
        raise RuntimeError(
            f"{len(conflicts)} student IDs already exist. Import cancelled."
        )

    sql = """
        INSERT INTO students
        (student_id, name, email, section, branch, academic_year)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    values = [
        (
            row["Student_ID"].strip(),
            row["Name"].strip(),
            row["Email"].strip(),
            row["Section"].strip(),
            row["Branch"].strip(),
            row["Academic_Year"].strip()
        )
        for row in rows
    ]

    cur.executemany(sql, values)
    con.commit()

    cur.execute("SELECT COUNT(*) FROM students")
    print("Total students after import:", cur.fetchone()[0])

    cur.execute(
        "SELECT COUNT(*) FROM students WHERE student_id = %s",
        ("STU000001",)
    )
    print("Original student still present:", cur.fetchone()[0] == 1)

    cur.execute(
        "SELECT COUNT(*) FROM user_accounts WHERE username = %s",
        ("arjunn",)
    )
    print("Original login still present:", cur.fetchone()[0] == 1)

except Exception:
    con.rollback()
    raise
finally:
    con.close()
