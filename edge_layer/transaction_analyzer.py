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

        if amount > 50000:
            score -= 30
        elif amount > 10000:
            score -= 15

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