class BehaviorMonitor:
    def evaluate(
        self,
        typing_speed,
        hesitation_time,
        cancelled_attempts,
        rapid_retries,
    ):
        score = 100

        # Extremely slow typing can indicate hesitation
        if typing_speed < 20:
            score -= 20

        # Long hesitation before confirming payment
        if hesitation_time > 5:
            score -= 20

        # Multiple cancelled attempts
        if cancelled_attempts >= 3:
            score -= 20

        # Multiple retries in a short time
        if rapid_retries:
            score -= 20

        score = max(score, 0)

        return {
            "behavior_score": score
        }