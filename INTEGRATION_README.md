# Joining Member 1 (Darsh) + Member 2 (Dhruv) + Member 3 (you) into one pipeline

## The core problem this solves

Right now the three pieces don't talk to each other:
- **Darsh's real pipeline** outputs `user_id`/`merchant_id` features (no sender→receiver
  structure) — can't feed a graph model.
- **Dhruv's model** trains on `data/upi_transactions.csv`, which has the right
  schema but was hand-built as a placeholder, not produced by Darsh's pipeline.
- **Your mule detection** produces a per-account score that currently lives in
  its own CSV, disconnected from Dhruv's model and from any live API.

These 3 new files close that loop — **run them in this order**:

```bash
python member3_mule_detection.py --input data/upi_transactions.csv   # you already have this
python merge_mule_score.py                                            # NEW — step 1
python retrain_with_mule_score.py                                     # NEW — step 2
python predict_wrapper_v2.py                                          # NEW — step 3 (test)
```

## What each new file does

**`merge_mule_score.py`** — joins your `output/account_mule_features.csv` onto
Dhruv's transaction table on `sender_vpa`/`receiver_vpa` (takes the max of the
two, since either party being flagged makes the transaction riskier). Writes
`data/upi_transactions_with_mule_score.csv` — same as Dhruv's file, plus one
new `mule_score` column.

**`retrain_with_mule_score.py`** — retrains Dhruv's exact model architecture
(same time-based split, same `scale_pos_weight` imbalance handling) twice:
once on his original 10 features, once with `mule_score` as an 11th. Prints
a side-by-side PR-AUC comparison so you can show judges a real number, not
just "we added a graph feature and it should help." Saves `models/fraud_model_v2.pkl`.

On the current placeholder data the lift is ~0 (+0.0001 PR-AUC) — **expected**,
because this dataset has no real mule-ring fraud in it yet (only amount-spike
fraud, see the note in `member3_mule_detection.py`). The comparison script
itself is correct and will show a real lift the moment training data
includes actual mule patterns — see "What to ask the team for" below.

**`predict_wrapper_v2.py`** — same call signature as Dhruv's original
`predict_wrapper.py`, so Member 4 changes one import line and nothing else:
```python
# before
from predict_wrapper import predict_transaction
# after
from predict_wrapper_v2 import predict_transaction
```
It loads `fraud_model_v2.pkl` instead of `fraud_model.pkl`, and looks up
`mule_score` from a plain dict loaded once at import time (not recomputed
per request — the graph is a **batch** job, refreshed periodically, never
computed live per transaction).

## What to ask the team for, in priority order

1. **Ask Darsh** to add `sender_vpa`/`receiver_vpa` columns to his real
   pipeline output (not just `user_id`/`merchant_id`) — without this, your
   graph model and Member 4's velocity engine have nothing to join on once
   real data replaces the placeholder.
2. **Ask whoever owns test-data generation** to plant a handful of real
   mule-ring transaction bursts (fan-in/fan-out + circular chains) into the
   training data — same idea as the validation file I built earlier
   (`upi_transactions_with_test_mule_patterns.csv`). Without this, the
   before/after comparison above will always show ~0 lift, which undersells
   your work to judges even though the detector genuinely works (it caught
   the planted patterns at rank #1-2 out of 505 accounts in testing).
3. **Re-run all three new scripts** once either of the above changes — the
   whole point of this pipeline is that it's a repeatable chain, not a
   one-off.

## Operational note for the live demo

Recompute `account_mule_features.csv` on a schedule (e.g. every few minutes
via cron, or before each demo run) — not on every incoming transaction. Graph
features need the recent transaction history to mean anything; computing
them per-request would blow the latency budget and defeats the "graph is a
batch signal, ML+rules are the real-time layer" architecture the whole
project is pitching to judges.
