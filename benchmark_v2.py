from predict_wrapper_v2 import predict_transaction
from datetime import datetime
import numpy as np

txn = {"amount": 450.0, "timestamp": datetime(2026,1,15,14,30), "hour":14,
       "lat":19.076, "lon":72.877, "transaction_type":"P2P",
       "sender_vpa":"user1@upi", "receiver_vpa":"user42@upi"}
hist = {"txn_count_1h":1, "avg_ticket_sender":500.0, "amount_std_sender":150.0,
        "last_txn_time":datetime(2026,1,15,10,0), "last_lat":19.076, "last_lon":72.877,
        "known_payees":{"user42@upi","user7@upi"}}

for _ in range(20):
    predict_transaction(txn, hist)  # warmup

latencies = [predict_transaction(txn, hist)["latency_ms"] for _ in range(200)]
print(f"p50: {np.percentile(latencies, 50):.3f}ms  p95: {np.percentile(latencies, 95):.3f}ms")