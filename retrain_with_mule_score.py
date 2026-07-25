"""
Integration Step 2 — retrain Member 2's model with mule_score included
=========================================================================
Same training logic as Dhruv's train_model.py (time-based split,
scale_pos_weight for imbalance, recall-targeted threshold), but:
  - reads data/upi_transactions_with_mule_score.csv (output of merge_mule_score.py)
  - adds "mule_score" as an 11th feature
  - trains BOTH a baseline (10 features, no mule_score) and an enhanced
    model (11 features, with mule_score) so you can show judges a real
    before/after number, not just claim the graph feature helps.

Falls back to sklearn's HistGradientBoostingClassifier if xgboost isn't
installed (same fallback pattern as the rest of this project) — swap in
xgboost for the real submission, the interface is identical.

Usage:
    python retrain_with_mule_score.py
"""

import json
import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_curve, average_precision_score, roc_auc_score

BASE_FEATURES = [
    "amount", "txn_count_1h", "avg_ticket_sender", "amount_zscore",
    "time_since_last_txn_min", "geo_velocity_kmph", "new_payee_flag",
    "is_odd_hour", "hour", "is_p2m",
]


def get_model(scale_pos_weight):
    try:
        import xgboost as xgb
        return xgb.XGBClassifier(
            n_estimators=150, max_depth=5, learning_rate=0.1,
            scale_pos_weight=scale_pos_weight, eval_metric="aucpr",
            tree_method="hist", random_state=42,
        ), "xgboost"
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        print("[warn] xgboost not installed here — using sklearn fallback for this test run. "
              "Swap to xgboost for the real submission (same .fit/.predict_proba interface).")
        return HistGradientBoostingClassifier(
            max_iter=150, max_depth=5, learning_rate=0.1,
            class_weight={0: 1, 1: scale_pos_weight}, random_state=42,
        ), "sklearn_histgb"


def tune_threshold(y_true, y_prob, target_recall=0.90):
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)
    valid = np.where(recall[:-1] >= target_recall)[0]
    if len(valid) == 0:
        return 0.5, 0.0, 0.0
    best = valid[np.argmax(precision[valid])]
    return thresholds[best], precision[best], recall[best]


def train_and_eval(df, features, label):
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

    X_train, y_train = train_df[features], train_df["is_fraud"]
    X_test, y_test = test_df[features], test_df["is_fraud"]

    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    model, model_name = get_model(scale_pos_weight)
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)
    ap = average_precision_score(y_test, y_prob)
    threshold, precision, recall = tune_threshold(y_test, y_prob)

    print(f"\n=== {label} ({len(features)} features, {model_name}) ===")
    print(f"  ROC-AUC: {auc:.4f}  |  PR-AUC: {ap:.4f}")
    print(f"  At threshold {threshold:.4f}: recall={recall:.3f}, precision={precision:.3f}")

    return {
        "label": label, "model": model, "features": features, "model_name": model_name,
        "roc_auc": round(float(auc), 4), "pr_auc": round(float(ap), 4),
        "threshold": round(float(threshold), 4),
        "precision_at_threshold": round(float(precision), 4),
        "recall_at_threshold": round(float(recall), 4),
    }


def main():
    df = pd.read_csv("data/upi_transactions_with_mule_score.csv", parse_dates=["timestamp"])
    df["is_p2m"] = (df["transaction_type"] == "P2M").astype(int)

    baseline = train_and_eval(df, BASE_FEATURES, "BASELINE (no mule_score)")
    enhanced = train_and_eval(df, BASE_FEATURES + ["mule_score"], "ENHANCED (with mule_score)")

    with open("models/fraud_model_v2.pkl", "wb") as f:
        pickle.dump({
            "model": enhanced["model"],
            "features": enhanced["features"],
            "threshold": enhanced["threshold"],
        }, f)

    comparison = {
        "baseline": {k: v for k, v in baseline.items() if k not in ("model",)},
        "enhanced": {k: v for k, v in enhanced.items() if k not in ("model",)},
        "pr_auc_delta": round(enhanced["pr_auc"] - baseline["pr_auc"], 4),
        "roc_auc_delta": round(enhanced["roc_auc"] - baseline["roc_auc"], 4),
    }
    with open("reports/mule_score_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"\n[done] PR-AUC change from adding mule_score: {comparison['pr_auc_delta']:+.4f}")
    print(f"       Saved models/fraud_model_v2.pkl + reports/mule_score_comparison.json")
    if comparison["pr_auc_delta"] <= 0:
        print("\n[note] No lift here is expected on THIS dataset — it has no real mule-ring")
        print("       fraud planted yet (see member3_mule_detection.py's validation notes).")
        print("       The lift will show up once real/planted mule patterns exist in training data.")


if __name__ == "__main__":
    main()
