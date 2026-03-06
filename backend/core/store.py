"""
In-Memory Signal Store
Thread-safe ring buffer for signals, market data, and analytics.
No database needed — everything lives in memory while app runs.
"""
import asyncio
from collections import deque
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class SignalRecord:
    id: str
    pair: str
    signal_type: str          # LONG / SHORT
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_percent: float
    confidence_score: float
    risk_reward: float
    algorithms_confirmed: List[str]
    pattern: str
    market_structure: str
    timeframe: str
    timestamp: str
    status: str = "ACTIVE"    # ACTIVE / TP_HIT / SL_HIT / EXPIRED
    result_pnl: Optional[float] = None
    composite_score: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MarketSnapshot:
    pair: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: str
    rsi: float = 50.0
    trend: str = "NEUTRAL"


class SignalStore:
    """Central in-memory store — singleton used across all services."""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self._signals: deque = deque(maxlen=200)
        self._market_data: Dict[str, MarketSnapshot] = {}
        self._analytics: Dict[str, Any] = {
            "total_signals": 0,
            "signals_today": 0,
            "long_signals": 0,
            "short_signals": 0,
            "platform_start": datetime.utcnow().isoformat(),
            "last_scan": None,
            "pairs_scanned": 0,
        }
        self._backtest_results: deque = deque(maxlen=50)
        self._signal_counter: int = 0

    def add_signal(self, signal: SignalRecord):
        self._signals.appendleft(signal)   # newest first
        self._analytics["total_signals"] += 1
        self._analytics["signals_today"] += 1
        if signal.signal_type == "LONG":
            self._analytics["long_signals"] += 1
        else:
            self._analytics["short_signals"] += 1

    def get_signals(self, limit: int = 50, pair: Optional[str] = None,
                    signal_type: Optional[str] = None) -> List[Dict]:
        signals = list(self._signals)
        if pair:
            signals = [s for s in signals if s.pair == pair]
        if signal_type:
            signals = [s for s in signals if s.signal_type == signal_type]
        return [s.to_dict() for s in signals[:limit]]

    def get_signal_by_id(self, signal_id: str) -> Optional[Dict]:
        for s in self._signals:
            if s.id == signal_id:
                return s.to_dict()
        return None

    def update_signal_status(self, signal_id: str, status: str, pnl: float = None):
        for s in self._signals:
            if s.id == signal_id:
                s.status = status
                if pnl is not None:
                    s.result_pnl = pnl
                break

    def update_market_data(self, pair: str, snapshot: MarketSnapshot):
        self._market_data[pair] = snapshot

    def get_market_data(self, pair: Optional[str] = None) -> Dict:
        if pair:
            snap = self._market_data.get(pair)
            return snap.__dict__ if snap else {}
        return {k: v.__dict__ for k, v in self._market_data.items()}

    def update_analytics(self, key: str, value: Any):
        self._analytics[key] = value

    def get_analytics(self) -> Dict:
        return dict(self._analytics)

    def add_backtest_result(self, result: Dict):
        self._backtest_results.appendleft(result)

    def get_backtest_results(self, limit: int = 20) -> List[Dict]:
        return list(self._backtest_results)[:limit]

    def next_signal_id(self) -> str:
        self._signal_counter += 1
        return f"SIG{self._signal_counter:05d}"

    def clear_daily_stats(self):
        self._analytics["signals_today"] = 0


# Global singleton
store = SignalStore()
