from pathlib import Path
import sqlite3

# Database will always be created inside the edge_layer folder
BASE_DIR = Path(__file__).resolve().parent
DATABASE_NAME = BASE_DIR / "transactions.db"


def get_connection():
    """Create and return a database connection."""
    print(f"Database path: {DATABASE_NAME}")

    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    """Create the transactions table if it doesn't exist."""
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            amount REAL NOT NULL,
            risk_score REAL NOT NULL,
            risk_level TEXT NOT NULL,
            decision TEXT,
            sender_name TEXT,
            sender_vpa TEXT,
            receiver_name TEXT,
            receiver_vpa TEXT,
            transaction_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    print("Transactions table ready.")

def get_recent_transactions(limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM transactions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_level='HIGH'")
    high = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_level='MEDIUM'")
    medium = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_level='LOW'")
    low = cursor.fetchone()[0]

    conn.close()

    return {
        "total_transactions": total,
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low
    }
def save_transaction(device_id, amount, risk_score, risk_level, decision=None,
                      sender_name=None, sender_vpa=None, receiver_name=None,
                      receiver_vpa=None, transaction_type=None):
    """Save one transaction into the database."""
    print("Saving transaction...")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO transactions
        (device_id, amount, risk_score, risk_level, decision,
         sender_name, sender_vpa, receiver_name, receiver_vpa, transaction_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            device_id,
            amount,
            risk_score,
            risk_level,
            decision,
            sender_name,
            sender_vpa,
            receiver_name,
            receiver_vpa,
            transaction_type,
        )
    )

    transaction_id = cursor.lastrowid

    conn.commit()

    print(f"Transaction saved successfully. Row ID: {transaction_id}")

    conn.close()

    return transaction_id

def get_all_transactions():
    """Return all saved transactions."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_recent_transactions(limit=10):
    """Return the latest transactions."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]