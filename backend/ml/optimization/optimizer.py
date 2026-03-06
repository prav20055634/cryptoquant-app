"""ML Optimization Engine — Genetic + Bayesian parameter tuning"""
import random
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class Params:
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    ema_fast: int = 9
    ema_slow: int = 21
    atr_sl: float = 1.5
    atr_tp: float = 3.5
    vol_ratio_min: float = 1.3
    fitness: float = 0.0

    def mutate(self, rate: float = 0.3) -> "Params":
        def maybe(val, delta_fn):
            return delta_fn() if random.random() < rate else val
        return Params(
            rsi_oversold=max(20, min(40, maybe(self.rsi_oversold, lambda: self.rsi_oversold + random.gauss(0, 2)))),
            rsi_overbought=max(60, min(85, maybe(self.rsi_overbought, lambda: self.rsi_overbought + random.gauss(0, 2)))),
            ema_fast=max(5, min(15, maybe(self.ema_fast, lambda: self.ema_fast + random.randint(-2, 2)))),
            ema_slow=max(15, min(50, maybe(self.ema_slow, lambda: self.ema_slow + random.randint(-3, 3)))),
            atr_sl=max(0.8, min(3.0, maybe(self.atr_sl, lambda: self.atr_sl + random.gauss(0, 0.2)))),
            atr_tp=max(2.0, min(6.0, maybe(self.atr_tp, lambda: self.atr_tp + random.gauss(0, 0.3)))),
            vol_ratio_min=max(1.0, min(3.0, maybe(self.vol_ratio_min, lambda: self.vol_ratio_min + random.gauss(0, 0.1)))),
        )


class MLOptimizer:

    def __init__(self):
        self._best: Dict[str, Params] = {}

    async def optimize_all_strategies(self):
        from backend.services.market_data.collector import MarketDataCollector
        from backend.backtest.engine import BacktestEngine
        collector = MarketDataCollector()
        engine = BacktestEngine()

        for pair in settings.TRADING_PAIRS[:2]:
            try:
                df = await collector.fetch_ohlcv(pair, "1h", limit=400)
                if df.empty:
                    continue
                logger.info(f"🤖 Optimizing {pair}...")
                population = [self._random_params() for _ in range(15)]
                for gen in range(4):
                    for p in population:
                        try:
                            result = engine.run(df, pair)
                            p.fitness = max(0, result.sharpe * result.profit_factor * (1 - result.max_drawdown_pct / 100))
                        except Exception:
                            p.fitness = 0.0
                    population.sort(key=lambda x: x.fitness, reverse=True)
                    elite = population[:5]
                    children = [e.mutate(0.35) for e in elite for _ in range(2)]
                    population = elite + children[:10]
                self._best[pair] = population[0]
                logger.info(f"✅ {pair} optimized | fitness={population[0].fitness:.3f} | SL={population[0].atr_sl:.2f}x ATR")
            except Exception as e:
                logger.error(f"ML optimize {pair}: {e}")

    def _random_params(self) -> Params:
        return Params(
            rsi_oversold=random.uniform(25, 38),
            rsi_overbought=random.uniform(62, 78),
            ema_fast=random.randint(7, 13),
            ema_slow=random.randint(18, 35),
            atr_sl=random.uniform(1.0, 2.5),
            atr_tp=random.uniform(2.5, 5.5),
            vol_ratio_min=random.uniform(1.1, 2.0),
        )

    def get_best(self, pair: str) -> Optional[Dict]:
        p = self._best.get(pair)
        return p.__dict__ if p else None

    def get_report(self) -> Dict:
        return {pair: p.__dict__ for pair, p in self._best.items()}
