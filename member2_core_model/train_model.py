import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import (precision_recall_curve, average_precision_score,
                              classification_report, roc_auc_score)
import pickle

df = pd.read_csv("data/upi_transactions.csv", parse_dates=["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

FEATURES = [
    "amount", "txn_count_1h", "avg_ticket_sender", "amount_zscore",
    "time_since_last_txn_min", "geo_velocity_kmph", "new_payee_flag",
    "is_odd_hour", "hour"
]
# transaction_type as categorical -> one-hot
df["is_p2m"] = (df["transaction_type"] == "P2M").astype(int)
FEATURES.append("is_p2m")

TARGET = "is_fraud"

# ---- Time-based split (critical for fraud - no random split) ----
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
test_df = df.iloc[split_idx:]

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_test, y_test = test_df[FEATURES], test_df[TARGET]

print(f"Train size: {len(X_train)}, fraud rate: {y_train.mean():.4f}")
print(f"Test size:  {len(X_test)}, fraud rate: {y_test.mean():.4f}")

# ---- Handle class imbalance via scale_pos_weight (not resampling) ----
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

# Find threshold that gives recall >= 0.90 while maximizing precision
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
print("\nClassification report at chosen threshold:")
print(classification_report(y_test, y_pred, digits=3))

# Feature importance
print("\nFeature importances:")
importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])
for feat, imp in importances:
    print(f"  {feat:25s} {imp:.4f}")

# ---- Save model + threshold + feature list ----
with open("fraud_model.pkl", "wb") as f:
    pickle.dump({
        "model": model,
        "threshold": float(chosen_threshold),
        "features": FEATURES
    }, f)

print("\nSaved model to fraud_model.pkl")
