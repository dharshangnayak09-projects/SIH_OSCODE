"""
Member 3 — Mule Account Detection (Graph / Network Angle)
=============================================================
Built against the REAL team schema (matches Dhruv's member2_core_model/data/
upi_transactions.csv: transaction_id, sender_vpa, receiver_vpa, amount,
timestamp, device_id, location, transaction_type, is_fraud, lat, lon).

IMPORTANT — a schema note for the team, not just you:
  Darsh's actual feature_engineering.py pipeline uses `user_id` /
  `merchant_id` with no sender->receiver edge structure, which a graph/mule
  model cannot be built on top of (a graph needs two distinct endpoints per
  transaction). Dhruv's placeholder data already has the right shape
  (sender_vpa, receiver_vpa), so this script uses that as the real input
  for now. Flag to Darsh: his real pipeline needs to output sender_vpa AND
  receiver_vpa (not just user_id/merchant_id) for Member 3's graph work and
  Member 4's velocity engine to plug in later — see the bottom of this file
  for the exact ask.

What this does:
  1. Loads the real transaction data.
  2. Builds a directed graph — but only over P2P edges between user@upi
     accounts. Merchant accounts (merchant_id@upi, P2M transactions) are
     excluded from mule *scoring* — a merchant receiving lots of money and
     never sending any out is completely normal, not a fan-in/fan-out
     pattern, and including them would flood the flagged list with false
     positives. They're irrelevant to this analysis, not a graph edge case.
  3. Computes per-account graph features: fan-in/fan-out, clustering
     coefficient, degree centrality, pass-through velocity, circular chain
     membership (short + time-boxed, see find_short_cycle_members).
  4. Produces mule_score (0-1) + human-readable flag_reason.
  5. Exports account_mule_features.csv (all accounts) and a small
     `get_mule_score(vpa)` lookup Member 4 can import directly.

Usage:
    python member3_mule_detection.py --input data/upi_transactions.csv
"""

import argparse
import os

import networkx as nx
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {"sender_vpa", "receiver_vpa", "amount", "timestamp"}


def load_transactions(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Input CSV missing required columns: {missing}. "
            f"Member 3's graph model needs a sender_vpa/receiver_vpa edge "
            f"per transaction — see the schema note at the top of this file."
        )
    return df


def is_merchant(vpa: str) -> bool:
    return isinstance(vpa, str) and vpa.startswith("merchant")


def build_graph(df: pd.DataFrame) -> nx.MultiDiGraph:
    """
    P2P-only graph: excludes edges where the receiver is a merchant account.
    Merchants are legitimate money sinks (that's their whole job) and would
    otherwise look identical to a mule cash-out account under fan-in/turnover
    scoring — this is a deliberate filter, not an oversight.
    """
    G = nx.MultiDiGraph()
    p2p = df[~df["receiver_vpa"].apply(is_merchant) & ~df["sender_vpa"].apply(is_merchant)]
    for _, row in p2p.iterrows():
        G.add_edge(
            row["sender_vpa"], row["receiver_vpa"],
            amount=row["amount"], timestamp=row["timestamp"],
            txn_id=row.get("transaction_id", None),
        )
    return G


def compute_pass_through_velocity(G: nx.MultiDiGraph, node) -> float:
    """Minutes between the LAST inbound txn and the FIRST outbound txn after it."""
    in_times = [d["timestamp"] for _, _, d in G.in_edges(node, data=True)]
    out_times = [d["timestamp"] for _, _, d in G.out_edges(node, data=True)]
    if not in_times or not out_times:
        return np.inf
    last_in = max(in_times)
    later_outs = [t for t in out_times if t >= last_in]
    if not later_outs:
        return np.inf
    return (min(later_outs) - last_in).total_seconds() / 60.0


def find_short_cycle_members(G: nx.MultiDiGraph, max_len=4, min_len=3,
                              max_window_hours=6) -> set:
    """
    Nodes in short circular chains (A->B->C->A layering).
    min_len=3 excludes ordinary back-and-forth pairs (A pays B, B pays A
    back later — common, not fraud). max_window_hours requires the loop to
    close FAST — real layering moves money round in minutes/hours, not weeks.
    """
    simple_G = nx.DiGraph(G)
    edge_time = {}
    for u, v, d in G.edges(data=True):
        key = (u, v)
        if key not in edge_time or d["timestamp"] < edge_time[key]:
            edge_time[key] = d["timestamp"]

    members = set()
    try:
        cycles = nx.simple_cycles(simple_G, length_bound=max_len)
    except TypeError:
        cycles = [c for c in nx.simple_cycles(simple_G) if len(c) <= max_len]

    for cycle in cycles:
        if len(cycle) < min_len:
            continue
        edge_ts = [edge_time[(cycle[i], cycle[(i + 1) % len(cycle)])]
                   for i in range(len(cycle))
                   if (cycle[i], cycle[(i + 1) % len(cycle)]) in edge_time]
        if not edge_ts:
            continue
        if (max(edge_ts) - min(edge_ts)).total_seconds() / 3600.0 <= max_window_hours:
            members.update(cycle)
    return members


def compute_account_features(G: nx.MultiDiGraph, p2p_df: pd.DataFrame) -> pd.DataFrame:
    undirected = nx.Graph(G)
    clustering = nx.clustering(undirected)
    degree_centrality = nx.degree_centrality(G)
    cycle_members = find_short_cycle_members(G)

    in_amount = p2p_df.groupby("receiver_vpa")["amount"].sum()
    out_amount = p2p_df.groupby("sender_vpa")["amount"].sum()

    raw = []
    for node in G.nodes():
        unique_senders = len(set(u for u, _ in G.in_edges(node)))
        unique_receivers = len(set(v for _, v in G.out_edges(node)))
        total_in = in_amount.get(node, 0.0)
        total_out = out_amount.get(node, 0.0)
        turnover_ratio = (total_out / total_in) if total_in > 0 else 0.0
        pass_through_min = compute_pass_through_velocity(G, node)

        raw.append({
            "account": node,
            "in_degree": G.in_degree(node),
            "out_degree": G.out_degree(node),
            "unique_senders": unique_senders,
            "unique_receivers": unique_receivers,
            "degree_centrality": degree_centrality.get(node, 0.0),
            "clustering_coeff": clustering.get(node, 0.0),
            "total_in_amount": round(total_in, 2),
            "total_out_amount": round(total_out, 2),
            "turnover_ratio": round(turnover_ratio, 4),
            "pass_through_minutes": pass_through_min,
            "in_cycle": node in cycle_members,
        })
    df = pd.DataFrame(raw)

    # IMPORTANT: thresholds are relative to THIS dataset's own density, not
    # fixed numbers. A dense synthetic graph (e.g. 500 accounts over 3 months)
    # can have a much higher "normal" fan-in than a sparse real one — a fixed
    # cutoff like ">= 6 senders" would either flag everyone or no one
    # depending on density. Percentiles keep the flag meaningful either way.
    fan_in_p90 = df["unique_senders"].quantile(0.90)
    fan_out_p25 = df["unique_receivers"].quantile(0.25)

    df["fan_in_fan_out_flag"] = (
        (df["unique_senders"] >= fan_in_p90) &
        (df["unique_receivers"] <= max(fan_out_p25, 2)) &
        (df["pass_through_minutes"] < 120) &
        (df["turnover_ratio"] > 0.85)
    )
    return df


def score_mule_accounts(features: pd.DataFrame) -> pd.DataFrame:
    f = features.copy()

    def norm(col):
        vals = f[col].replace([np.inf, -np.inf], np.nan).fillna(0)
        return (vals - vals.min()) / (vals.max() - vals.min()) if vals.max() != vals.min() else vals * 0

    fan_in_score = norm("unique_senders")
    turnover_score = f["turnover_ratio"].clip(0, 1.5) / 1.5
    velocity_score = (1 - norm("pass_through_minutes")).where(f["pass_through_minutes"] != np.inf, 0)
    clustering_score = norm("clustering_coeff")
    cycle_score = f["in_cycle"].astype(float)
    fan_flag_score = f["fan_in_fan_out_flag"].astype(float)

    f["mule_score"] = (
        0.25 * fan_in_score + 0.20 * turnover_score + 0.20 * velocity_score +
        0.10 * clustering_score + 0.15 * cycle_score + 0.10 * fan_flag_score
    ).round(4)
    f["flag_reason"] = f.apply(_explain_flag, axis=1)
    return f.sort_values("mule_score", ascending=False)


def _explain_flag(row) -> str:
    reasons = []
    if row["fan_in_fan_out_flag"]:
        reasons.append("fan-in/fan-out hub")
    if row["in_cycle"]:
        reasons.append("circular chain")
    if row["turnover_ratio"] > 0.9:
        reasons.append("high pass-through turnover")
    if row["pass_through_minutes"] < 30:
        reasons.append("fast cash-out")
    return ", ".join(reasons) if reasons else "low signal"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, default="data/upi_transactions.csv",
                         help="Path to the transaction CSV (sender_vpa/receiver_vpa/amount/timestamp).")
    parser.add_argument("--top_n", type=int, default=25)
    parser.add_argument("--outdir", type=str, default="output")
    args = parser.parse_args()

    df = load_transactions(args.input)
    p2p_df = df[~df["receiver_vpa"].apply(is_merchant) & ~df["sender_vpa"].apply(is_merchant)]
    print(f"[info] Loaded {len(df)} total transactions ({len(p2p_df)} P2P edges after "
          f"excluding merchant accounts from the mule graph)")

    G = build_graph(df)
    print(f"[info] P2P graph: {G.number_of_nodes()} accounts, {G.number_of_edges()} edges")

    features = compute_account_features(G, p2p_df)
    scored = score_mule_accounts(features)

    os.makedirs(args.outdir, exist_ok=True)
    features_path = f"{args.outdir}/account_mule_features.csv"
    flagged_path = f"{args.outdir}/flagged_mule_accounts.csv"
    graph_path = f"{args.outdir}/transaction_graph.graphml"

    scored.to_csv(features_path, index=False)
    scored.head(args.top_n).to_csv(flagged_path, index=False)

    G_export = nx.DiGraph()
    for u, v, d in G.edges(data=True):
        G_export.add_edge(u, v, amount=float(d["amount"]), timestamp=str(d["timestamp"]))
    nx.write_graphml(G_export, graph_path)

    print(f"[done] Wrote:\n  {features_path}\n  {flagged_path}\n  {graph_path}")
    print("\nTop 15 suspicious accounts:")
    print(scored[["account", "mule_score", "unique_senders", "turnover_ratio", "flag_reason"]]
          .head(15).to_string(index=False))

    # cross-check against is_fraud, purely informational — this dataset's fraud
    # labels are amount-spike-style (see Dhruv's README TODO), not mule rings,
    # so don't expect strong overlap; it's a genuinely different fraud angle.
    if "is_fraud" in df.columns:
        fraud_accounts = set(df.loc[df["is_fraud"] == 1, "sender_vpa"]) | \
                          set(df.loc[df["is_fraud"] == 1, "receiver_vpa"])
        overlap = fraud_accounts & set(scored.head(args.top_n)["account"])
        print(f"\n[info] {len(fraud_accounts)} accounts touch an is_fraud=1 transaction. "
              f"{len(overlap)} of those also appear in your top {args.top_n} mule-flagged accounts. "
              f"Low overlap is expected — this dataset's current fraud is amount-spike-based, "
              f"not mule-ring-based, so the graph angle is catching a different pattern (as intended).")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------
# Lookup helper for Member 4 — import this directly once scoring has run
# ---------------------------------------------------------------------
_MULE_SCORE_CACHE = None

def get_mule_score(vpa: str, path: str = "output/account_mule_features.csv") -> float:
    """
    Member 4: `from member3_mule_detection import get_mule_score` and call
    get_mule_score(txn["sender_vpa"]) inside your scoring endpoint.
    Returns 0.0 for any account not in the P2P graph (e.g. merchants, or
    accounts with too few transactions to have a meaningful score).
    """
    global _MULE_SCORE_CACHE
    if _MULE_SCORE_CACHE is None:
        try:
            _df = pd.read_csv(path)
            _MULE_SCORE_CACHE = dict(zip(_df["account"], _df["mule_score"]))
        except FileNotFoundError:
            _MULE_SCORE_CACHE = {}
    return _MULE_SCORE_CACHE.get(vpa, 0.0)
