# Member 2 — Core ML Fraud Classifier

## What's in here
- `data/upi_transactions.csv` — synthetic UPI dataset with engineered features (placeholder until Member 1's real pipeline is ready)
- `train_model.py` — trains XGBoost classifier with time-based split + class weighting, saves `fraud_model.pkl`
- `benchmark_latency.py` — converts model to ONNX, benchmarks single-row inference latency (raw vs ONNX)
- `fraud_model.pkl` — trained model bundle (model + threshold + feature list)
- `fraud_model.onnx` — ONNX export for low-latency serving (hand this to Member 4)

## Setup (local, in VS Code)
```bash
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python train_model.py           # trains model, prints PR-AUC/recall/precision, saves fraud_model.pkl
python benchmark_latency.py     # exports ONNX, benchmarks latency, saves fraud_model.onnx
```

## Current results (on synthetic data — will change once Member 1's real dataset lands)
- PR-AUC: 0.999 (too high — synthetic fraud is too obviously separable, expect this to drop with real data)
- Raw XGBoost latency: ~0.4ms mean, ~0.7ms p99
- ONNX Runtime latency: ~0.014ms mean, ~0.04ms p99 (~30x speedup)
- Both comfortably under the 50-100ms target

## TODO
- [ ] Swap in Member 1's real feature pipeline once ready (see feature list below)
- [ ] Build `predict()` wrapper function for Member 4's API integration
- [ ] Re-tune threshold once real data changes the precision/recall tradeoff
- [ ] Ask Member 1 to inject subtler fraud patterns (not just huge amount spikes) so model learns more than one rule

## Feature schema (contract with Member 1)
| Feature | Description |
|---|---|
| `amount` | Transaction amount |
| `txn_count_1h` | Sender's transaction count in trailing 1 hour |
| `avg_ticket_sender` | Sender's historical average transaction amount |
| `amount_zscore` | (amount - sender's avg) / sender's std dev |
| `time_since_last_txn_min` | Minutes since sender's previous transaction |
| `geo_velocity_kmph` | Distance from last known location / time elapsed |
| `new_payee_flag` | 1 if sender has never paid this receiver before |
| `is_odd_hour` | 1 if transaction hour is in {23,0,1,2,3,4} |
| `hour` | Hour of day (0-23) |
| `is_p2m` | 1 if transaction type is P2M (merchant), 0 if P2P |
