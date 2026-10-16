import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

load_dotenv(dotenv_path=Path.cwd() / ".env")

with open(
    "academic_records_5_years_rescaled.csv",
    newline="",
    encoding="utf-8-sig"
) as f:
    rows = list(csv.DictReader(f))

print("CSV academic records:", len(rows))

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

    cur.execute("SELECT student_id FROM students")
    student_ids = {str(row[0]) for row in cur.fetchall()}

    cur.execute("""
        SELECT subject_id, branch, academic_year, semester, subject_code
        FROM curriculum
    """)
    curriculum_keys = {
        (str(branch).strip(), int(year), int(semester), str(code).strip())
        for _, branch, year, semester, code in cur.fetchall()
    }

    cur.execute("SELECT COUNT(*) FROM academic_records")
    existing_records = cur.fetchone()[0]

    missing_students = set()
    missing_subjects = set()

    for row in rows:
        student_id = row["student_id"].strip()
        if student_id not in student_ids:
            missing_students.add(student_id)

        key = (
            row["branch"].strip(),
            int(row["academic_year"]),
            int(row["semester"]),
            row["subject_code"].strip()
        )
        if key not in curriculum_keys:
            missing_subjects.add(key)

    print("Missing student IDs:", len(missing_students))
    print("Missing curriculum matches:", len(missing_subjects))
    print("Existing academic records:", existing_records)

    if missing_students:
        print("Sample missing students:", list(missing_students)[:5])
    if missing_subjects:
        print("Sample missing curriculum keys:", list(missing_subjects)[:5])

    if (
        len(rows) == 32000
        and not missing_students
        and not missing_subjects
        and existing_records == 0
    ):
        print("VALIDATION PASSED — ready for the import step.")
    else:
        print("VALIDATION FAILED — do not import yet.")

finally:
    con.close()
