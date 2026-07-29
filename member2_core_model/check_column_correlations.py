import pandas as pd

df = pd.read_csv("data/upi_transactions_2024.csv")
df = df.rename(columns={"amount (INR)": "amount"})

print("=== Amount stats by fraud label ===")
print(df.groupby("fraud_flag")["amount"].describe())
print()

for col in ["transaction type", "merchant_category", "transaction_status",
            "device_type", "network_type", "sender_age_group", "receiver_age_group",
            "sender_state", "sender_bank", "receiver_bank", "hour_of_day", "is_weekend"]:
    print(f"--- Fraud rate by {col} ---")
    result = df.groupby(col)["fraud_flag"].agg(["mean", "count"]).sort_values("mean", ascending=False)
    print(result)
    print()

overall_rate = df["fraud_flag"].mean()
print(f"Overall fraud rate: {overall_rate:.5f}")
print("(Compare each group's rate above to this baseline — if none deviate meaningfully")
print(" beyond what's explainable by small sample size, there's no usable signal.)")
