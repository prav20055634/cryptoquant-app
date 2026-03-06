from fastapi import APIRouter
from backend.core.store import store
router = APIRouter()

@router.get("/overview")
async def overview():
    signals = store.get_signals(200)
    bt      = store.get_backtest_results(10)
    avg_conf = sum(s["confidence_score"] for s in signals) / max(len(signals), 1)
    by_pair  = {}
    for s in signals:
        by_pair[s["pair"]] = by_pair.get(s["pair"], 0) + 1
    top = max(by_pair, key=by_pair.get) if by_pair else "—"
    return {
        "platform": store.get_analytics(),
        "signals": {"total": len(signals), "avg_confidence": round(avg_conf, 1), "top_pair": top, "by_pair": by_pair},
        "latest_backtests": bt[:3],
    }
