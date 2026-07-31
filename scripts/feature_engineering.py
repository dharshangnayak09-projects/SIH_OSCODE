import pandas as pd

<<<<<<< HEAD
# -------------------------
# Load Dataset
# -------------------------

=======
# Load dataset
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
df = pd.read_csv("Data/fraud_dataset.csv")

print("Dataset Shape:", df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nFirst 5 Rows:")
print(df.head())

print("\nMissing Values:")
print(df.isnull().sum())
<<<<<<< HEAD

=======
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
# -------------------------
# Data Cleaning
# -------------------------

# Convert timestamp to datetime
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)
<<<<<<< HEAD

# Remove rows with invalid timestamps
df = df.dropna(subset=["timestamp"])

print("\nShape after removing invalid timestamps:", df.shape)
=======
# Remove rows with invalid timestamps

df = df.dropna(subset=["timestamp"])

print("Shape after removing invalid timestamps:", df.shape)
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c

# Remove duplicate rows
df = df.drop_duplicates()

<<<<<<< HEAD
print("Shape after removing duplicates:", df.shape)

=======
print("\nShape after removing duplicates:", df.shape)
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
# -------------------------
# Feature Engineering
# -------------------------

# Sort by user and timestamp
df = df.sort_values(by=["user_id", "timestamp"])

# 1. Average ticket size per user
<<<<<<< HEAD
df["avg_ticket_size"] = (
    df.groupby("user_id")["amount"]
      .transform("mean")
)

# 2. Rolling transaction count
=======
df["avg_ticket_size"] = df.groupby("user_id")["amount"].transform("mean")

# 2. Rolling transaction count (last 5 transactions)
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
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

<<<<<<< HEAD
# 4. New Merchant Flag
=======
# 4. New merchant flag
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
df["new_merchant_flag"] = (
    ~df.duplicated(subset=["user_id", "merchant_id"])
).astype(int)

<<<<<<< HEAD
# 5. Known Device Flag
=======
# 5. Device familiarity
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
df["known_device"] = (
    ~df.duplicated(subset=["user_id", "device_id"])
).astype(int)

<<<<<<< HEAD
print("\nFeature Engineering Completed!")

print(df[[
    "user_id",
    "merchant_id",
=======
print("\nFeature engineering completed!")
print(df[[
    "user_id",
>>>>>>> 6ae70fffeec1e83b3921fe119bb5fb37c570b27c
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
