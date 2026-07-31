"""
predict_with_mule_score.py (v2 -- separates mule_score from the fraud decision)

WHY V1 WAS CHANGED
--------------------
Retraining Member 2's model WITH mule_score included let mule_score
dominate feature importance (98%) and override real fraud signals: a test
transaction with every red-flag field set to 1 (brand-new receiver account,
pasted PIN, OTP override, unusual device/IP/location, all 1) still came back
"ALLOW" with a fraud_score of 0.019, purely because it was addressed to a
merchant with a high mule_score (which, per this dataset's structure, means
"repeat business" - the OPPOSITE of suspicious). A well-established merchant
can still receive a genuinely fraudulent payment in the real world; this
version doesn't let mule_score silently override that.

THIS VERSION
-------------
Uses Member 2's ORIGINAL model (predict_wrapper_member1_real.py, trained
WITHOUT mule_score) for the actual fraud_score and decision -- that model's
feature importance is healthier and doesn't get overridden by merchant
repeat-business history. mule_score is still computed and returned in the
response as a separate, informational signal (e.g. for a "collection-point
account" flag on the dashboard, or for Member 4's rules engine to use as
its OWN independent input) -- it just no longer feeds into or can override
the core fraud decision.

Usage:
    from predict_with_mule_score import predict_transaction
    result = predict_transaction(txn_dict)   # txn_dict must include merchant_id
    # {
    #   "fraud_score": 0.98, "decision": "FLAG", "latency_ms": 0.05,
    #   "mule_score": 0.12, "mule_flag_reason": "..."
    # }

Requires (same folder):
    fraud_model_member1_real.onnx      (Member 2's ORIGINAL model files)
    fraud_model_member1_real.pkl
    output/account_mule_features.csv   (from member3_mule_detection.py)
"""

import time

from predict_wrapper_member1_real import predict_transaction as _predict_core
from member3_mule_detection import get_mule_score

_MULE_REASON_CACHE = None


def _get_mule_reason(merchant_id: str, path: str = "output/account_mule_features.csv") -> str:
    global _MULE_REASON_CACHE
    if _MULE_REASON_CACHE is None:
        import pandas as pd
        try:
            df = pd.read_csv(path)
            _MULE_REASON_CACHE = dict(zip(df["account"], df["flag_reason"]))
        except FileNotFoundError:
            _MULE_REASON_CACHE = {}
    return _MULE_REASON_CACHE.get(merchant_id, "low signal")


def predict_transaction(txn: dict) -> dict:
    """
    Runs Member 2's original (mule_score-free) model for the fraud decision,
    and separately attaches mule_score as an informational field. mule_score
    never changes fraud_score or decision here.
    """
    t0 = time.perf_counter()

    result = _predict_core(txn)

    merchant_id = txn.get("merchant_id")
    mule_score = get_mule_score(merchant_id) if merchant_id else 0.0
    mule_reason = _get_mule_reason(merchant_id) if merchant_id else "no merchant_id provided"

    t1 = time.perf_counter()

    result["mule_score"] = float(mule_score)
    result["mule_flag_reason"] = mule_reason
    result["latency_ms"] = round((t1 - t0) * 1000, 4)  # includes both lookups
    return result


if __name__ == "__main__":
    # Same deliberately fraud-looking example as before, addressed to a
    # HIGH mule_score (repeat-business, i.e. "safe" per this dataset)
    # merchant -- fraud_score should now reflect the red flags, unaffected
    # by mule_score.
    example_txn = {
        "amount": 12000.0,
        "session_duration": 90,
        "authentication_attempts": 2,
        "receiver_account_age": 0,
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
        "merchant_id": "da2aec1a-42d5-4b13-bbe7-3a5ce249005b",  # top mule-flagged (high repeat business) merchant
    }
    print(predict_transaction(example_txn))