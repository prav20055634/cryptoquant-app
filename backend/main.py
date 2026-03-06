"""
CryptoQuant AI Trading Platform — Backend Entry Point
Run: uvicorn backend.main:app --reload --port 8000
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

_scheduler_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _scheduler_task
    logger.info("🚀 CryptoQuant AI Platform starting...")
    from backend.core.scheduler import TradingScheduler
    scheduler = TradingScheduler()
    _scheduler_task = asyncio.create_task(scheduler.start())
    logger.info("✅ All services active — scanning markets 24/7")
    yield
    if _scheduler_task:
        _scheduler_task.cancel()
    logger.info("🛑 Platform shutdown complete")


app = FastAPI(
    title="CryptoQuant AI Trading Platform",
    description="Institutional-grade AI crypto trading signals — in-app delivery",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
from backend.api.signals import router as signals_router
from backend.api.market import router as market_router
from backend.api.backtest import router as backtest_router
from backend.api.strategies import router as strategies_router
from backend.api.risk import router as risk_router
from backend.api.analytics import router as analytics_router

app.include_router(signals_router,    prefix="/api/v1/signals",    tags=["Signals"])
app.include_router(market_router,     prefix="/api/v1/market",     tags=["Market"])
app.include_router(backtest_router,   prefix="/api/v1/backtest",   tags=["Backtest"])
app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["Strategies"])
app.include_router(risk_router,       prefix="/api/v1/risk",       tags=["Risk"])
app.include_router(analytics_router,  prefix="/api/v1/analytics",  tags=["Analytics"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "platform": "CryptoQuant AI",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
