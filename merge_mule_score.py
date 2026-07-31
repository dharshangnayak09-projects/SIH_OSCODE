"""
merge_mule_score.py -- joins merchant-level mule_score onto every transaction
in fraud_dataset.csv, keyed by merchant_id (member3_mule_detection.py must
have already been run, producing output/account_mule_features.csv).

Produces Data/fraud_dataset_with_mule_score.csv for
train_model_member1_real.py (v2) to train on.
"""

import pandas as pd

TXN_PATH = "Data/fraud_dataset.csv"
MULE_SCORE_PATH = "output/account_mule_features.csv"
OUT_PATH = "Data/fraud_dataset_with_mule_score.csv"

df = pd.read_csv(TXN_PATH)
mule = pd.read_csv(MULE_SCORE_PATH)[["account", "mule_score"]].rename(
    columns={"account": "merchant_id"}
)

merged = df.merge(mule, on="merchant_id", how="left")
merged["mule_score"] = merged["mule_score"].fillna(0.0)

merged.to_csv(OUT_PATH, index=False)

pct_nonzero = (merged["mule_score"] > 0).mean() * 100
print(f"[done] Wrote {OUT_PATH} ({len(merged)} rows)")
print(f"       {pct_nonzero:.1f}% of transactions got a non-zero mule_score "
      f"(the rest touch merchants with <3 transactions -- too little "
      f"history to score)")
print(merged["mule_score"].describe())
