"""
Signal Generation Engine — 7-Algorithm Multi-Confirmation System
Signals are stored in-memory and served via REST API to the frontend.
NO Telegram — signals display in the app itself.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from backend.core.config import settings
from backend.core.store import store, SignalRecord
from backend.services.market_data.collector import MarketDataCollector
from backend.services.technical_analysis.indicators import TechnicalAnalysisEngine, Bias
from backend.risk.manager import RiskManager

logger = logging.getLogger(__name__)


class SignalGenerator:

    def __init__(self):
        self.collector = MarketDataCollector()
        self.ta = TechnicalAnalysisEngine()
        self.risk = RiskManager()

    async def scan_all_pairs(self) -> List[SignalRecord]:
        """Scan all pairs concurrently and store confirmed signals."""
        tasks = [self._analyze_pair(pair) for pair in settings.TRADING_PAIRS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        signals = [r for r in results if isinstance(r, SignalRecord)]
        for sig in signals:
            store.add_signal(sig)
            logger.info(
                f"🚨 Signal: {sig.pair} {sig.signal_type} | "
                f"Entry={sig.entry_price} | Conf={sig.confidence_score:.0f}% | "
                f"Algos={len(sig.algorithms_confirmed)}"
            )
        logger.info(f"Scan complete: {len(signals)} signals from {len(settings.TRADING_PAIRS)} pairs")
        return signals

    async def _analyze_pair(self, pair: str, timeframe: str = "1h") -> Optional[SignalRecord]:
        try:
            df = await self.collector.fetch_ohlcv(pair, timeframe, limit=300)
            if df.empty or len(df) < 100:
                return None

            analysis = self.ta.analyze(df)
            if not analysis:
                return None

            return self._evaluate_algorithms(pair, timeframe, analysis, df)
        except Exception as e:
            logger.error(f"analyze_pair {pair}: {e}")
            return None

    def _evaluate_algorithms(self, pair: str, timeframe: str, analysis: dict, df) -> Optional[SignalRecord]:
        """Run all 7 algorithms and confirm signal if 3+ agree."""
        confirmed_algos = []
        long_score = 0.0
        short_score = 0.0
        composite = analysis["score"]
        ms = analysis["market_structure"]
        ind = analysis["indicators"]
        latest = df.iloc[-1]
        price = float(latest["close"])

        # ── Algorithm 1: Trend Following ─────────────────────────────────────
        if ms["structure"] == "UPTREND":
            confirmed_algos.append("TrendFollow")
            long_score += 1.8
        elif ms["structure"] == "DOWNTREND":
            confirmed_algos.append("TrendFollow")
            short_score += 1.8

        # ── Algorithm 2: Mean Reversion ──────────────────────────────────────
        rsi = ind["rsi"]
        if rsi < 35:
            confirmed_algos.append("MeanReversion")
            long_score += 1.3
        elif rsi > 65:
            confirmed_algos.append("MeanReversion")
            short_score += 1.3

        # ── Algorithm 3: Momentum ────────────────────────────────────────────
        if ind["macd"] > ind["macd_signal"] and rsi > 50 and ind["volume_ratio"] > 1.3:
            confirmed_algos.append("Momentum")
            long_score += 1.5
        elif ind["macd"] < ind["macd_signal"] and rsi < 50 and ind["volume_ratio"] > 1.3:
            confirmed_algos.append("Momentum")
            short_score += 1.5

        # ── Algorithm 4: Breakout Detection ──────────────────────────────────
        resistances = analysis.get("resistance", [])
        supports    = analysis.get("support", [])
        for res in resistances:
            if abs(price - res) / (res + 1e-9) < 0.008:
                confirmed_algos.append("Breakout")
                long_score += 1.2
                break
        for sup in supports:
            if abs(price - sup) / (sup + 1e-9) < 0.008:
                confirmed_algos.append("Breakout")
                short_score += 1.0
                break

        # ── Algorithm 5: Market Structure ────────────────────────────────────
        if ms["bias"] == "BULLISH":
            long_score += 0.8
        elif ms["bias"] == "BEARISH":
            short_score += 0.8
        if ms["hh"] and ms["hl"]:
            confirmed_algos.append("MarketStructure")
            long_score += 1.0
        elif ms["lh"] and ms["ll"]:
            confirmed_algos.append("MarketStructure")
            short_score += 1.0

        # ── Algorithm 6: Pattern Recognition ─────────────────────────────────
        patterns = analysis.get("patterns", [])
        bullish_patterns = [p for p in patterns if p["signal"] in ("BUY", "STRONG_BUY")]
        bearish_patterns = [p for p in patterns if p["signal"] in ("SELL", "STRONG_SELL")]
        if bullish_patterns:
            confirmed_algos.append("PatternRecog")
            long_score += 1.2 * len(bullish_patterns)
        if bearish_patterns:
            confirmed_algos.append("PatternRecog")
            short_score += 1.2 * len(bearish_patterns)

        # ── Algorithm 7: ML / Composite Score ────────────────────────────────
        if composite > 0.35:
            confirmed_algos.append("ML_Score")
            long_score += composite * 2
        elif composite < -0.35:
            confirmed_algos.append("ML_Score")
            short_score += abs(composite) * 2

        # Deduplicate
        confirmed_algos = list(set(confirmed_algos))

        # Require at least 3 independent algorithm confirmations
        if len(confirmed_algos) < 3:
            return None

        # Determine direction from scores
        total = long_score + short_score
        if total < 0.1:
            return None

        signal_type = "LONG" if long_score >= short_score else "SHORT"
        confidence = min(95.0, (max(long_score, short_score) / (total + 1e-9)) * 100)

        if confidence < settings.MIN_CONFIDENCE_SCORE * 100:
            return None

        # Calculate levels using ATR
        atr = float(latest.get("atr", price * 0.015))
        if signal_type == "LONG":
            sl = price - 1.5 * atr
            tp = price + 3.5 * atr
        else:
            sl = price + 1.5 * atr
            tp = price - 3.5 * atr

        # Risk management validation
        sizing = self.risk.validate_and_size(pair, price, sl, tp)
        if not sizing.approved:
            logger.debug(f"Signal rejected ({pair}): {sizing.reason}")
            return None

        # Build signal record
        pattern_names = ", ".join(p["name"] for p in (bullish_patterns + bearish_patterns)) or "—"

        return SignalRecord(
            id=store.next_signal_id(),
            pair=pair,
            signal_type=signal_type,
            entry_price=round(price, 6),
            stop_loss=round(sl, 6),
            take_profit=round(tp, 6),
            risk_percent=round(settings.MAX_RISK_PER_TRADE * 100, 1),
            confidence_score=round(confidence, 1),
            risk_reward=round(sizing.risk_reward, 2),
            algorithms_confirmed=confirmed_algos,
            pattern=pattern_names,
            market_structure=ms["structure"],
            timeframe=timeframe,
            timestamp=datetime.now(timezone.utc).isoformat(),
            composite_score=round(composite, 3),
        )

    async def analyze_single(self, pair: str) -> Optional[SignalRecord]:
        """On-demand analysis for a single pair."""
        sig = await self._analyze_pair(pair)
        if sig:
            store.add_signal(sig)
        return sig
