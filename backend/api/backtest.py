from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.core.store import store

router = APIRouter()

class BacktestRequest(BaseModel):
    pair: str = "BTCUSDT"
    timeframe: str = "1h"
    strategy: str = "TrendMomentum"
    limit: int = 300

@router.post("/run")
async def run_backtest(req: BacktestRequest):
    from backend.services.market_data.collector import MarketDataCollector
    from backend.backtest.engine import BacktestEngine
    c = MarketDataCollector()
    engine = BacktestEngine()
    df = await c.fetch_ohlcv(req.pair.upper(), req.timeframe, req.limit)
    if df.empty:
        raise HTTPException(404, f"No data for {req.pair}")
    result = engine.run(df, req.pair.upper(), req.strategy, req.timeframe)
    store.add_backtest_result(result.to_dict())
    return result.to_dict()

@router.get("/results")
async def get_results(limit: int = 20):
    return {"results": store.get_backtest_results(limit)}

@router.get("/strategies")
async def list_strategies():
    return {"strategies": [
        {"id": "TrendMomentum", "name": "Trend + Momentum", "desc": "EMA + MACD + RSI"},
        {"id": "MeanReversion",  "name": "Mean Reversion",   "desc": "RSI extremes + Bollinger Bands"},
        {"id": "BreakoutMA",     "name": "MA Breakout",      "desc": "EMA 50 breakout"},
        {"id": "TrendFollow",    "name": "Trend Follow",     "desc": "Long-term trend following"},
    ]}
