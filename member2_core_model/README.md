# Member 2 — Core ML Fraud Classifier

Owner: Dhruv
Branch: `dhruv-core-model`

## TL;DR
XGBoost fraud classifier trained on Member 1's real transaction dataset (26k rows, genuine per-user history). ONNX-exported for low-latency serving: **~0.05-0.3ms inference**, **100% recall/precision** at the chosen threshold — well under the 50-100ms target.

## Files in this folder
| File | Purpose |
|---|---|
| `train_model_member1_real.py` | Trains the XGBoost model on `data/fraud_dataset.csv` |
| `benchmark_latency_member1_real.py` | Exports the model to ONNX, benchmarks inference latency |
| `predict_wrapper_member1_real.py` | **Member 4 imports `predict_transaction()` from here** |
| `fraud_model_member1_real.pkl` | Trained model bundle (model + threshold + feature list) |
| `fraud_model_member1_real.onnx` | ONNX export used for serving |
| `fix_timestamps.py` | Utility — adds usable dates/times for dashboard demo purposes (see note below) |
| `data/fraud_dataset.csv` | Member 1's real dataset (26,393 transactions, genuine user_id) |

## Setup
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Running things
You do NOT need to retrain — the model is already trained and committed.
```powershell
python predict_wrapper_member1_real.py    # quick sanity test, prints example predictions
```
Only re-run these if regenerating the model from scratch:
```powershell
python train_model_member1_real.py
python benchmark_latency_member1_real.py
```

---

## Integration guide — for Member 4

### 1. Import and call
```python
from predict_wrapper_member1_real import predict_transaction

result = predict_transaction(txn)
# {"fraud_score": 0.98, "decision": "FLAG", "threshold_used": 0.999, "latency_ms": 0.05}
```

That's it — one function, one dict in, one dict out. No separate history/state object needed (unlike earlier versions of this model) — all behavioral signal is already baked into the fields you pass in per-transaction.

### 2. What to pass in — the `txn` dict

**Numeric / flag fields** (pass the raw values as-is):
```python
{
    "amount": 12000.0,
    "session_duration": 90,                        # seconds
    "authentication_attempts": 2,
    "receiver_account_age": 0,                      # days old — 0 = brand new account (major red flag)
    "receiver_transaction_history": 2,              # how many past transactions receiver has
    "transaction_amount_vs_sender_history": 8.0,    # ratio vs sender's typical amount
    "geographic_disparity": 15000,
    "transaction_time_of_day": 2,                   # hour, 0-23
    "unusual_device_flag": 1,                       # 0 or 1
    "unusual_ip_flag": 1,
    "unusual_location_flag": 1,
    "unusual_transaction_amount_flag": 1,
    "transaction_velocity": 1,
    "failed_transaction_count": 1,

    # engineered fields — YOU maintain these per user (simple dict/cache is fine)
    "rolling_txn_count": 3,        # this user's total txn count so far
    "new_merchant_flag": 1,        # 1 if user has never paid this merchant before
    "known_device": 0,             # 1 if this device_id has been used by this user before
    "avg_ticket_user": 900.0,      # this user's historical average amount
}
```

**Categorical fields** (pass the raw string value — the wrapper handles encoding internally):
```python
{
    "pin_entry_method": "manual",        # "manual" or "pasted"
    "authorization_method": "pin",        # "otp" or "pin"
    "transaction_type": "payment",        # "payment" or "collection_request"
    "handle_registration_pattern": "none" # "none" or "recent"
}
```

You don't need to send every single field — anything omitted defaults to 0, which is a safe/neutral default for flags. But for best accuracy, send as many as you can, especially `receiver_account_age`, `unusual_*_flag` fields, and `handle_registration_pattern` — these carry the most signal (see feature importance below).

### 3. What YOU (Member 4) need to maintain as state
Since this model needs a few per-user rolling values, keep a simple in-memory dict (or Redis) keyed by `user_id`:
```python
user_state = {
    "user_123": {
        "rolling_txn_count": 12,
        "known_devices": {"device_abc"},
        "known_merchants": {"merchant_xyz"},
        "amount_history": [500, 620, 480, ...]  # to compute avg_ticket_user
    }
}
```
Update this after every transaction (increment count, add device/merchant to seen sets, append amount).

---

## Model performance
- PR-AUC: 1.0000 | ROC-AUC: 1.0000
- At chosen threshold (~0.999): 100% recall, 100% precision (on this dataset — see caveat below)
- Raw XGBoost latency: ~0.3-2.7ms mean (varies with system load)
- ONNX Runtime latency: ~0.01-0.05ms mean, ~0.03-0.07ms p99 (24-54x faster than raw)

## Important context — read before presenting to judges

**This dataset gives near-perfect scores because it's a clean, rule-based synthetic dataset, not noisy real-world data.** We found and removed one hard data leak (`handle_verification_status` was a 1:1 proxy for the fraud label) before training. The remaining strong signal — especially `receiver_account_age` — is legitimate (verified: 300 genuine non-fraud transactions also have age=0, so it's a strong tendency, not a hard rule), but real production fraud rates and precision will be lower than this. Be upfront about this if asked: *"High accuracy here reflects a well-structured dataset with clear fraud archetypes (mule accounts, phishing, screen-mirroring scams) built in, not a claim about real-world performance."*

**Known data issue (flagged to Member 1, not fixed at the source):** the dataset's `timestamp` column is broken/truncated (only contains fragments like "18:27.7", no date). We use the separate `transaction_time_of_day` column instead, which works fine. `fix_timestamps.py` generates cosmetic full datetime values for dashboard/demo purposes only — not real recovered timestamps.

## Feature importance (top drivers)
| Feature | Importance | What it means |
|---|---|---|
| `receiver_account_age` | 93.9% | Brand-new receiver accounts are overwhelmingly fraud |
| `unusual_ip_flag` | 2.6% | Pre-flagged anomalous IP |
| `receiver_transaction_history` | 1.8% | Receivers with little/no history are riskier |
| `handle_registration_pattern` | 1.0% | Recently-registered UPI handles are riskier |

## TODO / known limitations
- [ ] If Member 1 fixes the `timestamp` column, could add real time-since-last-transaction features
- [ ] Member 3's graph/mule features could be added as extra inputs later if time allows
- [ ] Consider testing with a slightly less clean/more adversarial dataset if time permits, to get a more "realistic" (less perfect) precision/recall story for the pitch