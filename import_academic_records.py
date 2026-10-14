
import pandas as pd
import mysql.connector
from pathlib import Path

BASE_DIR = Path.home() / "Documents" / "Python" / "ML" / "PROJECT_2"
CSV_PATH = BASE_DIR / "academic_records.csv"
BACKUP_PATH = BASE_DIR / "academic_records_before_import.csv"

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=input("MySQL password: "),
    database="Project_2",
    unix_socket="/tmp/mysql.sock",
)

try:
    df = pd.read_csv(CSV_PATH)

    required = [
        "student_id", "subject_code", "branch", "quiz1", "quiz2",
        "midsem", "assignment", "endsem", "classes_attended",
        "classes_held", "attendance_percentage", "marks_obtained",
        "maximum_marks", "grade", "grade_point", "backlog",
        "academic_year", "semester"
    ]
    missing = set(required) - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {sorted(missing)}")

    if len(df) != 32000:
        raise ValueError(f"Expected 32000 rows, found {len(df)}")

    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT subject_id, subject_code, branch, academic_year, semester
        FROM curriculum
    """)
    curriculum = cur.fetchall()

    curriculum_map = {
        (
            str(r["subject_code"]).strip(),
            str(r["branch"]).strip().casefold(),
            int(r["academic_year"]),
            int(r["semester"])
        ): r["subject_id"]
        for r in curriculum
    }

    keys = list(zip(
        df["subject_code"].astype(str).str.strip(),
        df["branch"].astype(str).str.strip().str.casefold(),
        df["academic_year"].astype(int),
        df["semester"].astype(int)
    ))

    df["subject_id"] = [curriculum_map.get(k) for k in keys]

    if df["subject_id"].isna().any():
        bad = df.loc[df["subject_id"].isna(),
                     ["subject_code", "branch", "academic_year", "semester"]]
        raise ValueError(
            "Some CSV rows do not match curriculum entries:\n"
            + bad.head(10).to_string(index=False)
        )

    cur.execute("SELECT COUNT(*) AS n FROM academic_records")
    existing_count = cur.fetchone()["n"]

    if existing_count:
        cur.execute("""
            SELECT student_id, subject_code, quiz1, quiz2, midsem,
                   assignment, endsem, classes_attended, classes_held,
                   attendance_percentage, marks_obtained, maximum_marks,
                   grade, grade_point, backlog, subject_id,
                   academic_year, semester
            FROM academic_records
        """)
        old_rows = cur.fetchall()
        pd.DataFrame(old_rows).to_csv(BACKUP_PATH, index=False)
        print(f"Existing records backed up to: {BACKUP_PATH}")

    columns = [
        "student_id", "subject_code", "quiz1", "quiz2", "midsem",
        "assignment", "endsem", "classes_attended", "classes_held",
        "attendance_percentage", "marks_obtained", "maximum_marks",
        "grade", "grade_point", "backlog", "subject_id",
        "academic_year", "semester"
    ]

    insert_sql = f"""
        INSERT INTO academic_records ({", ".join(columns)})
        VALUES ({", ".join(["%s"] * len(columns))})
    """

    cur.execute("START TRANSACTION")
    cur.execute("DELETE FROM academic_records")

    batch = []
    for _, row in df.iterrows():
        batch.append(tuple(
            None if pd.isna(row[c]) else row[c]
            for c in columns
        ))

        if len(batch) >= 1000:
            cur.executemany(insert_sql, batch)
            batch.clear()

    if batch:
        cur.executemany(insert_sql, batch)

    cur.execute("SELECT COUNT(*) AS n FROM academic_records")
    new_count = cur.fetchone()["n"]

    if new_count != len(df):
        raise RuntimeError(
            f"Import count mismatch: expected {len(df)}, got {new_count}"
        )

    conn.commit()
    print(f"Import successful: {new_count} academic records loaded.")

except Exception as exc:
    conn.rollback()
    print("Import failed; the database transaction was rolled back.")
    print(exc)
    raise

finally:
    conn.close()
