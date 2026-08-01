class TransactionAnalyzer:
    def evaluate(
        self,
        amount,
        new_beneficiary=False,
        unusual_location=False,
        late_night=False,
        high_frequency=False,
    ):
        score = 100

        # Proportional amount scoring instead of two coarse buckets - so
        # different amounts genuinely produce different scores, not just
        # amounts that cross the 10k/50k thresholds.
        if amount > 100000:
            score -= 40
        elif amount > 50000:
            score -= 30
        elif amount > 20000:
            score -= 20
        elif amount > 10000:
            score -= 12
        elif amount > 5000:
            score -= 6
        elif amount > 2000:
            score -= 2

        if new_beneficiary:
            score -= 20

        if unusual_location:
            score -= 20

        if late_night:
            score -= 10

        if high_frequency:
            score -= 20

        score = max(score, 0)

        return {
            "transaction_score": score,
            "amount": amount,
        }