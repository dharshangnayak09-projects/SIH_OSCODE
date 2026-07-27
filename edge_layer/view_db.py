from pathlib import Path
import sqlite3

db_path = Path("edge_layer") / "transactions.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM transactions")
print("Total Transactions:", cursor.fetchone()[0])

cursor.execute("SELECT * FROM transactions")

for row in cursor.fetchall():
    print(row)

conn.close()