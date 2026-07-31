from transaction_analyzer import TransactionAnalyzer

analyzer = TransactionAnalyzer()

print(analyzer.evaluate(500))
print(analyzer.evaluate(15000))
print(analyzer.evaluate(70000))
print(analyzer.evaluate(
    70000,
    new_beneficiary=True,
    unusual_location=True,
    late_night=True,
    high_frequency=True
))