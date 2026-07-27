from datetime import datetime

from edge_layer.device_fingerprint import DeviceFingerprint
from edge_layer.transaction_analyzer import TransactionAnalyzer
from edge_layer.behavior_monitor import BehaviorMonitor
from ml.predict import FraudPredictor


class RiskEngine:

    def __init__(self):
        self.device = DeviceFingerprint()
        self.transaction = TransactionAnalyzer()
        self.behavior = BehaviorMonitor()
        self.ml = FraudPredictor()

    def evaluate(self, request):

        # Device Analysis
        device = self.device.evaluate(
            request.device_id,
            request.rooted,
            request.emulator
        )

        # Transaction Analysis
        transaction = self.transaction.evaluate(
            request.amount,
            request.new_beneficiary,
            request.unusual_location,
            request.late_night,
            request.high_frequency
        )

        # Behavior Analysis
        behavior = self.behavior.evaluate(
            request.typing_speed,
            request.hesitation_time,
            request.cancelled_attempts,
            request.rapid_retries
        )

        # Rule-based score
        rule_score = (
            device["device_score"] * 0.3 +
            transaction["transaction_score"] * 0.4 +
            behavior["behavior_score"] * 0.3
        )

        # ML Prediction
        ml_result = self.ml.predict(request)
        ml_score = ml_result["fraud_probability"] * 100

        # Final combined score
        final_score = round((rule_score * 0.7) + (ml_score * 0.3), 2)

        # Determine risk level
        if final_score >= 80:
            risk = "LOW"
        elif final_score >= 50:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        # Decision
        if risk == "LOW":
            decision = "ALLOW"
        elif risk == "MEDIUM":
            decision = "VERIFY"
        else:
            decision = "BLOCK"

        return {
            "device": device,
            "transaction": transaction,
            "behavior": behavior,
            "risk_score": final_score,
            "risk_level": risk,
            "decision": decision,
            "ml_prediction": ml_result["prediction"],
            "fraud_probability": ml_result["fraud_probability"],
            "timestamp": datetime.now().isoformat()
        }