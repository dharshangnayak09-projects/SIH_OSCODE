from datetime import datetime

from edge_layer.device_fingerprint import DeviceFingerprint
from edge_layer.transaction_analyzer import TransactionAnalyzer
from edge_layer.behavior_monitor import BehaviorMonitor
from ml.predict import FraudPredictor

import traceback
try:
    from predict_with_mule_score import predict_transaction as predict_backend_model
    BACKEND_MODEL_AVAILABLE = True
    print("[risk_engine] backend model loaded successfully")
except Exception:
    BACKEND_MODEL_AVAILABLE = False
    print("[risk_engine] FAILED to load backend model:")
    traceback.print_exc()


class RiskEngine:

    def __init__(self):
        self.device = DeviceFingerprint()
        self.transaction = TransactionAnalyzer()
        self.behavior = BehaviorMonitor()
        self.ml = FraudPredictor()

    def evaluate(self, request):

        device = self.device.evaluate(
            request.device_id, request.rooted, request.emulator
        )
        transaction = self.transaction.evaluate(
            request.amount, request.new_beneficiary, request.unusual_location,
            request.late_night, request.high_frequency
        )
        behavior = self.behavior.evaluate(
            request.typing_speed, request.hesitation_time,
            request.cancelled_attempts, request.rapid_retries
        )

        rule_score = (
            device["device_score"] * 0.3 +
            transaction["transaction_score"] * 0.4 +
            behavior["behavior_score"] * 0.3
        )

        ml_result = self.ml.predict(request)
        ml_score = (1 - ml_result["fraud_probability"]) * 100

        final_score = round((rule_score * 0.7) + (ml_score * 0.3), 2)

        if final_score >= 80:
            risk = "LOW"
        elif final_score >= 50:
            risk = "MEDIUM"
        else:
            risk = "HIGH"

        decision = {"LOW": "ALLOW", "MEDIUM": "VERIFY"}.get(risk, "BLOCK")

        result = {
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

        backend_fields = getattr(request, "backend_txn", None)
        if BACKEND_MODEL_AVAILABLE and backend_fields:
            try:
                result["backend_model"] = predict_backend_model(backend_fields)
            except Exception as e:
                result["backend_model"] = {"error": str(e)}

        return result
