import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

print("Loading dataset...")
df = pd.read_csv("dataset/sih_fraud_dataset.csv")

X = df.drop("fraud", axis=1)
y = df["fraud"]

print("Splitting dataset...")
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training model...")
model = RandomForestClassifier(
    n_estimators=50,   # Reduced from 100 for faster training
    random_state=42,
    n_jobs=-1          # Use all CPU cores
)

model.fit(X_train, y_train)

print("Evaluating...")
predictions = model.predict(X_test)

print(classification_report(y_test, predictions))

print("Saving model...")
joblib.dump(model, "models/fraud_model.pkl")

print("Done!")