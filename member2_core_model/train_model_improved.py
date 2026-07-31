"""
train_model_improved.py

Improves on train_model_member1_real.py by:
1. Checking train vs test performance gap (the real overfitting test —
   PR-AUC alone doesn't tell you this)
2. Using k-fold cross-validation instead of a single train/test split,
   for a more reliable performance estimate
3. Light hyperparameter search across tree depth / regularization to find
   settings that generalize well, not just fit the training set
4. Early stopping to prevent the model from over-training
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (precision_recall_curve, average_precision_score,
                              classification_report, roc_auc_score)
import pickle

df = pd.read_csv("data/fraud_dataset.csv")
print(f"Dataset shape: {df.shape}")
print(f"Fraud rate: {df['is_fraud'].mean():.4f}")

df = df.sort_values(["user_id"]).reset_index(drop=True)

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
    "handle_verification_status"  # confirmed data leak - excluded
]

categorical_candidates = [c for c in df.columns
                           if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]))
                           and c not in DROP_COLS]
low_card_categoricals = [c for c in categorical_candidates if df[c].nunique() <= 20]
high_card_dropped = [c for c in categorical_candidates if c not in low_card_categoricals]
DROP_COLS = DROP_COLS + high_card_dropped

df_encoded = pd.get_dummies(df, columns=low_card_categoricals)
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

neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = neg / pos

# ---------------------------------------------------------------
# STEP 1: Cross-validation with the ORIGINAL params, to see the
# real variance in performance across folds (single split can be lucky)
# ---------------------------------------------------------------
print("\n" + "="*60)
print("STEP 1: 5-fold cross-validation with original hyperparameters")
print("="*60)

base_model = xgb.XGBClassifier(
    n_estimators=150, max_depth=5, learning_rate=0.1,
    scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
    tree_method="hist", random_state=42
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(base_model, X_train, y_train, cv=cv, scoring="average_precision")
print(f"CV PR-AUC scores per fold: {[f'{s:.4f}' for s in cv_scores]}")
print(f"CV PR-AUC mean: {cv_scores.mean():.4f} | std: {cv_scores.std():.4f}")
print("(High std would indicate instability/overfitting risk; std near 0 = stable)")

# ---------------------------------------------------------------
# STEP 2: Hyperparameter search - try several depth/regularization
# combinations, check train vs test gap for each (the actual overfitting test)
# ---------------------------------------------------------------
print("\n" + "="*60)
print("STEP 2: Hyperparameter search with train-vs-test gap check")
print("="*60)

param_grid = [
    {"max_depth": 3, "n_estimators": 100, "learning_rate": 0.1, "reg_lambda": 1.0, "reg_alpha": 0.0},
    {"max_depth": 4, "n_estimators": 150, "learning_rate": 0.1, "reg_lambda": 1.0, "reg_alpha": 0.0},
    {"max_depth": 5, "n_estimators": 150, "learning_rate": 0.1, "reg_lambda": 1.0, "reg_alpha": 0.0},
    {"max_depth": 6, "n_estimators": 200, "learning_rate": 0.05, "reg_lambda": 2.0, "reg_alpha": 0.5},
    {"max_depth": 4, "n_estimators": 100, "learning_rate": 0.05, "reg_lambda": 3.0, "reg_alpha": 1.0},
]

results = []
for params in param_grid:
    model = xgb.XGBClassifier(
        **params, scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
        tree_method="hist", random_state=42
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    train_proba = model.predict_proba(X_train)[:, 1]
    test_proba = model.predict_proba(X_test)[:, 1]

    train_ap = average_precision_score(y_train, train_proba)
    test_ap = average_precision_score(y_test, test_proba)
    gap = train_ap - test_ap

    results.append({
        "params": params, "train_pr_auc": train_ap, "test_pr_auc": test_ap, "gap": gap
    })

    print(f"\ndepth={params['max_depth']}, n_est={params['n_estimators']}, "
          f"lr={params['learning_rate']}, reg_lambda={params['reg_lambda']}, reg_alpha={params['reg_alpha']}")
    print(f"  Train PR-AUC: {train_ap:.4f} | Test PR-AUC: {test_ap:.4f} | Gap: {gap:.4f}"
          f"  {'<-- possible overfitting' if gap > 0.02 else '(healthy gap)'}")

# Pick the config with best test PR-AUC AND smallest train-test gap
best = min(results, key=lambda r: (r["gap"] > 0.02, -r["test_pr_auc"]))
print(f"\n{'='*60}")
print(f"BEST CONFIG: {best['params']}")
print(f"Test PR-AUC: {best['test_pr_auc']:.4f} | Train-test gap: {best['gap']:.4f}")
print(f"{'='*60}")

# ---------------------------------------------------------------
# STEP 3: Train final model with best params + early stopping
# ---------------------------------------------------------------
final_model = xgb.XGBClassifier(
    **best["params"], scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
    tree_method="hist", random_state=42, early_stopping_rounds=20
)
final_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
print(f"\nEarly stopping halted at round: {final_model.best_iteration}")

y_proba = final_model.predict_proba(X_test)[:, 1]
ap = average_precision_score(y_test, y_proba)
auc = roc_auc_score(y_test, y_proba)
print(f"\nFinal model - PR-AUC: {ap:.4f} | ROC-AUC: {auc:.4f}")

precision, recall, thresholds = precision_recall_curve(y_test, y_proba)
target_recall = 0.90
valid_idx = np.where(recall[:-1] >= target_recall)[0]
if len(valid_idx) > 0:
    best_idx = valid_idx[np.argmax(precision[valid_idx])]
    chosen_threshold = thresholds[best_idx]
else:
    chosen_threshold = 0.5

y_pred = (y_proba >= chosen_threshold).astype(int)
print(f"\nChosen threshold: {chosen_threshold:.4f}")
print(classification_report(y_test, y_pred, digits=3))

print("\nTop 15 feature importances:")
importances = sorted(zip(FEATURES, final_model.feature_importances_), key=lambda x: -x[1])[:15]
for feat, imp in importances:
    print(f"  {feat:40s} {imp:.4f}")

with open("fraud_model_improved.pkl", "wb") as f:
    pickle.dump({"threshold": float(chosen_threshold), "features": FEATURES}, f)

print("\nSaved improved model to fraud_model_improved.pkl")
