import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

required = [
    "MYSQLHOST",
    "MYSQLPORT",
    "MYSQLUSER",
    "MYSQLPASSWORD",
    "MYSQLDATABASE",
]

missing = [key for key in required if not os.getenv(key)]

if missing:
    print("Missing variables:", ", ".join(missing))
else:
    try:
        print("1. Connecting to Railway...", flush=True)

        connection = mysql.connector.connect(
            host=os.environ["MYSQLHOST"],
            port=int(os.environ["MYSQLPORT"]),
            user=os.environ["MYSQLUSER"],
            password=os.environ["MYSQLPASSWORD"],
            database=os.environ["MYSQLDATABASE"],
            connection_timeout=10,
        )

        print("2. Connected!", flush=True)
        cursor = connection.cursor()

        print("3. Creating table...", flush=True)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS overall_prediction_history (
                prediction_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(20) NOT NULL,
                academic_year VARCHAR(20),
                semester INT,
                predicted_sga DECIMAL(4,2),
                estimated_cg DECIMAL(4,2),
                predicted_backlog_count INT,
                backlog_risk VARCHAR(50),
                performance_category VARCHAR(100),
                overall_academic_risk VARCHAR(50),
                FOREIGN KEY (student_id)
                    REFERENCES students(student_id)
            )
        """)

        print("4. Table statement completed.", flush=True)
        connection.commit()
        print("5. Table created successfully!", flush=True)

        cursor.close()
        connection.close()

    except Exception as error:
        print("Error:", type(error).__name__, flush=True)
        print("Check connection settings without sharing credentials.")


