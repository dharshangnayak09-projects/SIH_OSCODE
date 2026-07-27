from fastapi import FastAPI
from pydantic import BaseModel

from edge_layer.database import (
    create_table,
    save_transaction,
    get_all_transactions,
    get_recent_transactions,
    get_statistics,
)

from edge_layer.risk_engine import RiskEngine
from edge_layer.logger import logger

app = FastAPI()

create_table()
engine = RiskEngine()


class TransactionRequest(BaseModel):
    device_id: str
    rooted: bool
    emulator: bool

    amount: float
    new_beneficiary: bool
    unusual_location: bool
    late_night: bool
    high_frequency: bool

    typing_speed: float
    hesitation_time: float
    cancelled_attempts: int
    rapid_retries: bool


@app.get("/")
def home():
    return {"message": "Edge Layer Running"}


@app.post("/evaluate")
def evaluate(request: TransactionRequest):

    result = engine.evaluate(request)

    logger.info(
        f"Device={request.device_id}, "
        f"Amount={request.amount}, "
        f"Risk={result['risk_level']}, "
        f"Score={result['risk_score']}"
    )

    transaction_id = save_transaction(
        request.device_id,
        request.amount,
        result["risk_score"],
        result["risk_level"],
    )

    result["transaction_id"] = transaction_id

    return result


@app.get("/transactions")
def transactions():
    return get_all_transactions()


@app.get("/recent")
def recent():
    return get_recent_transactions()


@app.get("/stats")
def stats():
    return get_statistics()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Edge Layer",
        "version": "1.0.0",
    }