"""
add_synthetic_sender_id.py

Member 1's real dataset has no sender/user ID, so no behavioral (velocity)
features can be computed. This script assigns a SYNTHETIC sender_id to each
transaction, then builds the same rolling behavioral features used in the
original synthetic-data model (txn_count_1h, avg_ticket_sender, amount_zscore,
time_since_last_txn, geo_velocity placeholder, new_payee_flag).

IMPORTANT CAVEAT (be upfront about this in the pitch):
Since sender_id is randomly assigned here (not the real underlying sender),
these behavioral features are SIMULATED, not real user history. This proves
the pipeline/method works and gives a usable demo, but is not a substitute
for Member 1 adding a genuine sender_id to the dataset. Swap this out the
moment real IDs are available.
"""

import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("data/upi_transactions_2024.csv", parse_dates=["timestamp"])
df = df.rename(columns={"amount (INR)": "amount", "transaction id": "transaction_id"})

# ---- Assign synthetic sender_id ----
# Distribute transactions across N synthetic users, weighted so some users
# transact more than others (more realistic than perfectly uniform).
N_SYNTHETIC_USERS = 5000
user_weights = np.random.dirichlet(np.ones(N_SYNTHETIC_USERS) * 0.5)  # skewed distribution
df["sender_id"] = np.random.choice(
    [f"user_{i}" for i in range(N_SYNTHETIC_USERS)],
    size=len(df),
    p=user_weights
)

# ---- Sort by sender + time (required for correct rolling calculations) ----
df = df.sort_values(by=["sender_id", "timestamp"]).reset_index(drop=True)

# ---- Behavioral features per synthetic sender ----
df["avg_ticket_sender"] = df.groupby("sender_id")["amount"].transform(
    lambda x: x.expanding().mean().shift(1)
)
df["avg_ticket_sender"] = df["avg_ticket_sender"].fillna(df["amount"])

df["amount_std_sender"] = df.groupby("sender_id")["amount"].transform(
    lambda x: x.expanding().std().shift(1)
)
df["amount_std_sender"] = df["amount_std_sender"].fillna(1.0).replace(0, 1.0)

df["amount_zscore"] = (df["amount"] - df["avg_ticket_sender"]) / df["amount_std_sender"]

df["rolling_txn_count"] = df.groupby("sender_id").cumcount() + 1

df["time_since_last_txn_min"] = (
    df.groupby("sender_id")["timestamp"].diff().dt.total_seconds() / 60
)
df["time_since_last_txn_min"] = df["time_since_last_txn_min"].fillna(999.0)

# Rolling 1-hour transaction count (approximation using time_since_last_txn chains)
# For simplicity here: flag if previous txn was within 60 min (proxy for burst activity)
df["recent_burst_flag"] = (df["time_since_last_txn_min"] <= 60).astype(int)

# New payee flag: has this sender paid this receiver_bank+merchant_category combo before
# (closest available proxy for "payee" since there's no receiver_vpa/merchant_id)
df["payee_key"] = df["receiver_bank"].astype(str) + "_" + df["merchant_category"].astype(str)
df["new_payee_flag"] = (
    ~df.duplicated(subset=["sender_id", "payee_key"])
).astype(int)

df["is_odd_hour"] = df["hour_of_day"].isin([23, 0, 1, 2, 3, 4]).astype(int)
df["bank_mismatch"] = (df["sender_bank"] != df["receiver_bank"]).astype(int)
df["is_p2m"] = (df["transaction type"] == "P2M").astype(int)

print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['fraud_flag'].mean():.4f}")
print("\nBehavioral feature averages by fraud label:")
print(df[["amount", "amount_zscore", "rolling_txn_count", "time_since_last_txn_min",
           "new_payee_flag", "recent_burst_flag", "is_odd_hour"]].groupby(df["fraud_flag"]).mean())

df.to_csv("data/upi_transactions_2024_with_sender.csv", index=False)
print("\nSaved to data/upi_transactions_2024_with_sender.csv")
