"""
Integration Step 3 — unified predict_wrapper for Member 4
=============================================================
Same call signature as Dhruv's original predict_wrapper.py so Member 4
doesn't have to change their API code, just the import:

    from predict_wrapper_v2 import predict_transaction
    result = predict_transaction(txn_dict, sender_history)
    # {"fraud_score": 0.87, "decision": "FLAG", "mule_score": 0.41, "latency_ms": 0.05}

What changed vs. the original:
  - Loads models/fraud_model_v2.pkl (11 features, includes mule_score)
    instead of fraud_model.pkl (10 features) — retrain with
    retrain_with_mule_score.py first if you haven't.
  - Looks up mule_score from data/account_mule_features.csv (Member 3's
    batch output) instead of recomputing the graph per-request — graph
    features are a BATCH job (recompute every N minutes/hours on the full
    transaction history), never a per-transaction computation. This is the
    same "don't recompute expensive stats live" principle the original
    predict_wrapper.py already used for sender_history.
  - Falls back to the plain pickle model if fraud_model.onnx / onnxruntime
    aren't available — same idea as Member 2's fallback pattern elsewhere
    in this project, so this still runs without every package installed.

txn / sender_history shapes are UNCHANGED from Dhruv's original wrapper —
see build_features() below for the exact dict keys expected.
"""

import pickle
import time
from math import radians, sin, cos, sqrt, atan2

import numpy as np

MODEL_PKL_PATH = "models/fraud_model_v2.pkl"
MULE_SCORES_PATH = "data/account_mule_features.csv"

with open(MODEL_PKL_PATH, "rb") as f:
    _bundle = pickle.load(f)
_MODEL = _bundle["model"]
FEATURES = _bundle["features"]           # now includes "mule_score" as the 11th feature
THRESHOLD = _bundle["threshold"]

# try ONNX for speed; fall back to the plain sklearn/xgboost model object
_USE_ONNX = False
try:
    import onnxruntime as rt
    _session = rt.InferenceSession("models/fraud_model_v2.onnx", providers=["CPUExecutionProvider"])
    _input_name = _session.get_inputs()[0].name
    _label_name = _session.get_outputs()[1].name
    _USE_ONNX = True
except Exception:
    pass  # no ONNX export yet for v2 — plain pickle model works fine, just a bit slower


def _load_mule_scores():
    import csv
    scores = {}
    try:
        with open(MULE_SCORES_PATH, newline="") as f:
            for row in csv.DictReader(f):
                scores[row["account"]] = float(row["mule_score"])
    except FileNotFoundError:
        pass  # Member 3 hasn't run yet — everything defaults to 0, not a crash
    return scores


_MULE_SCORES = _load_mule_scores()


def get_mule_score(vpa: str) -> float:
    return _MULE_SCORES.get(vpa, 0.0)


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def build_features(txn: dict, sender_history: dict) -> np.ndarray:
    """
    Identical to Dhruv's original build_features, plus mule_score looked up
    for BOTH sender and receiver (take the max — a transaction is risky if
    either party is a flagged account).

    txn: {"amount", "timestamp", "hour", "lat", "lon", "transaction_type", "receiver_vpa"}
          + "sender_vpa" (needed here for the mule_score lookup; the original
          wrapper didn't need it since it had no graph feature)
    sender_history: {"txn_count_1h", "avg_ticket_sender", "amount_std_sender",
                      "last_txn_time", "last_lat", "last_lon", "known_payees"}
    """
    amount = txn["amount"]
    avg = sender_history.get("avg_ticket_sender", amount)
    std = sender_history.get("amount_std_sender", 1.0) or 1.0
    amount_zscore = (amount - avg) / std

    if sender_history.get("last_txn_time") is not None:
        mins_elapsed = (txn["timestamp"] - sender_history["last_txn_time"]).total_seconds() / 60
        mins_elapsed = max(mins_elapsed, 0.01)
        dist_km = _haversine_km(sender_history["last_lat"], sender_history["last_lon"], txn["lat"], txn["lon"])
        geo_velocity_kmph = dist_km / max(mins_elapsed / 60, 1 / 60)
    else:
        mins_elapsed = 999.0
        geo_velocity_kmph = 0.0

    new_payee_flag = 0 if txn["receiver_vpa"] in sender_history.get("known_payees", set()) else 1
    is_odd_hour = 1 if txn["hour"] in (23, 0, 1, 2, 3, 4) else 0
    is_p2m = 1 if txn["transaction_type"] == "P2M" else 0

    sender_mule = get_mule_score(txn.get("sender_vpa", ""))
    receiver_mule = get_mule_score(txn.get("receiver_vpa", ""))
    mule_score = max(sender_mule, receiver_mule)

    feature_map = {
        "amount": amount, "txn_count_1h": sender_history.get("txn_count_1h", 0),
        "avg_ticket_sender": avg, "amount_zscore": amount_zscore,
        "time_since_last_txn_min": mins_elapsed, "geo_velocity_kmph": geo_velocity_kmph,
        "new_payee_flag": new_payee_flag, "is_odd_hour": is_odd_hour,
        "hour": txn["hour"], "is_p2m": is_p2m, "mule_score": mule_score,
    }
    return np.array([[feature_map[f] for f in FEATURES]], dtype=np.float32), mule_score


def predict_transaction(txn: dict, sender_history: dict) -> dict:
    t0 = time.perf_counter()
    x, mule_score = build_features(txn, sender_history)

    if _USE_ONNX:
        proba = _session.run([_label_name], {_input_name: x})[0][0][1]
    else:
        proba = _MODEL.predict_proba(x)[0][1]

    decision = "FLAG" if proba >= THRESHOLD else "ALLOW"
    latency_ms = round((time.perf_counter() - t0) * 1000, 4)

    return {
        "fraud_score": float(proba),
        "mule_score": round(mule_score, 4),
        "decision": decision,
        "threshold_used": float(THRESHOLD),
        "latency_ms": latency_ms,
    }


if __name__ == "__main__":
    from datetime import datetime

    normal_txn = {
        "amount": 450.0, "timestamp": datetime(2026, 1, 15, 14, 30), "hour": 14,
        "lat": 19.076, "lon": 72.877, "transaction_type": "P2P",
        "sender_vpa": "user1@upi", "receiver_vpa": "user42@upi",
    }
    normal_history = {
        "txn_count_1h": 1, "avg_ticket_sender": 500.0, "amount_std_sender": 150.0,
        "last_txn_time": datetime(2026, 1, 15, 10, 0), "last_lat": 19.076, "last_lon": 72.877,
        "known_payees": {"user42@upi", "user7@upi"},
    }
    print("=== Normal transaction ===")
    print(predict_transaction(normal_txn, normal_history))
