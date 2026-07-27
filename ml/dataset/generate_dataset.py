import pandas as pd
import numpy as np

np.random.seed(42)

rows = 20000

data = {
    "amount": np.random.randint(10, 100000, rows),
    "rooted": np.random.randint(0, 2, rows),
    "emulator": np.random.randint(0, 2, rows),
    "new_beneficiary": np.random.randint(0, 2, rows),
    "unusual_location": np.random.randint(0, 2, rows),
    "late_night": np.random.randint(0, 2, rows),
    "high_frequency": np.random.randint(0, 2, rows),
    "typing_speed": np.random.normal(70, 15, rows).clip(10, 120),
    "hesitation_time": np.random.uniform(0, 5, rows),
    "cancelled_attempts": np.random.randint(0, 6, rows),
    "rapid_retries": np.random.randint(0, 2, rows)
}

df = pd.DataFrame(data)

score = (
    (df["amount"] > 50000).astype(int) * 2 +
    df["rooted"] * 2 +
    df["emulator"] * 3 +
    df["new_beneficiary"] * 2 +
    df["unusual_location"] * 2 +
    df["late_night"] +
    df["high_frequency"] * 2 +
    (df["typing_speed"] < 35).astype(int) +
    (df["hesitation_time"] > 2).astype(int) +
    (df["cancelled_attempts"] > 2).astype(int) +
    df["rapid_retries"] * 2
)

df["fraud"] = (score >= 8).astype(int)

df.to_csv("dataset/sih_fraud_dataset.csv", index=False)

print(df.head())
print(f"\nGenerated {len(df)} records.")