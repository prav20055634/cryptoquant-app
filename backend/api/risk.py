from fastapi import APIRouter
from pydantic import BaseModel
from backend.risk.manager import RiskManager
from backend.core.config import settings

router = APIRouter()
_rm = RiskManager()

class SizeRequest(BaseModel):
    pair: str
    entry: float
    stop_loss: float
    take_profit: float
    balance: float = settings.DEFAULT_ACCOUNT_BALANCE

@router.post("/size")
async def position_size(req: SizeRequest):
    result = _rm.validate_and_size(req.pair, req.entry, req.stop_loss, req.take_profit, req.balance)
    return result.__dict__

@router.get("/status")
async def risk_status():
    return _rm.get_status()

@router.get("/rules")
async def risk_rules():
    return {
        "max_risk_per_trade": "1% of account balance",
        "min_risk_reward": "1:2 minimum",
        "max_daily_drawdown": "5%",
        "min_confidence": "65%",
        "min_algo_confirmations": "3 of 7",
    }
