import sqlite3

conn = sqlite3.connect("transactions.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM transactions")
count = cursor.fetchone()[0]

print(f"Total Transactions: {count}")

cursor.execute("SELECT * FROM transactions")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()