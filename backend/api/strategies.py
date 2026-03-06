from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def list_all():
    return {"strategies": [
        {"id": 1, "name": "Trend Following",    "algo": "EMA 9/21/50 stack + HH/HL structure"},
        {"id": 2, "name": "Mean Reversion",      "algo": "RSI extremes + BB touch"},
        {"id": 3, "name": "Momentum",            "algo": "MACD cross + RSI + vol spike"},
        {"id": 4, "name": "Breakout Detection",  "algo": "Near resistance + vol confirm"},
        {"id": 5, "name": "Market Structure",    "algo": "HH/HL/LH/LL analysis"},
        {"id": 6, "name": "Pattern Recognition", "algo": "Candlestick + chart patterns"},
        {"id": 7, "name": "ML Optimizer",        "algo": "Genetic algorithm tuning"},
    ]}

@router.get("/ml/params")
async def ml_params():
    from backend.ml.optimization.optimizer import MLOptimizer
    return MLOptimizer().get_report()
