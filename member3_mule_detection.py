"""
Member 3 -- Mule / Suspicious-Merchant Detection (Graph / Network Angle)
=========================================================================
REDESIGNED for Member 1's real fraud_dataset.csv + Member 2's
predict_wrapper_member1_real.py model (supersedes the earlier version
built against Dhruv's placeholder sender_vpa/receiver_vpa dataset).

WHY THIS NEEDED A REDESIGN, NOT JUST A COLUMN RENAME
-----------------------------------------------------
The real dataset has two structural properties the old script assumed
away:

1. NO RECIPROCAL FLOW. Every edge here is user_id -> merchant_id (a
   payment). Users never receive money back through this data, and
   merchants never send money out. The old script's core mule signals
   -- turnover_ratio (money out / money in) and pass_through_minutes
   (how fast money re-exits a node) -- need money flowing BOTH ways
   through a node. That doesn't exist in a pure P2M dataset, so those
   features would just be constant/undefined here, not meaningfully low.

2. `timestamp` IS BROKEN. It only contains fragments like "18:27.7"
   (minutes:seconds, no date) -- see Dhruv's note in
   train_model_member1_real.py. Any time-window logic (circular chains
   that "close within 6 hours", velocity in minutes) is impossible to
   compute honestly on this field. Don't fake it with row order --
   that's not a time window, that's a coincidence.

WHAT THIS VERSION DOES INSTEAD
-------------------------------
Reframed around what the original brief actually asked for that this
data CAN support: "sudden spike in unique counterparties." Builds a
bipartite user_id <-> merchant_id graph and flags merchant_ids that
look like collection points rather than real repeat-customer merchants:

  - fan_in: how many distinct users have paid this merchant_id
  - sender_concentration: unique_senders / total_txn_count -- close to
    1.0 means almost every transaction is from a NEW sender (no repeat
    customers at all), which is unusual for a legitimate merchant and
    consistent with a one-shot collection account
  - txn_volume: total transactions received (context, not a red flag by
    itself -- a large legitimate merchant naturally has high volume)
  - avg_amount / total_in_amount: for context in the report

This is honestly a "suspicious merchant / collection-point" detector,
not classic personal-account mule-chain detection -- because personal
account-to-account transfers aren't present in this dataset at all.
Flag this distinction to the team explicitly when presenting: it's a
legitimate reframe given the data you actually have, not a downgrade.

Usage:
    python member3_mule_detection.py --input Data/fraud_dataset.csv
"""

import argparse
import os

import networkx as nx
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"user_id", "merchant_id", "amount"}


def load_transactions(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Input CSV missing required columns: {missing}. "
            f"This script needs user_id/merchant_id/amount per transaction."
        )
    return df


def build_graph(df: pd.DataFrame) -> nx.DiGraph:
    """Bipartite-style directed graph: user_id -> merchant_id per transaction."""
    G = nx.MultiDiGraph()
    for _, row in df.iterrows():
        G.add_edge(
            row["user_id"], row["merchant_id"],
            amount=row["amount"],
            txn_id=row.get("transaction_id", None),
        )
    return G


def compute_merchant_features(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("merchant_id").agg(
        txn_count=("user_id", "count"),
        unique_senders=("user_id", "nunique"),
        total_in_amount=("amount", "sum"),
        avg_amount=("amount", "mean"),
    ).reset_index().rename(columns={"merchant_id": "account"})

    grouped["sender_concentration"] = (
        grouped["unique_senders"] / grouped["txn_count"]
    ).round(4)

    if "is_fraud" in df.columns:
        fraud_rate = df.groupby("merchant_id")["is_fraud"].mean()
        grouped["fraud_txn_rate"] = grouped["account"].map(fraud_rate).round(4)

    return grouped


def score_mule_accounts(features: pd.DataFrame) -> pd.DataFrame:
    f = features.copy()

    def norm(col):
        vals = f[col].replace([np.inf, -np.inf], np.nan).fillna(0)
        return (vals - vals.min()) / (vals.max() - vals.min()) if vals.max() != vals.min() else vals * 0

    fan_in_score = norm("unique_senders")
    concentration_score = f["sender_concentration"]  # already 0-1
    volume_score = norm("txn_count")

    # Weighted toward the two signals that actually indicate a one-shot
    # collection point: lots of distinct senders (fan_in) who each only
    # transact once (concentration). Volume alone is NOT weighted heavily
    # -- a big legitimate merchant has high volume too, that's not a red
    # flag by itself, only combined with the other two.
    f["mule_score"] = (
        0.45 * fan_in_score + 0.45 * concentration_score + 0.10 * volume_score
    ).round(4)

    # Meaningful minimum: don't flag merchants with only 1-2 transactions,
    # there's no pattern to detect yet, just noise.
    f.loc[f["txn_count"] < 3, "mule_score"] = 0.0

    f["flag_reason"] = f.apply(_explain_flag, axis=1)
    return f.sort_values("mule_score", ascending=False)


def _explain_flag(row) -> str:
    reasons = []
    if row["unique_senders"] >= 8 and row["sender_concentration"] >= 0.9:
        reasons.append("high fan-in, all one-off senders (collection-point pattern)")
    elif row["sender_concentration"] >= 0.95 and row["txn_count"] >= 5:
        reasons.append("no repeat customers across many transactions")
    elif row["unique_senders"] >= 10:
        reasons.append("unusually broad sender base")
    return ", ".join(reasons) if reasons else "low signal"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="Data/fraud_dataset.csv",
                         help="Path to fraud_dataset.csv (user_id/merchant_id/amount).")
    parser.add_argument("--top_n", type=int, default=25)
    parser.add_argument("--outdir", type=str, default="output")
    args = parser.parse_args()

    df = load_transactions(args.input)
    print(f"[info] Loaded {len(df)} transactions, "
          f"{df['user_id'].nunique()} users, {df['merchant_id'].nunique()} merchants")

    features = compute_merchant_features(df)
    scored = score_mule_accounts(features)

    os.makedirs(args.outdir, exist_ok=True)
    features_path = f"{args.outdir}/account_mule_features.csv"
    flagged_path = f"{args.outdir}/flagged_mule_accounts.csv"

    scored.to_csv(features_path, index=False)
    scored.head(args.top_n).to_csv(flagged_path, index=False)

    print(f"[done] Wrote:\n  {features_path}\n  {flagged_path}")
    print("\nTop 15 suspicious merchant accounts:")
    cols = ["account", "mule_score", "unique_senders", "txn_count",
            "sender_concentration", "flag_reason"]
    print(scored[cols].head(15).to_string(index=False))

    if "fraud_txn_rate" in scored.columns:
        top = scored.head(args.top_n)
        print(f"\n[info] Avg fraud_txn_rate among top {args.top_n} flagged merchants: "
              f"{top['fraud_txn_rate'].mean():.4f} vs dataset-wide average: "
              f"{df['is_fraud'].mean():.4f}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------
# Lookup helper for Member 4 / retraining -- import this directly once
# scoring has run.
# ---------------------------------------------------------------------
_MULE_SCORE_CACHE = None

def get_mule_score(merchant_id: str, path: str = "output/account_mule_features.csv") -> float:
    """
    Member 4: `from member3_mule_detection import get_mule_score` and call
    get_mule_score(txn["merchant_id"]) inside your scoring endpoint.
    Returns 0.0 for any merchant not in the graph (e.g. too few transactions
    to have a meaningful score).
    """
    global _MULE_SCORE_CACHE
    if _MULE_SCORE_CACHE is None:
        try:
            _df = pd.read_csv(path)
            _MULE_SCORE_CACHE = dict(zip(_df["account"], _df["mule_score"]))
        except FileNotFoundError:
            _MULE_SCORE_CACHE = {}
    return _MULE_SCORE_CACHE.get(merchant_id, 0.0)
