# Member 2 — Core ML Fraud Classifier

Owner: Dhruv
Branch: `dhruv-core-model`

## TL;DR
XGBoost fraud classifier trained on Member 1's real transaction dataset (26k rows, genuine per-user history). Cross-validated and regularization-tested to confirm no overfitting. ONNX-exported: **~0.03-0.15ms inference**, **100% recall/precision** at chosen threshold — well under the 50-100ms target.

## Files in this folder
| File | Purpose |
|---|---|
| `train_model_improved.py` | Trains the model with 5-fold CV + hyperparameter search + early stopping |
| `benchmark_latency_improved.py` | Exports to ONNX, benchmarks latency |
| `predict_wrapper_improved.py` | **Member 4 imports `predict_transaction()` from here** |
| `fraud_model_improved.pkl` | Trained model bundle |
| `fraud_model_improved.onnx` | ONNX export used for serving |
| `fix_timestamps.py` | Utility for dashboard demo timestamps (see note below) |
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
python predict_wrapper_improved.py    # quick sanity test
```
Only re-run if regenerating from scratch:
```powershell
python train_model_improved.py         # takes ~1-2 min (runs CV + hyperparameter search)
python benchmark_latency_improved.py
```

---

## Integration guide — for Member 4

### 1. Import and call
```python
from predict_wrapper_improved import predict_transaction

result = predict_transaction(txn)
# {"fraud_score": 0.98, "decision": "FLAG", "threshold_used": 0.975, "latency_ms": 0.05}
```

### 2. What to pass in — the `txn` dict

**Numeric / flag fields:**
```python
{
    "amount": 12000.0,
    "session_duration": 90,
    "authentication_attempts": 2,
    "receiver_account_age": 0,                      # 0 = brand new account, strongest fraud signal
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
    "input_pause_patterns": 0,          # behavioral biometric signal
    "background_data_usage": 0,         # possible screen-mirroring indicator

    # engineered — YOU maintain these per user
    "rolling_txn_count": 3,
    "new_merchant_flag": 1,
    "known_device": 0,
    "avg_ticket_user": 900.0,
}
```

**Categorical fields (raw string values):**
```python
{
    "pin_entry_method": "manual",         # "manual" or "pasted"
    "authorization_method": "pin",         # "otp" or "pin"
    "transaction_type": "payment",         # "payment" or "collection_request"
    "handle_registration_pattern": "none"  # "none" or "recent"
}
```

Anything omitted defaults to 0 (safe/neutral). For best accuracy, prioritize sending `receiver_account_age`, `unusual_ip_flag`, `receiver_transaction_history`, `handle_registration_pattern` — these carry the most weight (see feature importance below).

### 3. What YOU (Member 4) maintain as state
Simple in-memory dict or Redis, keyed by `user_id`:
```python
user_state = {
    "user_123": {
        "rolling_txn_count": 12,
        "known_devices": {"device_abc"},
        "known_merchants": {"merchant_xyz"},
        "amount_history": [500, 620, 480, ...]
    }
}
```

---

## Model performance & rigor

- **PR-AUC: 1.0000 | ROC-AUC: 1.0000** — 100% recall, 100% precision at threshold ~0.975
- **5-fold cross-validation: PR-AUC 1.0000 on every single fold, std = 0.0000** — no variance across folds
- **Train-vs-test gap: 0.0000** across 5 different hyperparameter configurations (varying tree depth, regularization strength) — confirms this is NOT overfitting
- Final model uses early stopping (halted at round 34/100), depth 3, moderate regularization — simplest config that generalizes well
- ONNX Runtime latency: ~0.03-0.15ms mean, ~29x faster than raw XGBoost

## Why scores are this high — read before presenting to judges

We rigorously checked this isn't overfitting (see above) — the near-perfect scores instead reflect that Member 1's dataset was constructed around clear, deterministic fraud archetypes (mule accounts with brand-new receiver accounts, phishing via links, screen-mirroring scams, typo-squatted handles). We also **found and removed one genuine data leak** (`handle_verification_status` was a 1:1 proxy for the label itself) before any of this validation. Be upfront if asked: *"We validated this isn't overfitting through cross-validation and regularization testing. The high accuracy reflects the dataset's clear fraud archetypes rather than a claim about real-world noisy-data performance — but the modeling approach and rigor are sound."*

**Known data issue (flagged to Member 1):** `timestamp` column is truncated/broken (no date, only fragments like "18:27.7"). We use `transaction_time_of_day` instead, which works fine. `fix_timestamps.py` generates cosmetic full datetime values for dashboard demo purposes only.

## Feature importance (top drivers)
| Feature | Importance |
|---|---|
| `receiver_account_age` | 89.6% |
| `input_pause_patterns` | 2.6% |
| `receiver_transaction_history` | 2.5% |
| `handle_registration_pattern` | 2.3% |
| `background_data_usage` | 1.9% |
| `unusual_ip_flag` | 0.7% |

## TODO / known limitations
- [ ] If Member 1 fixes `timestamp`, add real time-since-last-transaction features
- [ ] Member 3's graph/mule features could be added as extra inputs later
- [ ] Consider testing against a more adversarial/noisy dataset if time permits, for a more "real-world" precision/recall story
