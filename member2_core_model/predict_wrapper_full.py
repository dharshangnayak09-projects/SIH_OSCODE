"""
predict_wrapper_full.py — Member 2 -> Member 4 integration point (v2)

Updated for the fraud_model_full model, trained on a dataset with genuine
per-sender behavioral history (rolling_txn_count, avg_ticket_sender, etc.)
instead of the earlier synthetic model's feature set.

NOTE: This version does NOT include geo_velocity_kmph, since the underlying
dataset has no location data. If Member 1 or the team later adds location
per transaction, that feature can be re-added (see original predict_wrapper.py
for the geo-velocity calculation logic to reuse).

Usage:
    from predict_wrapper_full import predict_transaction
    result = predict_transaction(txn_dict, sender_history)
    # {"fraud_score": 0.87, "decision": "FLAG", "latency_ms": 0.03}
"""

import time
import pickle
import numpy as np
import onnxruntime as rt

MODEL_PATH = "fraud_model_full.onnx"
META_PATH = "fraud_model_full.pkl"

with open(META_PATH, "rb") as f:
    _bundle = pickle.load(f)

FEATURES = _bundle["features"]
THRESHOLD = _bundle["threshold"]

_session = rt.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
_input_name = _session.get_inputs()[0].name
_label_name = _session.get_outputs()[1].name


def build_features(txn: dict, sender_history: dict) -> np.ndarray:
    """
    Turns a raw transaction + sender's rolling stats into the feature
    vector the model expects, in the correct order.

    txn: {
        "amount": float, "hour_of_day": int, "is_weekend": int,
        "transaction_type": "P2P"/"P2M"/"Bill Payment"/"Recharge",
        "sender_bank": str, "receiver_bank": str
    }
    sender_history: {
        "rolling_txn_count": int,          # this sender's total txn count so far
        "avg_ticket_sender": float,        # sender's historical average amount
        "amount_std_sender": float,        # sender's historical std dev of amount
        "last_txn_time": datetime or None, # for time_since_last_txn_min
        "known_payees": set                # for new_payee_flag (bank+category keys)
    }
    """
    amount = txn["amount"]
    avg = sender_history.get("avg_ticket_sender", amount)
    std = sender_history.get("amount_std_sender", 1.0) or 1.0
    amount_zscore = (amount - avg) / std

    if sender_history.get("last_txn_time") is not None and "timestamp" in txn:
        mins_elapsed = (txn["timestamp"] - sender_history["last_txn_time"]).total_seconds() / 60
        mins_elapsed = max(mins_elapsed, 0.01)
    else:
        mins_elapsed = 999.0

    payee_key = f"{txn.get('receiver_bank','')}_{txn.get('merchant_category','')}"
    new_payee_flag = 0 if payee_key in sender_history.get("known_payees", set()) else 1

    is_odd_hour = 1 if txn["hour_of_day"] in (23, 0, 1, 2, 3, 4) else 0
    is_p2m = 1 if txn["transaction_type"] == "P2M" else 0
    bank_mismatch = 1 if txn.get("sender_bank") != txn.get("receiver_bank") else 0

    feature_map = {
        "amount": amount,
        "rolling_txn_count": sender_history.get("rolling_txn_count", 1),
        "avg_ticket_sender": avg,
        "amount_zscore": amount_zscore,
        "time_since_last_txn_min": mins_elapsed,
        "new_payee_flag": new_payee_flag,
        "is_odd_hour": is_odd_hour,
        "hour_of_day": txn["hour_of_day"],
        "is_p2m": is_p2m,
        "bank_mismatch": bank_mismatch,
        "is_weekend": txn.get("is_weekend", 0),
    }

    return np.array([[feature_map[f] for f in FEATURES]], dtype=np.float32)


def predict_transaction(txn: dict, sender_history: dict) -> dict:
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


if __name__ == "__main__":
    from datetime import datetime

    normal_txn = {
        "amount": 450.0,
        "timestamp": datetime(2024, 6, 15, 14, 30),
        "hour_of_day": 14,
        "is_weekend": 0,
        "transaction_type": "P2P",
        "sender_bank": "HDFC",
        "receiver_bank": "HDFC",
        "merchant_category": "Grocery"
    }
    normal_history = {
        "rolling_txn_count": 42,
        "avg_ticket_sender": 500.0,
        "amount_std_sender": 150.0,
        "last_txn_time": datetime(2024, 6, 15, 10, 0),
        "known_payees": {"HDFC_Grocery", "SBI_Fuel"}
    }

    fraud_txn = {
        "amount": 7200.0,
        "timestamp": datetime(2024, 6, 15, 2, 10),
        "hour_of_day": 2,
        "is_weekend": 0,
        "transaction_type": "P2P",
        "sender_bank": "HDFC",
        "receiver_bank": "ICICI",
        "merchant_category": "Other"
    }
    fraud_history = {
        "rolling_txn_count": 43,
        "avg_ticket_sender": 500.0,
        "amount_std_sender": 150.0,
        "last_txn_time": datetime(2024, 6, 15, 1, 55),
        "known_payees": {"HDFC_Grocery"}
    }

    print("=== Normal transaction ===")
    print(predict_transaction(normal_txn, normal_history))

    print("\n=== Suspicious transaction ===")
    print(predict_transaction(fraud_txn, fraud_history))
