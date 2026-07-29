"""
generate_full_dataset.py

Builds a UPI transaction dataset that combines:
- Member 1's realistic column schema (banks, states, age groups, merchant categories)
- A GENUINE sender_id with repeated transactions per sender (so behavioral
  features actually work, unlike the real dataset which had no such linkage)
- Fraud patterns deliberately tied to behavioral deviation (burst activity,
  amount spikes vs personal average, new payee, odd hours) — so the fraud
  label is actually learnable from behavior, which is the whole point.

This is meant to stand in for Member 1's dataset until they can produce a
genuine one from real backend logs. Every column name matches their schema
style so downstream code doesn't need to change column names later.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N_USERS = 3000
N_TXNS = 250000          # match Member 1's real dataset size
FRAUD_RATE = 0.006        # ~0.6%, between synthetic (0.8%) and real (0.19%) — realistic middle ground

MERCHANT_CATEGORIES = ["Grocery", "Food", "Fuel", "Shopping", "Entertainment",
                        "Healthcare", "Utilities", "Education", "Transport", "Other"]
BANKS = ["SBI", "HDFC", "ICICI", "Axis", "Kotak", "PNB", "Yes Bank", "IndusInd"]
STATES = ["Maharashtra", "Delhi", "Karnataka", "Telangana", "Tamil Nadu",
          "West Bengal", "Uttar Pradesh", "Gujarat", "Rajasthan", "Andhra Pradesh"]
AGE_GROUPS = ["18-25", "26-35", "36-45", "46-55", "56+"]
DEVICE_TYPES = ["Android", "iOS", "Web"]
NETWORK_TYPES = ["4G", "5G", "WiFi", "3G"]
TXN_TYPES = ["P2P", "P2M", "Bill Payment", "Recharge"]

# ---- Build user profiles (real behavioral anchors per user) ----
users = [f"user_{i}" for i in range(N_USERS)]
user_profile = {}
for u in users:
    user_profile[u] = {
        "age_group": random.choice(AGE_GROUPS),
        "state": random.choice(STATES),
        "bank": random.choice(BANKS),
        "avg_amount": np.random.gamma(3, 300),
        "known_payees": set(),
        "txn_count": 0
    }

start_time = datetime(2024, 1, 1)
rows = []

for i in range(N_TXNS):
    sender = random.choice(users)
    profile = user_profile[sender]

    is_fraud = np.random.rand() < FRAUD_RATE

    txn_type = random.choices(TXN_TYPES, weights=[0.45, 0.35, 0.12, 0.08])[0]
    receiver_bank = random.choice(BANKS)
    merchant_category = random.choice(MERCHANT_CATEGORIES)

    # payee key: what "new payee" is checked against (bank+category combo, closest
    # available proxy without a real receiver_vpa/merchant_id column)
    payee_key = f"{receiver_bank}_{merchant_category}"

    timestamp = start_time + timedelta(seconds=random.randint(0, 60*60*24*300))

    if is_fraud:
        amount = profile["avg_amount"] * np.random.uniform(3, 12)
        # odd hour is now a TENDENCY (70% chance), not guaranteed
        if np.random.rand() < 0.7:
            hour = random.choice([0, 1, 2, 3, 4, 23])
        else:
            hour = random.randint(0, 23)
        timestamp = timestamp.replace(hour=hour)
        # new payee is a tendency (80% chance), not guaranteed
        if np.random.rand() < 0.8:
            payee_key = f"NEWPAYEE_{i}"
        device_type = random.choice(["Web", "Android", "iOS"])
        status = "SUCCESS"
    else:
        amount = max(10, np.random.normal(profile["avg_amount"], profile["avg_amount"] * 0.3))
        # occasionally normal users transact at odd hours too (10% chance)
        if np.random.rand() < 0.10:
            hour = random.choice([0, 1, 2, 3, 4, 23])
        else:
            hour = random.randint(6, 22)
        timestamp = timestamp.replace(hour=hour)
        device_type = random.choice(DEVICE_TYPES)
        status = random.choices(["SUCCESS", "FAILED"], weights=[0.95, 0.05])[0]

    profile["txn_count"] += 1

    rows.append({
        "transaction_id": f"TXN{i:010d}",
        "timestamp": timestamp,
        "sender_id": sender,
        "transaction_type": txn_type,
        "merchant_category": merchant_category,
        "amount": round(amount, 2),
        "transaction_status": status,
        "sender_age_group": profile["age_group"],
        "receiver_age_group": random.choice(AGE_GROUPS),
        "sender_state": profile["state"],
        "sender_bank": profile["bank"],
        "receiver_bank": receiver_bank,
        "device_type": device_type,
        "network_type": random.choice(NETWORK_TYPES),
        "payee_key": payee_key,
        "fraud_flag": int(is_fraud),
        "hour_of_day": hour,
        "day_of_week": timestamp.strftime("%A"),
        "is_weekend": int(timestamp.weekday() >= 5)
    })

df = pd.DataFrame(rows).sort_values(["sender_id", "timestamp"]).reset_index(drop=True)

# ---- Behavioral features computed causally (only using past data per sender) ----
df["avg_ticket_sender"] = df.groupby("sender_id")["amount"].transform(
    lambda x: x.expanding().mean().shift(1)
).fillna(df["amount"])

df["amount_std_sender"] = df.groupby("sender_id")["amount"].transform(
    lambda x: x.expanding().std().shift(1)
).fillna(1.0).replace(0, 1.0)

df["amount_zscore"] = (df["amount"] - df["avg_ticket_sender"]) / df["amount_std_sender"]

df["rolling_txn_count"] = df.groupby("sender_id").cumcount() + 1

df["time_since_last_txn_min"] = (
    df.groupby("sender_id")["timestamp"].diff().dt.total_seconds() / 60
).fillna(999.0)

df["new_payee_flag"] = (~df.duplicated(subset=["sender_id", "payee_key"])).astype(int)
df["is_odd_hour"] = df["hour_of_day"].isin([23, 0, 1, 2, 3, 4]).astype(int)
df["bank_mismatch"] = (df["sender_bank"] != df["receiver_bank"]).astype(int)
df["is_p2m"] = (df["transaction_type"] == "P2M").astype(int)

df = df.drop(columns=["payee_key"])
df = df.sort_values("timestamp").reset_index(drop=True)  # final chronological order

print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['fraud_flag'].mean():.4f}")
print("\nBehavioral feature averages by fraud label (should now show real separation):")
print(df[["amount", "amount_zscore", "time_since_last_txn_min",
           "new_payee_flag", "is_odd_hour"]].groupby(df["fraud_flag"]).mean())

df.to_csv("data/upi_transactions_full.csv", index=False)
print("\nSaved to data/upi_transactions_full.csv")
