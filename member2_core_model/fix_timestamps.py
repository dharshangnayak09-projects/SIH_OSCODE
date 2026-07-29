"""
fix_timestamps.py

Member 1's fraud_dataset.csv has a broken 'timestamp' column (only contains
fragments like '18:27.7' - minutes:seconds, no date/hour). Since the dataset
already has a working 'transaction_time_of_day' column (0-23), we don't lose
real fraud signal by ignoring the broken timestamp for modeling purposes.

This script just adds a NEW, realistic full datetime column for DEMO/DASHBOARD
purposes (e.g. showing a live transaction feed with sensible dates/times) -
it does not attempt to recover the real original timestamps, since that's
not possible from truncated data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

df = pd.read_csv("Data/fraud_dataset.csv")

# Spread transactions across a 90-day window, respecting the existing
# transaction_time_of_day column so hour-of-day stays consistent with
# whatever signal that column already carries.
start_date = datetime(2024, 1, 1)
random_days = np.random.randint(0, 90, size=len(df))
random_minutes = np.random.randint(0, 60, size=len(df))
random_seconds = np.random.randint(0, 60, size=len(df))

df["timestamp_fixed"] = [
    start_date + timedelta(days=int(d), hours=int(h), minutes=int(m), seconds=int(s))
    for d, h, m, s in zip(random_days, df["transaction_time_of_day"], random_minutes, random_seconds)
]

df.to_csv("Data/fraud_dataset_fixed_timestamp.csv", index=False)
print(f"Saved {len(df)} rows with fixed timestamps to Data/fraud_dataset_fixed_timestamp.csv")
print(df[["transaction_time_of_day", "timestamp_fixed"]].head())
