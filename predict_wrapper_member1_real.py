"""
predict_wrapper_member1_real.py — Member 2 -> Member 4 integration point (FINAL)

Built on Member 1's real fraud_dataset.csv (26k transactions, genuine user_id,
rich behavioral/device/security signals). This is the final, most complete
model — supersedes predict_wrapper.py and predict_wrapper_full.py.

Key signals this model relies on (in order of importance):
1. receiver_account_age - how old the receiving account is (fraud -> almost
   always brand new accounts)
2. unusual_ip_flag - pre-computed anomaly flag for IP address
3. receiver_transaction_history - how much transaction history the receiver has
4. handle_registration_pattern - whether the UPI handle was recently registered

NOTE: dropped 'handle_verification_status' entirely - it was a 1:1 proxy for
the fraud label itself (data leak), not a real production-usable signal.

Usage:
    from predict_wrapper_member1_real import predict_transaction
    result = predict_transaction(txn_dict)
    # {"fraud_score": 0.98, "decision": "FLAG", "latency_ms": 0.05}
"""

import time
import pickle
import numpy as np
import onnxruntime as rt

MODEL_PATH = "fraud_model_member1_real.onnx"
META_PATH = "fraud_model_member1_real.pkl"

with open(META_PATH, "rb") as f:
    _bundle = pickle.load(f)

FEATURES = _bundle["features"]
THRESHOLD = _bundle["threshold"]

_session = rt.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
_input_name = _session.get_inputs()[0].name
_label_name = _session.get_outputs()[1].name

# Categories that were one-hot encoded during training - Member 4 needs to
# know the possible values for each so they can build the right dummy columns.
CATEGORICAL_COLUMNS = {
    "merchant_category_code": ["entertainment", "food", "retail", "services", "unknown", "utilities"],
    "session_source": ["app", "link"],
    "recent_app_installs": ["[]", "['screen_mirroring_app']"],
    "permissions_granted": ["[]", "['camera', 'screen_capture']"],
    "recognized_screen_sharing_apps": ["[]", "['screen_mirroring_app']"],
    "pin_entry_method": ["manual", "pasted"],
    "authorization_method": ["otp", "pin"],
    "transaction_type": ["collection_request", "payment"],
    "relationship_to_requester": [],  # fill in from real data if used
    "handle_typo_analysis": ["none", "typo_squatting"],
    "social_media_presence": [],
    "handle_registration_pattern": ["none", "recent"],
}


def build_features(txn: dict) -> np.ndarray:
    """
    txn should contain all raw fields matching fraud_dataset.csv columns
    (minus id/text columns), plus the engineered ones:
      - rolling_txn_count: this user's transaction count so far
      - new_merchant_flag: 1 if never paid this merchant before
      - known_device: 1 if this device has been used by this user before
      - avg_ticket_user: this user's historical average amount

    Categorical fields (e.g. transaction_type, pin_entry_method) should be
    passed as their raw string value; this function handles one-hot encoding.
    """
    feature_map = {}

    # Numeric / flag fields - pass through directly if present in FEATURES
    for f in FEATURES:
        if f in txn:
            feature_map[f] = txn[f]

    # One-hot encode categorical fields to match training-time columns
    for col, categories in CATEGORICAL_COLUMNS.items():
        if col in txn:
            value = txn[col]
            for cat in categories:
                dummy_col = f"{col}_{cat}".replace("[", "_").replace("]", "_").replace(",", "_")
                if dummy_col in FEATURES:
                    feature_map[dummy_col] = 1 if value == cat else 0

    # Fill anything missing with 0 (safe default for one-hot / rare flags)
    row = [feature_map.get(f, 0) for f in FEATURES]
    return np.array([row], dtype=np.float32)


def predict_transaction(txn: dict) -> dict:
    t0 = time.perf_counter()

    x = build_features(txn)
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
    normal_txn = {
        "amount": 800.0,
        "session_duration": 180,
        "authentication_attempts": 1,
        "receiver_account_age": 200,       # old, established account
        "receiver_transaction_history": 60,
        "transaction_amount_vs_sender_history": 1.5,
        "geographic_disparity": 9500,
        "transaction_time_of_day": 14,
        "unusual_device_flag": 0,
        "unusual_ip_flag": 0,
        "unusual_location_flag": 0,
        "unusual_transaction_amount_flag": 0,
        "transaction_velocity": 0,
        "failed_transaction_count": 0,
        "pin_entry_method": "manual",
        "authorization_method": "pin",
        "transaction_type": "payment",
        "handle_registration_pattern": "none",
        "rolling_txn_count": 12,
        "new_merchant_flag": 0,
        "known_device": 1,
        "avg_ticket_user": 750.0,
    }

    fraud_txn = {
        "amount": 12000.0,
        "session_duration": 90,
        "authentication_attempts": 2,
        "receiver_account_age": 0,          # brand new account - major red flag
        "receiver_transaction_history": 2,
        "transaction_amount_vs_sender_history": 8.0,
        "geographic_disparity": 15000,
        "transaction_time_of_day": 2,
        "unusual_device_flag": 1,
        "unusual_ip_flag": 1,
        "unusual_location_flag": 1,
        "unusual_transaction_amount_flag": 1,
        "transaction_velocity": 1,
        "failed_transaction_count": 1,
        "pin_entry_method": "pasted",
        "authorization_method": "otp",
        "transaction_type": "collection_request",
        "handle_registration_pattern": "recent",
        "rolling_txn_count": 3,
        "new_merchant_flag": 1,
        "known_device": 0,
        "avg_ticket_user": 900.0,
    }

    print("=== Normal transaction ===")
    print(predict_transaction(normal_txn))

    print("\n=== Suspicious transaction ===")
    print(predict_transaction(fraud_txn))
