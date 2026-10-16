import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

load_dotenv(dotenv_path=Path.cwd() / ".env")

with open(
    "semester_results_5_years.csv",
    newline="",
    encoding="utf-8-sig"
) as f:
    rows = list(csv.DictReader(f))

if len(rows) != 8000:
    raise SystemExit(f"Expected 8000 rows, found {len(rows)}. Cancelled.")

required = [
    "Student_ID", "Academic_Year", "Semester",
    "Semester_Percentage", "SGA", "Total_Backlogs", "Total_Credits"
]
if not rows or not all(column in rows[0] for column in required):
    raise SystemExit("Unexpected CSV columns. Import cancelled.")

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

    cur.execute("SELECT COUNT(*) FROM semester_results")
    existing = cur.fetchone()[0]
    if existing != 0:
        raise RuntimeError(
            f"semester_results contains {existing} rows. Import cancelled."
        )

    cur.execute("SELECT student_id FROM students")
    student_ids = {str(row[0]) for row in cur.fetchall()}

    missing = {
        row["Student_ID"].strip()
        for row in rows
        if row["Student_ID"].strip() not in student_ids
    }
    if missing:
        raise RuntimeError(
            f"{len(missing)} student IDs are missing. Import cancelled."
        )

    values = [
        (
            row["Student_ID"].strip(),
            int(row["Academic_Year"]),
            int(row["Semester"]),
            row["SGA"].strip() or None,
            row["Semester_Percentage"].strip() or None,
            int(float(row["Total_Backlogs"])),
            None,
            int(float(row["Total_Credits"]))
        )
        for row in rows
    ]

    sql = """
        INSERT INTO semester_results (
            student_id, academic_year, semester, sga,
            semester_percentage, total_backlogs, semester_status,
            total_credits
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cur.executemany(sql, values)
    con.commit()

    cur.execute("SELECT COUNT(*) FROM semester_results")
    print("Semester results after import:", cur.fetchone()[0])
    print("Expected:", len(rows))

except Exception:
    con.rollback()
    raise
finally:
    con.close()
