"""
train_model_member1_real.py

Trains on Member 1's actual fraud_dataset.csv (65 columns, real user_id
repeating across transactions, rich behavioral/device/security signals).
This REPLACES the earlier synthetic full-dataset model now that real,
usable data with genuine user history is available.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (precision_recall_curve, average_precision_score,
                              classification_report, roc_auc_score)
import pickle

df = pd.read_csv("Data/fraud_dataset.csv")
print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['is_fraud'].mean():.4f}")

# NOTE: the 'timestamp' column is broken in this export (only contains
# fragments like '18:27.7' - minutes:seconds, no date/hour). Flagged to
# Member 1 to re-export properly. Until fixed, we skip anything that
# requires real chronological ordering (time_since_last_txn, timestamp
# sorting) and rely on the already-provided 'transaction_time_of_day'
# column plus rolling_txn_count based on row order instead.

df["rolling_txn_count"] = df.groupby("user_id").cumcount() + 1

df["new_merchant_flag"] = (~df.duplicated(subset=["user_id", "merchant_id"])).astype(int)
df["known_device"] = (~df.duplicated(subset=["user_id", "device_id"])).astype(int)

df["avg_ticket_user"] = df.groupby("user_id")["amount"].transform(
    lambda x: x.expanding().mean().shift(1)
).fillna(df["amount"])

# ---- Select features: numeric/flag columns + engineered ones ----
# Excluding free-text/ID columns that shouldn't go directly into the model
DROP_COLS = [
    "transaction_id", "user_id", "merchant_id", "timestamp", "description",
    "device_id", "ip_address", "location", "request_description",
    "request_description_keywords", "url_referrer", "is_fraud",
    "handle_verification_status"  # perfect 1:1 proxy for is_fraud - data leak, must exclude
]

# One-hot encode remaining low-cardinality categorical columns
categorical_candidates = [c for c in df.columns
                           if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]))
                           and c not in DROP_COLS]
low_card_categoricals = [c for c in categorical_candidates if df[c].nunique() <= 20]

high_card_dropped = [c for c in categorical_candidates if c not in low_card_categoricals]
DROP_COLS = DROP_COLS + high_card_dropped

print(f"\nOne-hot encoding: {low_card_categoricals}")
print(f"Dropping (too high cardinality or free text): {high_card_dropped}")

df_encoded = pd.get_dummies(df, columns=low_card_categoricals)

# XGBoost rejects feature names containing [, ], < — sanitize them
df_encoded.columns = [
    str(c).replace("[", "_").replace("]", "_").replace("<", "_").replace(">", "_").replace(",", "_")
    for c in df_encoded.columns
]

FEATURES = [c for c in df_encoded.columns if c not in DROP_COLS]
TARGET = "is_fraud"

X = df_encoded[FEATURES]
y = df_encoded[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\nTrain size: {len(X_train)}, fraud rate: {y_train.mean():.4f}")
print(f"Test size:  {len(X_test)}, fraud rate: {y_test.mean():.4f}")

neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = neg / pos
print(f"scale_pos_weight: {scale_pos_weight:.2f}")

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

y_proba = model.predict_proba(X_test)[:, 1]
ap = average_precision_score(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)
print(f"\nPR-AUC: {ap:.4f} | ROC-AUC: {auc:.4f}")

precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
target_recall = 0.90
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

print("\nTop 20 feature importances:")
importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])[:20]
for feat, imp in importances:
    print(f"  {feat:45s} {imp:.4f}")

with open("fraud_model_member1_real.pkl", "wb") as f:
    pickle.dump({"model": model, "threshold": float(chosen_threshold), "features": FEATURES}, f)

print("\nSaved model to fraud_model_member1_real.pkl")
