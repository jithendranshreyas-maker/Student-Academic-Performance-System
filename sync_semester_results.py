
import pandas as pd
import mysql.connector
from datetime import datetime

CSV_PATH = "semester_results.csv"

con = mysql.connector.connect(
    host="localhost",
    user="root",
    password=input("MySQL password: "),
    database="Project_2"
)

cursor = con.cursor()

try:
    cursor.execute("SELECT * FROM semester_results")
    columns = [col[0] for col in cursor.description]
    existing_rows = cursor.fetchall()

    backup_path = f"semester_results_backup_{datetime.now():%Y%m%d_%H%M%S}.csv"
    pd.DataFrame(existing_rows, columns=columns).to_csv(backup_path, index=False)
    print(f"Database backup saved to {backup_path}")

    df = pd.read_csv(CSV_PATH)
    df.columns = df.columns.str.strip().str.lower()

    required = [
        "student_id",
        "academic_year",
        "semester",
        "sga",
        "semester_percentage",
        "total_backlogs",
        "semester_status"
    ]

    if list(df.columns) != required:
        raise ValueError(f"Unexpected CSV columns: {df.columns.tolist()}")

    if df.duplicated(["student_id", "academic_year", "semester"]).any():
        raise ValueError("CSV contains duplicate semester keys; stopping.")

    query = """
        INSERT INTO semester_results
        (student_id, academic_year, semester, sga,
         semester_percentage, total_backlogs, semester_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            sga = VALUES(sga),
            semester_percentage = VALUES(semester_percentage),
            total_backlogs = VALUES(total_backlogs),
            semester_status = VALUES(semester_status)
    """

    cursor.executemany(query, [
        (
            str(row.student_id),
            int(row.academic_year),
            int(row.semester),
            None if pd.isna(row.sga) else float(row.sga),
            None if pd.isna(row.semester_percentage) else float(row.semester_percentage),
            int(row.total_backlogs),
            row.semester_status
        )
        for row in df.itertuples(index=False)
    ])

    con.commit()
    print(f"Synchronization complete: processed {len(df)} CSV rows.")

except Exception:
    con.rollback()
    raise

finally:
    cursor.close()
    con.close()
