"""
Integration Step 1 — merge Member 3's mule_score into Member 2's dataset
==========================================================================
Joins on sender_vpa AND receiver_vpa: a transaction is more suspicious if
EITHER party is a flagged mule-pattern account, so we take the max of the
two. This is the join that turns three separate deliverables into one
feature table Member 2 can retrain on.

Run this AFTER:
  python member3_mule_detection.py --input data/upi_transactions.csv
      (writes output/account_mule_features.csv)

Usage:
    python merge_mule_score.py
"""

import pandas as pd

TXN_PATH = "data/upi_transactions.csv"
MULE_SCORES_PATH = "output/account_mule_features.csv"   # from member3_mule_detection.py
OUTPUT_PATH = "data/upi_transactions_with_mule_score.csv"


def main():
    txns = pd.read_csv(TXN_PATH, parse_dates=["timestamp"])
    mule = pd.read_csv(MULE_SCORES_PATH)
    mule_lookup = dict(zip(mule["account"], mule["mule_score"]))

    txns["sender_mule_score"] = txns["sender_vpa"].map(mule_lookup).fillna(0.0)
    txns["receiver_mule_score"] = txns["receiver_vpa"].map(mule_lookup).fillna(0.0)
    txns["mule_score"] = txns[["sender_mule_score", "receiver_mule_score"]].max(axis=1)
    txns = txns.drop(columns=["sender_mule_score", "receiver_mule_score"])

    txns.to_csv(OUTPUT_PATH, index=False)

    coverage = (txns["mule_score"] > 0).mean()
    print(f"[done] Wrote {OUTPUT_PATH} ({len(txns)} rows)")
    print(f"       {coverage:.1%} of transactions have a non-zero mule_score "
          f"(the rest touch accounts with too little graph activity to score, "
          f"or merchant accounts, which are excluded from mule scoring by design)")
    print(f"       mule_score distribution:\n{txns['mule_score'].describe()}")


if __name__ == "__main__":
    main()
