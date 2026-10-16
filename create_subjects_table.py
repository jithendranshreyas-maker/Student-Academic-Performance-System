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
        CREATE TABLE IF NOT EXISTS overall_prediction_subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prediction_id INT NOT NULL,
            subject_code VARCHAR(20) NOT NULL,
            subject_name VARCHAR(150) NOT NULL,
            credits INT,
            predicted_marks DECIMAL(5,2),
            estimated_grade VARCHAR(10),
            attendance_percentage DECIMAL(5,2),
            backlog_risk VARCHAR(50),
            historical_average DECIMAL(5,2),
            performance_vs_history VARCHAR(100),
            FOREIGN KEY (prediction_id)
                REFERENCES overall_prediction_history(prediction_id)
        )
    """)

    connection.commit()
    print("overall_prediction_subjects created successfully!")

except mysql.connector.Error as error:
    print("Database error:", error)

finally:
    cursor.close()
    connection.close()

