import joblib
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "fraud_model.pkl")

class FraudPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)

    def predict(self, request):
        features = [[
            request.amount,
            request.rooted,
            request.emulator,
            request.new_beneficiary,
            request.unusual_location,
            request.late_night,
            request.high_frequency,
            request.typing_speed,
            request.hesitation_time,
            request.cancelled_attempts,
            request.rapid_retries
        ]]

        prediction = self.model.predict(features)[0]
        probability = self.model.predict_proba(features)[0][1]

        return {
            "prediction": int(prediction),
            "fraud_probability": round(float(probability), 4)
        }