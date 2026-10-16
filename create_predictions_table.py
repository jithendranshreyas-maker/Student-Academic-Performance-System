import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

connection = mysql.connector.connect(
    host=os.environ["MYSQLHOST"],
    port=int(os.environ["MYSQLPORT"]),
    user=os.environ["MYSQLUSER"],
    password=os.environ["MYSQLPASSWORD"],
    database=os.environ["MYSQLDATABASE"],
    connection_timeout=10,
)

cursor = connection.cursor()

try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(20) NOT NULL,
            subject_id INT NOT NULL,
            prediction_type VARCHAR(50),
            predicted_marks DECIMAL(5,2),
            predicted_grade VARCHAR(10),
            lower_bound DECIMAL(5,2),
            upper_bound DECIMAL(5,2),
            prediction_confidence DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id)
                REFERENCES students(student_id),
            FOREIGN KEY (subject_id)
                REFERENCES curriculum(subject_id)
        )
    """)

    connection.commit()
    print("predictions created successfully!")

except mysql.connector.Error as error:
    print("Database error:", error)

finally:
    cursor.close()
    connection.close()
