"""
Technical Analysis Engine — 30+ Indicators
RSI, MACD, Bollinger Bands, EMA, ATR, Fibonacci, S/R, Patterns, Market Structure
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Bias(Enum):
    STRONG_BUY = 2
    BUY = 1
    NEUTRAL = 0
    SELL = -1
    STRONG_SELL = -2


@dataclass
class TASignal:
    name: str
    bias: Bias
    value: float
    note: str
    weight: float = 1.0


class TechnicalAnalysisEngine:

    def analyze(self, df: pd.DataFrame) -> Dict:
        if len(df) < 60:
            return {}
        df = df.copy()
        df = self._add_indicators(df)
        signals = (
            self._trend_signals(df) +
            self._momentum_signals(df) +
            self._volatility_signals(df) +
            self._volume_signals(df)
        )
        support, resistance = self._support_resistance(df)
        fib = self._fibonacci(df)
        patterns = self._patterns(df)
        ms = self._market_structure(df)
        score = self._score(signals)
        latest = df.iloc[-1]

        return {
            "signals": [
                {"name": s.name, "bias": s.bias.name, "value": round(s.value, 4), "note": s.note}
                for s in signals
            ],
            "score": round(score, 3),
            "support": support,
            "resistance": resistance,
            "fibonacci": fib,
            "patterns": patterns,
            "market_structure": ms,
            "indicators": {
                "rsi": round(float(latest.get("rsi", 50)), 2),
                "macd": round(float(latest.get("macd", 0)), 4),
                "macd_signal": round(float(latest.get("macd_sig", 0)), 4),
                "ema_9": round(float(latest.get("ema_9", 0)), 4),
                "ema_21": round(float(latest.get("ema_21", 0)), 4),
                "ema_50": round(float(latest.get("ema_50", 0)), 4),
                "bb_upper": round(float(latest.get("bb_up", 0)), 4),
                "bb_lower": round(float(latest.get("bb_lo", 0)), 4),
                "atr": round(float(latest.get("atr", 0)), 4),
                "volume_ratio": round(float(latest.get("vol_ratio", 1)), 2),
            },
        }

    # ── Indicators ────────────────────────────────────────────────────────────

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        c = df["close"]

        # EMAs
        df["ema_9"]  = c.ewm(span=9,  adjust=False).mean()
        df["ema_21"] = c.ewm(span=21, adjust=False).mean()
        df["ema_50"] = c.ewm(span=50, adjust=False).mean()
        df["sma_200"] = c.rolling(200).mean()

        # RSI
        delta = c.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df["rsi"] = 100 - 100 / (1 + gain / (loss + 1e-9))

        # MACD
        e12 = c.ewm(span=12, adjust=False).mean()
        e26 = c.ewm(span=26, adjust=False).mean()
        df["macd"]     = e12 - e26
        df["macd_sig"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_sig"]

        # Bollinger Bands
        sma20 = c.rolling(20).mean()
        std20 = c.rolling(20).std()
        df["bb_up"]  = sma20 + 2 * std20
        df["bb_lo"]  = sma20 - 2 * std20
        df["bb_mid"] = sma20
        df["bb_pct"] = (c - df["bb_lo"]) / (df["bb_up"] - df["bb_lo"] + 1e-9)

        # ATR
        hl = df["high"] - df["low"]
        hc = (df["high"] - c.shift()).abs()
        lc = (df["low"]  - c.shift()).abs()
        df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

        # Volume
        df["vol_sma"] = df["volume"].rolling(20).mean()
        df["vol_ratio"] = df["volume"] / (df["vol_sma"] + 1e-9)

        # Stochastic
        low14  = df["low"].rolling(14).min()
        high14 = df["high"].rolling(14).max()
        df["stoch_k"] = 100 * (c - low14) / (high14 - low14 + 1e-9)
        df["stoch_d"] = df["stoch_k"].rolling(3).mean()

        # CCI
        tp = (df["high"] + df["low"] + c) / 3
        df["cci"] = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std() + 1e-9)

        return df

    # ── Signal Categories ─────────────────────────────────────────────────────

    def _trend_signals(self, df: pd.DataFrame) -> List[TASignal]:
        r, p = df.iloc[-1], df.iloc[-2]
        signals = []
        price = r["close"]

        # EMA alignment
        if r["ema_9"] > r["ema_21"] > r["ema_50"]:
            signals.append(TASignal("EMA_Stack", Bias.STRONG_BUY, price, "EMA 9>21>50 — bullish stack", 1.5))
        elif r["ema_9"] < r["ema_21"] < r["ema_50"]:
            signals.append(TASignal("EMA_Stack", Bias.STRONG_SELL, price, "EMA 9<21<50 — bearish stack", 1.5))

        # Golden / death cross (EMA 21 vs 50)
        if r["ema_21"] > r["ema_50"] and p["ema_21"] <= p["ema_50"]:
            signals.append(TASignal("MA_Cross", Bias.STRONG_BUY, r["ema_21"], "Golden cross EMA21/50", 1.8))
        elif r["ema_21"] < r["ema_50"] and p["ema_21"] >= p["ema_50"]:
            signals.append(TASignal("MA_Cross", Bias.STRONG_SELL, r["ema_21"], "Death cross EMA21/50", 1.8))
        elif r["ema_21"] > r["ema_50"]:
            signals.append(TASignal("MA_Bias", Bias.BUY, r["ema_21"], "Bullish MA alignment", 0.8))
        else:
            signals.append(TASignal("MA_Bias", Bias.SELL, r["ema_21"], "Bearish MA alignment", 0.8))

        return signals

    def _momentum_signals(self, df: pd.DataFrame) -> List[TASignal]:
        r, p = df.iloc[-1], df.iloc[-2]
        signals = []

        # RSI
        rsi = r["rsi"]
        if rsi < 28:
            signals.append(TASignal("RSI", Bias.STRONG_BUY, rsi, f"RSI extremely oversold: {rsi:.1f}", 1.4))
        elif rsi < 40:
            signals.append(TASignal("RSI", Bias.BUY, rsi, f"RSI oversold zone: {rsi:.1f}", 1.1))
        elif rsi > 72:
            signals.append(TASignal("RSI", Bias.STRONG_SELL, rsi, f"RSI extremely overbought: {rsi:.1f}", 1.4))
        elif rsi > 60:
            signals.append(TASignal("RSI", Bias.SELL, rsi, f"RSI overbought zone: {rsi:.1f}", 1.1))
        else:
            signals.append(TASignal("RSI", Bias.NEUTRAL, rsi, f"RSI neutral: {rsi:.1f}", 0.4))

        # MACD crossover
        if r["macd"] > r["macd_sig"] and p["macd"] <= p["macd_sig"]:
            signals.append(TASignal("MACD_Cross", Bias.STRONG_BUY, r["macd"], "MACD bullish crossover", 1.5))
        elif r["macd"] < r["macd_sig"] and p["macd"] >= p["macd_sig"]:
            signals.append(TASignal("MACD_Cross", Bias.STRONG_SELL, r["macd"], "MACD bearish crossover", 1.5))
        elif r["macd"] > 0:
            signals.append(TASignal("MACD_Pos", Bias.BUY, r["macd"], "MACD positive", 0.7))
        else:
            signals.append(TASignal("MACD_Neg", Bias.SELL, r["macd"], "MACD negative", 0.7))

        # Stochastic
        if r["stoch_k"] < 20 and r["stoch_k"] > r["stoch_d"]:
            signals.append(TASignal("Stoch", Bias.BUY, r["stoch_k"], "Stoch oversold + K>D", 1.0))
        elif r["stoch_k"] > 80 and r["stoch_k"] < r["stoch_d"]:
            signals.append(TASignal("Stoch", Bias.SELL, r["stoch_k"], "Stoch overbought + K<D", 1.0))

        # CCI
        cci = r["cci"]
        if cci < -100:
            signals.append(TASignal("CCI", Bias.BUY, cci, f"CCI oversold: {cci:.0f}", 0.8))
        elif cci > 100:
            signals.append(TASignal("CCI", Bias.SELL, cci, f"CCI overbought: {cci:.0f}", 0.8))

        return signals

    def _volatility_signals(self, df: pd.DataFrame) -> List[TASignal]:
        r = df.iloc[-1]
        signals = []
        bp = r["bb_pct"]
        if bp < 0.05:
            signals.append(TASignal("BB_Lower", Bias.STRONG_BUY, bp, "Price at lower Bollinger Band", 1.2))
        elif bp < 0.2:
            signals.append(TASignal("BB_Low", Bias.BUY, bp, "Price near lower BB", 0.8))
        elif bp > 0.95:
            signals.append(TASignal("BB_Upper", Bias.STRONG_SELL, bp, "Price at upper Bollinger Band", 1.2))
        elif bp > 0.8:
            signals.append(TASignal("BB_High", Bias.SELL, bp, "Price near upper BB", 0.8))
        return signals

    def _volume_signals(self, df: pd.DataFrame) -> List[TASignal]:
        r, p = df.iloc[-1], df.iloc[-2]
        signals = []
        vr = r["vol_ratio"]
        if vr > 2.5 and r["close"] > p["close"]:
            signals.append(TASignal("Vol_Spike", Bias.STRONG_BUY, vr, f"Bullish volume spike: {vr:.1f}x", 1.3))
        elif vr > 2.5 and r["close"] < p["close"]:
            signals.append(TASignal("Vol_Spike", Bias.STRONG_SELL, vr, f"Bearish volume spike: {vr:.1f}x", 1.3))
        elif vr > 1.5 and r["close"] > p["close"]:
            signals.append(TASignal("Vol_High", Bias.BUY, vr, f"Above-average buy volume: {vr:.1f}x", 0.7))
        return signals

    # ── Support / Resistance ──────────────────────────────────────────────────

    def _support_resistance(self, df: pd.DataFrame, window: int = 15) -> Tuple[List[float], List[float]]:
        highs = df["high"].values
        lows  = df["low"].values
        supports, resistances = [], []
        for i in range(window, len(df) - window):
            if lows[i]  == min(lows[i-window:i+window]):
                supports.append(float(lows[i]))
            if highs[i] == max(highs[i-window:i+window]):
                resistances.append(float(highs[i]))
        price = float(df["close"].iloc[-1])
        supports    = sorted(self._cluster(supports))
        resistances = sorted(self._cluster(resistances))
        below = sorted([s for s in supports    if s < price], reverse=True)[:4]
        above = sorted([r for r in resistances if r > price])[:4]
        return below, above

    def _cluster(self, levels: List[float], tol: float = 0.003) -> List[float]:
        if not levels:
            return []
        levels = sorted(levels)
        out = [levels[0]]
        for lv in levels[1:]:
            if abs(lv - out[-1]) / (out[-1] + 1e-9) > tol:
                out.append(lv)
        return out

    # ── Fibonacci ─────────────────────────────────────────────────────────────

    def _fibonacci(self, df: pd.DataFrame, period: int = 100) -> Dict:
        rec = df.tail(period)
        hi  = float(rec["high"].max())
        lo  = float(rec["low"].min())
        diff = hi - lo
        return {
            f"{int(r*100)}%": round(hi - diff * r, 6)
            for r in [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        }

    # ── Pattern Recognition ───────────────────────────────────────────────────

    def _patterns(self, df: pd.DataFrame) -> List[Dict]:
        patterns = []
        r, p = df.iloc[-1], df.iloc[-2]

        body = abs(r["close"] - r["open"])
        upper_wick = r["high"] - max(r["close"], r["open"])
        lower_wick = min(r["close"], r["open"]) - r["low"]
        total = r["high"] - r["low"]

        # Doji
        if total > 0 and body / total < 0.08:
            patterns.append({"name": "Doji", "signal": "NEUTRAL", "desc": "Indecision — potential reversal"})
        # Hammer
        if lower_wick > 2 * body and upper_wick < 0.3 * body and r["close"] > r["open"]:
            patterns.append({"name": "Hammer", "signal": "BUY", "desc": "Bullish reversal after downtrend"})
        # Shooting Star
        if upper_wick > 2 * body and lower_wick < 0.3 * body and r["close"] < r["open"]:
            patterns.append({"name": "Shooting Star", "signal": "SELL", "desc": "Bearish reversal after uptrend"})
        # Bullish Engulfing
        if (r["close"] > r["open"] and p["close"] < p["open"] and
                r["close"] > p["open"] and r["open"] < p["close"]):
            patterns.append({"name": "Bullish Engulfing", "signal": "STRONG_BUY", "desc": "Strong bullish reversal"})
        # Bearish Engulfing
        if (r["close"] < r["open"] and p["close"] > p["open"] and
                r["close"] < p["open"] and r["open"] > p["close"]):
            patterns.append({"name": "Bearish Engulfing", "signal": "STRONG_SELL", "desc": "Strong bearish reversal"})
        # Marubozu
        if total > 0 and body / total > 0.9:
            sig = "STRONG_BUY" if r["close"] > r["open"] else "STRONG_SELL"
            patterns.append({"name": "Marubozu", "signal": sig, "desc": "High-conviction directional candle"})

        # Chart structure patterns (last 30 bars)
        closes = df["close"].values[-30:]
        highs  = df["high"].values[-30:]
        lows   = df["low"].values[-30:]
        n = len(closes)
        if n >= 20:
            high_slope = float(np.polyfit(range(n), highs, 1)[0])
            low_slope  = float(np.polyfit(range(n), lows,  1)[0])
            if high_slope < -0.001 and low_slope > 0.001:
                patterns.append({"name": "Symmetrical Triangle", "signal": "NEUTRAL", "desc": "Breakout imminent"})
            elif high_slope < -0.001 and abs(low_slope) < 0.0005:
                patterns.append({"name": "Descending Triangle", "signal": "SELL", "desc": "Bearish continuation"})
            elif low_slope > 0.001 and abs(high_slope) < 0.0005:
                patterns.append({"name": "Ascending Triangle", "signal": "BUY", "desc": "Bullish continuation"})

        return patterns

    # ── Market Structure ──────────────────────────────────────────────────────

    def _market_structure(self, df: pd.DataFrame) -> Dict:
        highs  = df["high"].values[-30:]
        lows   = df["low"].values[-30:]
        closes = df["close"].values[-20:]

        hh = bool(highs[-1] > np.max(highs[:-1]))
        hl = bool(lows[-1]  > np.min(lows[:-1]))
        lh = bool(highs[-1] < np.max(highs[:-1]))
        ll = bool(lows[-1]  < np.min(lows[:-1]))

        if hh and hl:
            structure, bias = "UPTREND", "BULLISH"
        elif lh and ll:
            structure, bias = "DOWNTREND", "BEARISH"
        else:
            structure, bias = "RANGING", "NEUTRAL"

        momentum = float(np.mean(np.diff(closes[-10:])))

        return {
            "structure": structure,
            "bias": bias,
            "hh": hh, "hl": hl, "lh": lh, "ll": ll,
            "momentum": round(momentum, 5),
        }

    # ── Composite Score ───────────────────────────────────────────────────────

    def _score(self, signals: List[TASignal]) -> float:
        """Returns -1.0 (strong sell) to +1.0 (strong buy)."""
        if not signals:
            return 0.0
        bias_map = {Bias.STRONG_BUY: 1.0, Bias.BUY: 0.5,
                    Bias.NEUTRAL: 0.0, Bias.SELL: -0.5, Bias.STRONG_SELL: -1.0}
        total_w  = sum(s.weight for s in signals)
        weighted = sum(bias_map[s.bias] * s.weight for s in signals)
        return weighted / (total_w + 1e-9)
