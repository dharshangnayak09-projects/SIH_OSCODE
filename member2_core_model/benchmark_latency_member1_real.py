import pickle
import numpy as np
import time
import pandas as pd
import xgboost as xgb

with open("fraud_model_member1_real.pkl", "rb") as f:
    bundle = pickle.load(f)

model = bundle["model"]
features = bundle["features"]
threshold = bundle["threshold"]

# Rebuild the same encoded dataframe used in training to get sample rows
df = pd.read_csv("data/fraud_dataset.csv")
df["rolling_txn_count"] = df.groupby("user_id").cumcount() + 1
df["new_merchant_flag"] = (~df.duplicated(subset=["user_id", "merchant_id"])).astype(int)
df["known_device"] = (~df.duplicated(subset=["user_id", "device_id"])).astype(int)
df["avg_ticket_user"] = df.groupby("user_id")["amount"].transform(
    lambda x: x.expanding().mean().shift(1)
).fillna(df["amount"])

categorical_candidates = [c for c in df.columns
                           if (df[c].dtype == object or pd.api.types.is_string_dtype(df[c]))]
low_card_categoricals = [c for c in categorical_candidates if df[c].nunique() <= 20]
df_encoded = pd.get_dummies(df, columns=low_card_categoricals)
df_encoded.columns = [
    str(c).replace("[", "_").replace("]", "_").replace("<", "_").replace(">", "_").replace(",", "_")
    for c in df_encoded.columns
]

# Ensure all expected features exist (fill missing with 0 - e.g. category not in this sample)
for f in features:
    if f not in df_encoded.columns:
        df_encoded[f] = 0

sample_rows = df_encoded[features].sample(500, random_state=1).values.astype(np.float32)

# Re-fit on plain numpy arrays (no column names) for ONNX compatibility
X_all = df_encoded[features].values.astype(np.float32)
y_all = df_encoded["is_fraud"].values
model_np = xgb.XGBClassifier(**model.get_params())
model_np.fit(X_all, y_all)
model = model_np

# ---------- Benchmark 1: raw XGBoost ----------
latencies = []
for row in sample_rows:
    x = row.reshape(1, -1)
    t0 = time.perf_counter()
    _ = model.predict_proba(x)
    t1 = time.perf_counter()
    latencies.append((t1 - t0) * 1000)

latencies = np.array(latencies)
print("=== Raw XGBoost single-row latency ===")
print(f"  mean: {latencies.mean():.3f} ms | p95: {np.percentile(latencies,95):.3f} ms | p99: {np.percentile(latencies,99):.3f} ms")

# ---------- Convert to ONNX ----------
from onnxmltools import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType
import onnxruntime as rt

initial_type = [("float_input", FloatTensorType([None, len(features)]))]
onnx_model = convert_xgboost(model, initial_types=initial_type, target_opset=12)

with open("fraud_model_member1_real.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())
print("\nSaved ONNX model to fraud_model_member1_real.onnx")

sess = rt.InferenceSession("fraud_model_member1_real.onnx", providers=["CPUExecutionProvider"])
input_name = sess.get_inputs()[0].name
label_name = sess.get_outputs()[1].name

onnx_latencies = []
for row in sample_rows:
    x = row.reshape(1, -1).astype(np.float32)
    t0 = time.perf_counter()
    _ = sess.run([label_name], {input_name: x})
    t1 = time.perf_counter()
    onnx_latencies.append((t1 - t0) * 1000)

onnx_latencies = np.array(onnx_latencies)
print("\n=== ONNX Runtime single-row latency ===")
print(f"  mean: {onnx_latencies.mean():.3f} ms | p95: {np.percentile(onnx_latencies,95):.3f} ms | p99: {np.percentile(onnx_latencies,99):.3f} ms")

speedup = latencies.mean() / onnx_latencies.mean()
print(f"\n=== Speedup: {speedup:.2f}x faster with ONNX ===")
