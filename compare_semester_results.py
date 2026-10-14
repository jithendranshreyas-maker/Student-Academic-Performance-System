import pandas as pd
import mysql.connector
from pathlib import Path

BASE_DIR = Path.home() / "Documents" / "Python" / "ML" / "PROJECT_2"
csv_path = BASE_DIR / "semester_results.csv"

csv_df = pd.read_csv(csv_path)

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=input("MySQL password: "),
    database="Project_2",
    unix_socket="/tmp/mysql.sock"
)

try:
    db_df = pd.read_sql(
        """
        SELECT student_id, academic_year, semester, sga,
               semester_percentage, total_backlogs, semester_status
        FROM semester_results
        """,
        conn
    )
finally:
    conn.close()

key_cols = ["student_id", "academic_year", "semester"]
value_cols = [
    "sga", "semester_percentage",
    "total_backlogs", "semester_status"
]

csv_df["student_id"] = csv_df["student_id"].astype(str)
db_df["student_id"] = db_df["student_id"].astype(str)

for col in ["academic_year", "semester", "total_backlogs"]:
    csv_df[col] = pd.to_numeric(csv_df[col], errors="coerce")
    db_df[col] = pd.to_numeric(db_df[col], errors="coerce")

for col in ["sga", "semester_percentage"]:
    csv_df[col] = pd.to_numeric(csv_df[col], errors="coerce")
    db_df[col] = pd.to_numeric(db_df[col], errors="coerce")

print("CSV rows:", len(csv_df))
print("Database rows:", len(db_df))
print("Duplicate keys in CSV:", csv_df.duplicated(key_cols).sum())
print("Duplicate keys in database:", db_df.duplicated(key_cols).sum())

merged = csv_df.merge(
    db_df,
    on=key_cols,
    how="outer",
    suffixes=("_csv", "_db"),
    indicator=True
)

print("\nKey matches:")
print(merged["_merge"].value_counts().to_string())

matched = merged[merged["_merge"] == "both"].copy()

for col in value_cols:
    csv_col = f"{col}_csv"
    db_col = f"{col}_db"

    if col in ["sga", "semester_percentage"]:
        differs = (
            (matched[csv_col] - matched[db_col]).abs() > 0.01
        ) | (matched[csv_col].isna() != matched[db_col].isna())
    else:
        differs = (
            matched[csv_col].astype(str) != matched[db_col].astype(str)
        )

    print(f"{col} differences:", int(differs.sum()))