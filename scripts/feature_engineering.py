import pandas as pd

# -------------------------
# Load Dataset
# -------------------------

df = pd.read_csv("Data/fraud_dataset.csv")

print("Dataset Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 Rows:")
print(df.head())

print("\nMissing Values:")
print(df.isnull().sum())

# -------------------------
# Data Cleaning
# -------------------------

# Convert timestamp to datetime
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

# Remove rows with invalid timestamps
df = df.dropna(subset=["timestamp"])

print("\nShape after removing invalid timestamps:", df.shape)

# Remove duplicate rows
df = df.drop_duplicates()

print("Shape after removing duplicates:", df.shape)

# -------------------------
# Feature Engineering
# -------------------------

# Sort by user and timestamp
df = df.sort_values(by=["user_id", "timestamp"])

# 1. Average ticket size per user
df["avg_ticket_size"] = (
    df.groupby("user_id")["amount"]
      .transform("mean")
)

# 2. Rolling transaction count
df["rolling_txn_count"] = (
    df.groupby("user_id")
      .cumcount() + 1
)

# 3. Time since previous transaction (seconds)
df["time_since_last_txn"] = (
    df.groupby("user_id")["timestamp"]
      .diff()
      .dt.total_seconds()
)

# Fill first transaction with 0
df["time_since_last_txn"] = df["time_since_last_txn"].fillna(0)

# 4. New Merchant Flag
df["new_merchant_flag"] = (
    ~df.duplicated(subset=["user_id", "merchant_id"])
).astype(int)

# 5. Known Device Flag
df["known_device"] = (
    ~df.duplicated(subset=["user_id", "device_id"])
).astype(int)

print("\nFeature Engineering Completed!")

print(df[[
    "user_id",
    "merchant_id",
    "amount",
    "avg_ticket_size",
    "rolling_txn_count",
    "time_since_last_txn",
    "new_merchant_flag",
    "known_device"
]].head(10))

# -------------------------
# Save Engineered Dataset
# -------------------------

df.to_csv("Data/engineered_dataset.csv", index=False)

print("\nEngineered dataset saved successfully!")
print("Saved as: Data/engineered_dataset.csv")