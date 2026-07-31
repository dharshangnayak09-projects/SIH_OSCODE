"""
retrain_with_mule_score.py (v2 -- fixes a data leak found in the first run)

WHAT WAS WRONG WITH THE FIRST RUN
-----------------------------------
It scored PR-AUC / ROC-AUC = 1.0000 with mule_score carrying 97% of feature
importance. That is NOT a good result -- it's a leak. Verified directly:
100% of merchants with more than one transaction in fraud_dataset.csv have
a perfectly pure is_fraud label (every transaction to a given merchant is
either ALL fraud or ALL legitimate, never mixed). Since the original script
split transactions randomly BY ROW, the same merchant's transactions ended
up in both train and test. mule_score is a merchant-identity statistic, so
the model wasn't learning a fraud pattern -- it was memorizing "I've seen
this exact merchant_id's mule_score before and I know its label."

THE FIX
--------
Split train/test BY MERCHANT (GroupShuffleSplit), so no merchant's
transactions appear in both sets. This is the only way to honestly measure
whether mule_score (or any merchant-level feature) generalizes to merchants
the model has never seen -- which is the real question for production, since
in the real world you'll be scoring transactions to NEW merchants constantly.

ALSO FIXED: the ONNX conversion error from the first run
(`RuntimeError: Unable to interpret 'mule_score', feature names should
follow pattern 'f%d'`). onnxmltools' xgboost converter needs the booster's
internal feature names to be the default f0/f1/f2... pattern. Passing a
pandas DataFrame with real column names to model.fit() makes xgboost store
those names on the booster instead, which the converter chokes on. Fixed
by fitting on a plain numpy array (.values) instead of the DataFrame
directly -- FEATURES still tracks the real column order for prediction time.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import (precision_recall_curve, average_precision_score,
                              classification_report, roc_auc_score)
import pickle

df = pd.read_csv("Data/fraud_dataset_with_mule_score.csv")
print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['is_fraud'].mean():.4f}")

df["rolling_txn_count"] = df.groupby("user_id").cumcount() + 1
df["new_merchant_flag"] = (~df.duplicated(subset=["user_id", "merchant_id"])).astype(int)
df["known_device"] = (~df.duplicated(subset=["user_id", "device_id"])).astype(int)
df["avg_ticket_user"] = df.groupby("user_id")["amount"].transform(
    lambda x: x.expanding().mean().shift(1)
).fillna(df["amount"])

DROP_COLS = [
    "transaction_id", "user_id", "merchant_id", "timestamp", "description",
    "device_id", "ip_address", "location", "request_description",
    "request_description_keywords", "url_referrer", "is_fraud",
    "handle_verification_status"  # perfect 1:1 proxy for is_fraud - data leak
]

categorical_candidates = [c for c in df.columns
                           if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]))
                           and c not in DROP_COLS]
low_card_categoricals = [c for c in categorical_candidates if df[c].nunique() <= 20]
high_card_dropped = [c for c in categorical_candidates if c not in low_card_categoricals]
DROP_COLS = DROP_COLS + high_card_dropped

print(f"\nOne-hot encoding: {low_card_categoricals}")
print(f"Dropping (too high cardinality or free text): {high_card_dropped}")

df_encoded = pd.get_dummies(df, columns=low_card_categoricals)
df_encoded.columns = [
    str(c).replace("[", "_").replace("]", "_").replace("<", "_").replace(">", "_").replace(",", "_")
    for c in df_encoded.columns
]

FEATURES = [c for c in df_encoded.columns if c not in DROP_COLS]
assert "mule_score" in FEATURES, "mule_score got dropped somewhere -- check DROP_COLS"
TARGET = "is_fraud"

X = df_encoded[FEATURES]
y = df_encoded[TARGET]
groups = df["merchant_id"]  # split by this -- NOT a random row split

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

overlap = set(groups.iloc[train_idx]) & set(groups.iloc[test_idx])
print(f"\nMerchant overlap between train/test: {len(overlap)} (must be 0)")
print(f"Train size: {len(X_train)}, fraud rate: {y_train.mean():.4f}")
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

# Fit on plain numpy arrays (not the DataFrame) so the booster's internal
# feature names default to f0/f1/f2... -- required for onnxmltools to
# convert this model without erroring on named columns like "mule_score".
model.fit(X_train.values, y_train.values,
          eval_set=[(X_test.values, y_test.values)], verbose=False)

y_proba = model.predict_proba(X_test.values)[:, 1]
ap = average_precision_score(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)
print(f"\nPR-AUC: {ap:.4f} | ROC-AUC: {auc:.4f}")
print("(If this is still ~1.0, something else is leaking -- it should NOT be, "
      "now that merchants are held out. A real, honest number here is more "
      "useful for your pitch than a fake perfect one.)")

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

print("\nTop 20 feature importances (check where mule_score ranks now):")
importances = sorted(zip(FEATURES, model.feature_importances_), key=lambda x: -x[1])[:20]
for feat, imp in importances:
    marker = "  <-- Member 3's feature" if feat == "mule_score" else ""
    print(f"  {feat:45s} {imp:.4f}{marker}")

with open("fraud_model_v3_with_mule.pkl", "wb") as f:
    pickle.dump({"threshold": float(chosen_threshold), "features": FEATURES}, f)
print("\nSaved metadata to fraud_model_v3_with_mule.pkl")

from onnxmltools import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType

onnx_model = convert_xgboost(
    model, initial_types=[("input", FloatTensorType([None, len(FEATURES)]))]
)
with open("fraud_model_v3_with_mule.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
print("Saved ONNX model to fraud_model_v3_with_mule.onnx")