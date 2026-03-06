from fastapi import APIRouter, HTTPException, Query
from backend.core.store import store
from backend.core.config import settings

router = APIRouter()

@router.get("/pairs")
async def get_pairs():
    return {"pairs": settings.TRADING_PAIRS}

@router.get("/prices")
async def get_all_prices():
    return {"market": store.get_market_data()}

@router.get("/ticker/{symbol}")
async def get_ticker(symbol: str):
    data = store.get_market_data(symbol.upper())
    if not data:
        raise HTTPException(404, f"No data for {symbol}")
    return data

@router.get("/ohlcv/{symbol}")
async def get_ohlcv(symbol: str, interval: str = Query("1h"), limit: int = Query(200, ge=10, le=1000)):
    from backend.services.market_data.collector import MarketDataCollector
    c = MarketDataCollector()
    df = await c.fetch_ohlcv(symbol.upper(), interval, limit)
    if df.empty:
        raise HTTPException(404, f"No OHLCV data for {symbol}")
    df_r = df.reset_index()
    df_r.columns = ["timestamp", "open", "high", "low", "close", "volume"]
    df_r["timestamp"] = df_r["timestamp"].astype(str)
    return {"symbol": symbol, "interval": interval, "candles": df_r.to_dict("records")}

@router.get("/analysis/{symbol}")
async def get_analysis(symbol: str, interval: str = "1h"):
    from backend.services.market_data.collector import MarketDataCollector
    from backend.services.technical_analysis.indicators import TechnicalAnalysisEngine
    c = MarketDataCollector()
    ta = TechnicalAnalysisEngine()
    df = await c.fetch_ohlcv(symbol.upper(), interval)
    if df.empty:
        raise HTTPException(404, "No data")
    return {"symbol": symbol, "interval": interval, "analysis": ta.analyze(df)}

@router.get("/sentiment")
async def get_sentiment():
    from backend.services.market_data.collector import MarketDataCollector
    c = MarketDataCollector()
    return await c.fetch_sentiment()
