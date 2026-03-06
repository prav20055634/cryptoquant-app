"""
24/7 Trading Scheduler
Runs all background tasks: data collection, signal scanning, backtesting, ML optimization.
"""
import asyncio
import logging
from datetime import datetime, timezone
from backend.core.config import settings

logger = logging.getLogger(__name__)


class TradingScheduler:
    def __init__(self):
        self._running = False
        self._tasks = []

    async def start(self):
        self._running = True
        logger.info("⏱️  Scheduler started — platform running 24/7")

        # Run initial scan immediately on startup
        await asyncio.sleep(3)
        await self._safe_run("initial_market_data", self._collect_market_data)
        await self._safe_run("initial_signal_scan", self._scan_signals)

        # Launch recurring loops
        self._tasks = [
            asyncio.create_task(self._loop("market_data",   settings.MARKET_DATA_INTERVAL, self._collect_market_data)),
            asyncio.create_task(self._loop("signal_scan",   settings.SIGNAL_SCAN_INTERVAL,  self._scan_signals)),
            asyncio.create_task(self._loop("backtest",      settings.BACKTEST_INTERVAL,     self._run_backtests)),
            asyncio.create_task(self._loop("ml_optimize",   settings.ML_OPTIMIZE_INTERVAL,  self._optimize_ml)),
            asyncio.create_task(self._daily_reset_loop()),
        ]
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def stop(self):
        self._running = False
        for task in self._tasks:
            task.cancel()

    async def _loop(self, name: str, interval: int, coro_fn):
        while self._running:
            await asyncio.sleep(interval)
            await self._safe_run(name, coro_fn)

    async def _safe_run(self, name: str, coro_fn):
        try:
            logger.info(f"▶ {name}")
            await coro_fn()
            logger.info(f"✓ {name} complete")
        except Exception as e:
            logger.error(f"✗ {name} error: {e}", exc_info=True)

    async def _collect_market_data(self):
        from backend.services.market_data.collector import MarketDataCollector
        from backend.core.store import store
        from datetime import datetime, timezone
        collector = MarketDataCollector()
        try:
            results = await collector.fetch_all_tickers()
            store.update_analytics("last_scan", datetime.now(timezone.utc).isoformat())
            store.update_analytics("pairs_scanned", len(results))
        finally:
            await collector.close()

    async def _scan_signals(self):
        from backend.services.signal_engine.generator import SignalGenerator
        generator = SignalGenerator()
        try:
            await generator.scan_all_pairs()
        finally:
            await generator.collector.close()
    async def _run_backtests(self):
        from backend.backtest.engine import BacktestEngine
        from backend.services.market_data.collector import MarketDataCollector
        from backend.core.store import store
        collector = MarketDataCollector()
        engine = BacktestEngine()
        for pair in settings.TRADING_PAIRS[:3]:
            df = await collector.fetch_ohlcv(pair, "1h", limit=300)
            if not df.empty:
                result = engine.run(df, pair, "TrendMomentum", "1h")
                store.add_backtest_result(result.to_dict())

    async def _optimize_ml(self):
        from backend.ml.optimization.optimizer import MLOptimizer
        optimizer = MLOptimizer()
        await optimizer.optimize_all_strategies()

    async def _daily_reset_loop(self):
        """Reset daily stats at midnight UTC."""
        while self._running:
            now = datetime.now(timezone.utc)
            # Seconds until next midnight
            seconds_til_midnight = (
                (24 - now.hour - 1) * 3600
                + (60 - now.minute - 1) * 60
                + (60 - now.second)
            )
            await asyncio.sleep(seconds_til_midnight)
            from backend.core.store import store
            store.clear_daily_stats()
            logger.info("🌅 Daily stats reset at midnight UTC")
