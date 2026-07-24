"""
predict_wrapper.py — Member 2 -> Member 4 integration point

Member 4 imports `predict_transaction()` from this file and calls it with
a raw transaction dict. It returns fraud_score, decision, and latency_ms.

Usage:
    from predict_wrapper import predict_transaction
    result = predict_transaction(txn_dict, sender_history)
    # {"fraud_score": 0.87, "decision": "FLAG", "latency_ms": 0.03}

NOTE: In production, `sender_history` (rolling stats per sender) should come
from Member 1's live feature pipeline / a fast cache (e.g. Redis), not
recomputed from scratch per request. This wrapper assumes those stats are
already available and just need light math to turn into model features.
"""

import time
import pickle
import numpy as np
import onnxruntime as rt
from math import radians, sin, cos, sqrt, atan2

# ---------- Load model once at import time (not per-request) ----------
MODEL_PATH = "fraud_model.onnx"
META_PATH = "fraud_model.pkl"  # used only for feature order + threshold

with open(META_PATH, "rb") as f:
    _bundle = pickle.load(f)

FEATURES = _bundle["features"]
THRESHOLD = _bundle["threshold"]

_session = rt.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
_input_name = _session.get_inputs()[0].name
_label_name = _session.get_outputs()[1].name  # probability output


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def build_features(txn: dict, sender_history: dict) -> np.ndarray:
    """
    Turns a raw transaction + sender's rolling stats into the exact
    feature vector the model expects, in the correct order.

    txn: {
        "amount": float, "timestamp": datetime, "hour": int,
        "lat": float, "lon": float, "transaction_type": "P2P"/"P2M",
        "receiver_vpa": str
    }
    sender_history: {
        "txn_count_1h": int,
        "avg_ticket_sender": float,
        "amount_std_sender": float,       # needed to compute zscore
        "last_txn_time": datetime or None,
        "last_lat": float or None,
        "last_lon": float or None,
        "known_payees": set
    }
    """
    amount = txn["amount"]
    avg = sender_history.get("avg_ticket_sender", amount)
    std = sender_history.get("amount_std_sender", 1.0) or 1.0
    amount_zscore = (amount - avg) / std

    if sender_history.get("last_txn_time") is not None:
        mins_elapsed = (txn["timestamp"] - sender_history["last_txn_time"]).total_seconds() / 60
        mins_elapsed = max(mins_elapsed, 0.01)
        dist_km = _haversine_km(
            sender_history["last_lat"], sender_history["last_lon"],
            txn["lat"], txn["lon"]
        )
        geo_velocity_kmph = dist_km / max(mins_elapsed / 60, 1 / 60)
    else:
        mins_elapsed = 999.0
        geo_velocity_kmph = 0.0

    new_payee_flag = 0 if txn["receiver_vpa"] in sender_history.get("known_payees", set()) else 1
    is_odd_hour = 1 if txn["hour"] in (23, 0, 1, 2, 3, 4) else 0
    is_p2m = 1 if txn["transaction_type"] == "P2M" else 0

    feature_map = {
        "amount": amount,
        "txn_count_1h": sender_history.get("txn_count_1h", 0),
        "avg_ticket_sender": avg,
        "amount_zscore": amount_zscore,
        "time_since_last_txn_min": mins_elapsed,
        "geo_velocity_kmph": geo_velocity_kmph,
        "new_payee_flag": new_payee_flag,
        "is_odd_hour": is_odd_hour,
        "hour": txn["hour"],
        "is_p2m": is_p2m,
    }

    # Order matters — must match FEATURES from training
    return np.array([[feature_map[f] for f in FEATURES]], dtype=np.float32)


def predict_transaction(txn: dict, sender_history: dict) -> dict:
    """
    Main entry point for Member 4's API layer.
    Returns fraud_score (0-1), decision (ALLOW/FLAG), and latency_ms.
    """
    t0 = time.perf_counter()

    x = build_features(txn, sender_history)
    proba = _session.run([_label_name], {_input_name: x})[0][0][1]
    decision = "FLAG" if proba >= THRESHOLD else "ALLOW"

    t1 = time.perf_counter()

    return {
        "fraud_score": float(proba),
        "decision": decision,
        "threshold_used": float(THRESHOLD),
        "latency_ms": round((t1 - t0) * 1000, 4)
    }


# ---------- Quick manual test when run directly ----------
if __name__ == "__main__":
    from datetime import datetime

    # Simulate a normal transaction
    normal_txn = {
        "amount": 450.0,
        "timestamp": datetime(2026, 1, 15, 14, 30),
        "hour": 14,
        "lat": 19.076, "lon": 72.877,  # Mumbai
        "transaction_type": "P2P",
        "receiver_vpa": "user42@upi"
    }
    normal_history = {
        "txn_count_1h": 1,
        "avg_ticket_sender": 500.0,
        "amount_std_sender": 150.0,
        "last_txn_time": datetime(2026, 1, 15, 10, 0),
        "last_lat": 19.076, "last_lon": 72.877,
        "known_payees": {"user42@upi", "user7@upi"}
    }

    # Simulate a suspicious transaction: new payee, huge amount, odd hour, geo jump
    fraud_txn = {
        "amount": 9800.0,
        "timestamp": datetime(2026, 1, 15, 2, 10),
        "hour": 2,
        "lat": 28.613, "lon": 77.209,  # Delhi
        "transaction_type": "P2P",
        "receiver_vpa": "unknown99@upi"
    }
    fraud_history = {
        "txn_count_1h": 4,
        "avg_ticket_sender": 500.0,
        "amount_std_sender": 150.0,
        "last_txn_time": datetime(2026, 1, 15, 1, 55),
        "last_lat": 19.076, "last_lon": 72.877,  # was in Mumbai 15 min ago
        "known_payees": {"user42@upi"}
    }

    print("=== Normal transaction ===")
    print(predict_transaction(normal_txn, normal_history))

    print("\n=== Suspicious transaction ===")
    print(predict_transaction(fraud_txn, fraud_history))