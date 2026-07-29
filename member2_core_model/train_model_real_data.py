"""
train_model_real_data.py — trains on Member 1's real upi_transactions_2024.csv

NOTE: This dataset has NO sender/user ID column, only category buckets
(age_group, state, bank, etc). So behavioral/velocity features from the
synthetic version (txn_count_1h, avg_ticket_sender, geo_velocity, etc.)
CANNOT be computed here. This script uses transaction-level + categorical
signals instead. If Member 1 adds a sender_id column later, re-add the
velocity features from the original train_model.py.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (precision_recall_curve, average_precision_score,
                              classification_report, roc_auc_score)
import pickle

# ---- Load ----
df = pd.read_csv("data/upi_transactions_2024.csv", parse_dates=["timestamp"])
df = df.rename(columns={"amount (INR)": "amount", "transaction id": "transaction_id"})

print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['fraud_flag'].mean():.4f}")

# ---- Feature engineering (adapted — no sender_id available) ----
# Amount relative to its merchant category's typical range (proxy for "unusual for this context")
df["category_avg_amount"] = df.groupby("merchant_category")["amount"].transform("mean")
df["category_std_amount"] = df.groupby("merchant_category")["amount"].transform("std")
df["amount_zscore_category"] = (
    (df["amount"] - df["category_avg_amount"]) / df["category_std_amount"].replace(0, 1)
)

df["is_odd_hour"] = df["hour_of_day"].isin([23, 0, 1, 2, 3, 4]).astype(int)
df["bank_mismatch"] = (df["sender_bank"] != df["receiver_bank"]).astype(int)
df["is_p2m"] = (df["transaction type"] == "P2M").astype(int)
df["txn_failed"] = (df["transaction_status"] != df["transaction_status"].mode()[0]).astype(int)

# One-hot encode LOW-cardinality categoricals only (all safe here, max 10 uniques)
categorical_cols = ["merchant_category", "sender_age_group", "receiver_age_group",
                     "sender_state", "device_type", "network_type"]
df_encoded = pd.get_dummies(df, columns=categorical_cols, prefix=categorical_cols)

FEATURES = [
    "amount", "amount_zscore_category", "is_odd_hour", "is_weekend",
    "bank_mismatch", "is_p2m", "txn_failed", "hour_of_day"
] + [c for c in df_encoded.columns if any(c.startswith(p + "_") for p in categorical_cols)]

TARGET = "fraud_flag"

X = df_encoded[FEATURES]
y = df_encoded[TARGET]

# ---- Split FIRST, then would apply any resampling only to train (not needed here, using scale_pos_weight instead) ----
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain size: {len(X_train)}, fraud rate: {y_train.mean():.4f}")
print(f"Test size:  {len(X_test)}, fraud rate: {y_test.mean():.4f}")

neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = neg / pos
print(f"scale_pos_weight: {scale_pos_weight:.1f}")

model = xgb.XGBClassifier(
    n_estimators=150,
    max_depth=5,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    eval_metric="aucpr",
    tree_method="hist",
    random_state=42
)

model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

# ---- Evaluate ----
y_proba = model.predict_proba(X_test)[:, 1]
ap = average_precision_score(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)
print(f"\nPR-AUC: {ap:.4f} | ROC-AUC: {auc:.4f}")

precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
target_recall = 0.80  # lower bar than synthetic data since real fraud is harder to catch
valid_idx = np.where(recall[:-1] >= target_recall)[0]
if len(valid_idx) > 0:
    best_idx = valid_idx[np.argmax(precision[valid_idx])]
    chosen_threshold = thresholds[best_idx]
    print(f"\nChosen threshold: {chosen_threshold:.4f}")
    print(f"  -> Recall: {recall[best_idx]:.3f}, Precision: {precision[best_idx]:.3f}")
else:
    chosen_threshold = 0.5
    print("Could not hit target recall, using default threshold 0.5")

y_pred = (y_proba >= chosen_threshold).astype(int)
print("\nClassification report:")
print(classification_report(y_test, y_pred, digits=3))

print("\nTop 15 feature importances:")
importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])[:15]
for feat, imp in importances:
    print(f"  {feat:35s} {imp:.4f}")

with open("fraud_model_real.pkl", "wb") as f:
    pickle.dump({"model": model, "threshold": float(chosen_threshold), "features": FEATURES}, f)

print("\nSaved model to fraud_model_real.pkl")
