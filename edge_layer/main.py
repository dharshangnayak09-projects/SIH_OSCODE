from typing import Optional, Dict, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from edge_layer.database import (
    create_table, save_transaction, get_all_transactions,
    get_recent_transactions, get_statistics,
)
from edge_layer.risk_engine import RiskEngine
from edge_layer.logger import logger

app = FastAPI()

# Allow the Vite dev server (default port 5173) to call this API from the browser.
# Without this, every fetch() from the frontend fails silently with a CORS error.
import os

# Allow the frontend to call this API from the browser. Set FRONTEND_URL as
# an env var on your hosting provider once deployed (e.g. your Vercel URL);
# localhost is always allowed for local development.
allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
if os.environ.get("FRONTEND_URL"):
    allowed_origins.append(os.environ["FRONTEND_URL"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # Optional display/context fields - not used by the ML/rules models,
    # only stored so the dashboard can show real sender/receiver info
    # instead of hardcoded demo data.
    sender_name: Optional[str] = None
    sender_vpa: Optional[str] = None
    receiver_name: Optional[str] = None
    receiver_vpa: Optional[str] = None
    transaction_type: Optional[str] = None

    backend_txn: Optional[Dict[str, Any]] = None


@app.get("/")
def home():
    return {"message": "Edge Layer Running"}


@app.post("/evaluate")
def evaluate(request: TransactionRequest):
    result = engine.evaluate(request)

    logger.info(
        f"Device={request.device_id}, Amount={request.amount}, "
        f"Risk={result['risk_level']}, Score={result['risk_score']}"
    )

    transaction_id = save_transaction(
        request.device_id, request.amount,
        result["risk_score"], result["risk_level"],
        decision=result["decision"],
        sender_name=request.sender_name,
        sender_vpa=request.sender_vpa,
        receiver_name=request.receiver_name,
        receiver_vpa=request.receiver_vpa,
        transaction_type=request.transaction_type,
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
    return {"status": "healthy", "service": "Edge Layer", "version": "1.0.0"}
