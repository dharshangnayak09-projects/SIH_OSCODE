from predict_wrapper_v2 import predict_transaction
from datetime import datetime

suspicious_txn = {
    "amount": 9800.0, "timestamp": datetime(2026, 1, 15, 2, 10), "hour": 2,
    "lat": 28.613, "lon": 77.209,  # Delhi
    "transaction_type": "P2P",
    "sender_vpa": "user1@upi", "receiver_vpa": "unknown99@upi",
}
suspicious_history = {
    "txn_count_1h": 4, "avg_ticket_sender": 500.0, "amount_std_sender": 150.0,
    "last_txn_time": datetime(2026, 1, 15, 1, 55),
    "last_lat": 19.076, "last_lon": 72.877,  # was in Mumbai 15 min ago — impossible travel
    "known_payees": {"user42@upi"},
}
print(predict_transaction(suspicious_txn, suspicious_history))