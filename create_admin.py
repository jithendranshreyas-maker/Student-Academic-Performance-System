
from getpass import getpass

import bcrypt
from auth import get_connection

username = input("Admin username: ").strip()
email = input("Admin email: ").strip().lower()
password = getpass("Admin password (minimum 8 characters): ")
confirm_password = getpass("Confirm admin password: ")

if not username or not email:
    print("Username and email are required.")
elif len(password) < 8:
    print("Password must be at least 8 characters.")
elif password != confirm_password:
    print("Passwords do not match.")
else:
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    con = get_connection()
    cursor = con.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO user_accounts
                (student_id, username, email, password_hash, role, is_active)
            VALUES
                (NULL, %s, %s, %s, 'admin', 1)
            """,
            (username, email, password_hash)
        )
        con.commit()
        print("Admin account created successfully!")

    except Exception as e:
        con.rollback()
        print("Could not create admin account:", e)

    finally:
        cursor.close()
        con.close()
