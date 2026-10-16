from auth import get_connection

con = get_connection()
cursor = con.cursor()

try:
    cursor.execute("""
        ALTER TABLE user_accounts
        MODIFY COLUMN student_id VARCHAR(20) NULL
    """)
    con.commit()
    print("Schema updated successfully.")
except Exception as e:
    con.rollback()
    print("Schema update failed:", e)
finally:
    cursor.close()
    con.close()