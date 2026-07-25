import pandas as pd

# Load dataset
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

print("Shape after removing invalid timestamps:", df.shape)

# Remove duplicate rows
df = df.drop_duplicates()

print("\nShape after removing duplicates:", df.shape)
# -------------------------
# Feature Engineering
# -------------------------

# Sort by user and timestamp
df = df.sort_values(by=["user_id", "timestamp"])

# 1. Average ticket size per user
df["avg_ticket_size"] = df.groupby("user_id")["amount"].transform("mean")

# 2. Rolling transaction count (last 5 transactions)
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

# 4. New merchant flag
df["new_merchant_flag"] = (
    ~df.duplicated(subset=["user_id", "merchant_id"])
).astype(int)

# 5. Device familiarity
df["known_device"] = (
    ~df.duplicated(subset=["user_id", "device_id"])
).astype(int)

print("\nFeature engineering completed!")
print(df[[
    "user_id",
    "amount",
    "avg_ticket_size",
    "rolling_txn_count",
    "time_since_last_txn",
    "new_merchant_flag",
    "known_device"
]].head(10))
# -------------------------
# Handle Class Imbalance
# -------------------------

from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE

# Remove columns that should not be used for training
X = df.drop(columns=[
    "transaction_id",
    "timestamp",
    "is_fraud"
])

# Convert categorical columns to numbers
X = pd.get_dummies(X)

# Target column
y = df["is_fraud"]

print("\nFraud Distribution Before SMOTE:")
print(y.value_counts())

# Apply SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X, y)

print("\nFraud Distribution After SMOTE:")
print(pd.Series(y_resampled).value_counts())

# -------------------------
# Train/Test Split
# -------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X_resampled,
    y_resampled,
    test_size=0.2,
    random_state=42,
    stratify=y_resampled
)

print("\nTrain Shape:", X_train.shape)
print("Test Shape:", X_test.shape)

train_data = X_train.copy()
train_data["is_fraud"] = y_train

test_data = X_test.copy()
test_data["is_fraud"] = y_test

train_data.to_csv("Data/train_data.csv", index=False)
test_data.to_csv("Data/test_data.csv", index=False)

print("\nTrain and test datasets saved successfully!")

# Save processed train and test datasets
train_data = X_train.copy()
train_data["is_fraud"] = y_train.values

test_data = X_test.copy()
test_data["is_fraud"] = y_test.values

train_data.to_csv("Data/train_data.csv", index=False)
test_data.to_csv("Data/test_data.csv", index=False)

print("\nProcessed train_data.csv and test_data.csv saved successfully!")