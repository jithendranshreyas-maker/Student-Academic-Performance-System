import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print(mysql.connector.__file__)
print(mysql.connector.__version__)

con=mysql.connector.connect(host=os.getenv("DB_HOST", "127.0.0.1"),
port=3306,
user=os.getenv("DB_USER"),
password=os.getenv("DB_PASSWORD"),
database=os.getenv("DB_NAME", "Project_2")
)
print("Connected Succesfully")
con.close()