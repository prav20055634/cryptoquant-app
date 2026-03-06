from fastapi import APIRouter, Query
from backend.core.store import store
from backend.core.config import settings

router = APIRouter()

@router.get("/")
async def get_signals(limit: int = Query(50, ge=1, le=200), pair: str = Query(None), signal_type: str = Query(None)):
    return {"signals": store.get_signals(limit, pair, signal_type), "count": limit}

@router.post("/scan")
async def trigger_scan():
    from backend.services.signal_engine.generator import SignalGenerator
    gen = SignalGenerator()
    signals = await gen.scan_all_pairs()
    return {"message": f"Scan complete. {len(signals)} signals generated.", "count": len(signals)}

@router.get("/pair/{pair}")
async def analyze_pair(pair: str):
    from backend.services.signal_engine.generator import SignalGenerator
    gen = SignalGenerator()
    sig = await gen.analyze_single(pair.upper())
    if not sig:
        return {"message": f"No confirmed signal for {pair}", "signal": None}
    return {"signal": sig.to_dict()}

@router.get("/stats")
async def signal_stats():
    signals = store.get_signals(200)
    long_count  = sum(1 for s in signals if s["signal_type"] == "LONG")
    short_count = sum(1 for s in signals if s["signal_type"] == "SHORT")
    high_conf   = [s for s in signals if s["confidence_score"] >= 80]
    return {"total": len(signals), "long": long_count, "short": short_count, "high_confidence": len(high_conf), "platform": store.get_analytics()}
