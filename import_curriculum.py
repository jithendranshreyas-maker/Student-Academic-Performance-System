import csv
import os
from pathlib import Path
from dotenv import load_dotenv
import mysql.connector

load_dotenv(dotenv_path=Path.cwd() / ".env")

csv_path = Path("curriculum_5_years.csv")

with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
    rows = list(csv.DictReader(file))

required = [
    "Branch", "Academic_Year", "Semester",
    "Subject_Code", "Subject_Name", "Credits",
    "Maximum_Marks"
]

if not rows:
    raise SystemExit("CSV is empty.")

if not all(column in rows[0] for column in required):
    raise SystemExit("CSV columns do not match the expected format.")

keys = [
    (
        row["Branch"].strip(),
        int(row["Academic_Year"]),
        int(row["Semester"]),
        row["Subject_Code"].strip()
    )
    for row in rows
]

if len(keys) != len(set(keys)):
    raise SystemExit("Duplicate curriculum keys found. Nothing imported.")

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
    cur.execute("SELECT COUNT(*) FROM curriculum")
    existing = cur.fetchone()[0]

    if existing != 0:
        raise RuntimeError(
            f"Curriculum already contains {existing} rows. Import cancelled."
        )

    sql = """
        INSERT INTO curriculum
        (subject_code, subject_name, branch, academic_year,
         semester, credits, maximum_marks)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    values = [
        (
            row["Subject_Code"].strip(),
            row["Subject_Name"].strip(),
            row["Branch"].strip(),
            int(row["Academic_Year"]),
            int(row["Semester"]),
            int(row["Credits"]),
            int(row["Maximum_Marks"])
        )
        for row in rows
    ]

    cur.executemany(sql, values)
    con.commit()

    cur.execute("SELECT COUNT(*) FROM curriculum")
    print("Curriculum rows after import:", cur.fetchone()[0])
    print("Expected:", len(rows))

except Exception:
    con.rollback()
    raise
finally:
    con.close()
