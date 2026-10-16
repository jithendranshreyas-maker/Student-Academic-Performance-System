from auth import get_connection

con = get_connection()
cursor = con.cursor()

cursor.execute("DESCRIBE user_accounts")

for column in cursor.fetchall():
    print(column)

cursor.close()
con.close()