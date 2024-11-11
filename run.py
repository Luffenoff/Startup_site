import sqlite3
conn = sqlite3.connect('startup_platform.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM startup_submissions")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()


