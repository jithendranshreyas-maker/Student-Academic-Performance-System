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
        CREATE TABLE IF NOT EXISTS prediction_feedback (
            feedback_id INT AUTO_INCREMENT PRIMARY KEY,
            prediction_id INT NOT NULL,
            actual_marks DECIMAL(5,2),
            actual_grade VARCHAR(10),
            absolute_error DECIMAL(5,2),
            feedback_notes TEXT,
            feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prediction_id)
                REFERENCES predictions(prediction_id)
        )
    """)

    connection.commit()
    print("prediction_feedback created successfully!")

except mysql.connector.Error as error:
    print("Database error:", error)

finally:
    cursor.close()
    connection.close()
