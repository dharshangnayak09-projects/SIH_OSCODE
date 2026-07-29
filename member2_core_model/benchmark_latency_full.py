import pickle
import numpy as np
import time
import pandas as pd
import xgboost as xgb

with open("fraud_model_full.pkl", "rb") as f:
    bundle = pickle.load(f)

model = bundle["model"]
features = bundle["features"]
threshold = bundle["threshold"]

df = pd.read_csv("data/upi_transactions_full.csv", parse_dates=["timestamp"])
sample_rows = df[features].sample(500, random_state=1).values.astype(np.float32)

# Re-fit on plain numpy arrays (no column names) since onnxmltools breaks
# on string feature names attached by the sklearn-style XGBoost API.
X_all = df[features].values.astype(np.float32)
y_all = df["fraud_flag"].values
model_np = xgb.XGBClassifier(**model.get_params())
model_np.fit(X_all, y_all)
model = model_np

# ---------- Benchmark 1: raw XGBoost, single-row predict ----------
latencies = []
for row in sample_rows:
    x = row.reshape(1, -1)
    t0 = time.perf_counter()
    _ = model.predict_proba(x)
    t1 = time.perf_counter()
    latencies.append((t1 - t0) * 1000)

latencies = np.array(latencies)
print("=== Raw XGBoost (sklearn API) single-row latency ===")
print(f"  mean: {latencies.mean():.3f} ms")
print(f"  p50:  {np.percentile(latencies, 50):.3f} ms")
print(f"  p95:  {np.percentile(latencies, 95):.3f} ms")
print(f"  p99:  {np.percentile(latencies, 99):.3f} ms")

# ---------- Convert to ONNX ----------
from onnxmltools import convert_xgboost
from onnxmltools.convert.common.data_types import FloatTensorType
import onnxruntime as rt

initial_type = [("float_input", FloatTensorType([None, len(features)]))]
onnx_model = convert_xgboost(model, initial_types=initial_type, target_opset=12)

with open("fraud_model_full.onnx", "wb") as f:
    f.write(onnx_model.SerializeToString())

print("\nSaved ONNX model to fraud_model_full.onnx")

# ---------- Benchmark 2: ONNX runtime, single-row predict ----------
sess = rt.InferenceSession("fraud_model_full.onnx", providers=["CPUExecutionProvider"])
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
print(f"  mean: {onnx_latencies.mean():.3f} ms")
print(f"  p50:  {np.percentile(onnx_latencies, 50):.3f} ms")
print(f"  p95:  {np.percentile(onnx_latencies, 95):.3f} ms")
print(f"  p99:  {np.percentile(onnx_latencies, 99):.3f} ms")

speedup = latencies.mean() / onnx_latencies.mean()
print(f"\n=== Speedup: {speedup:.2f}x faster with ONNX ===")

sk_probs = model.predict_proba(sample_rows[:5])[:, 1]
onnx_probs = [sess.run([label_name], {input_name: sample_rows[i:i+1].astype(np.float32)})[0][0][1] for i in range(5)]
print("\nSanity check (sklearn vs onnx probs, first 5 rows):")
for a, b in zip(sk_probs, onnx_probs):
    print(f"  sklearn={a:.4f}  onnx={b:.4f}")
