"""
Backtesting Engine — Vectorized strategy simulation with institutional metrics
"""
import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    pair: str
    direction: str
    entry: float
    exit: float
    sl: float
    tp: float
    pnl: float
    pnl_pct: float
    rr: float
    exit_reason: str


@dataclass
class BacktestResult:
    strategy: str
    pair: str
    timeframe: str
    start: str
    end: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    sharpe: float
    sortino: float
    calmar: float
    avg_win_pct: float
    avg_loss_pct: float
    best_trade_pct: float
    worst_trade_pct: float
    equity_curve: List[float] = field(default_factory=list)
    trades: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["win_rate"] = round(d["win_rate"] * 100, 1)
        d["equity_curve"] = d["equity_curve"][:100]  # truncate for API
        return d


class BacktestEngine:

    def __init__(self, initial_capital: float = 10000.0):
        self.capital = initial_capital

    def run(self, df: pd.DataFrame, pair: str, strategy: str = "TrendMomentum",
            timeframe: str = "1h") -> BacktestResult:
        df = self._indicators(df.copy())
        df = self._signals(df, strategy)
        trades, equity = self._simulate(df, pair)
        return self._metrics(trades, equity, pair, strategy, timeframe, df)

    def _indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        c = df["close"]
        df["ema9"]  = c.ewm(span=9,  adjust=False).mean()
        df["ema21"] = c.ewm(span=21, adjust=False).mean()
        df["ema50"] = c.ewm(span=50, adjust=False).mean()

        delta = c.diff()
        g = delta.clip(lower=0).rolling(14).mean()
        l = (-delta.clip(upper=0)).rolling(14).mean()
        df["rsi"] = 100 - 100 / (1 + g / (l + 1e-9))

        df["macd"] = c.ewm(span=12).mean() - c.ewm(span=26).mean()
        df["macd_sig"] = df["macd"].ewm(span=9).mean()

        hl = df["high"] - df["low"]
        hc = (df["high"] - c.shift()).abs()
        lc = (df["low"]  - c.shift()).abs()
        df["atr"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

        sma = c.rolling(20).mean()
        std = c.rolling(20).std()
        df["bb_up"] = sma + 2 * std
        df["bb_lo"] = sma - 2 * std

        return df.dropna()

    def _signals(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        df["sig"] = 0
        if strategy == "TrendMomentum":
            long  = (df["ema9"] > df["ema21"]) & (df["rsi"] > 50) & (df["rsi"] < 70) & (df["macd"] > df["macd_sig"])
            short = (df["ema9"] < df["ema21"]) & (df["rsi"] < 50) & (df["rsi"] > 30) & (df["macd"] < df["macd_sig"])
        elif strategy == "MeanReversion":
            long  = df["rsi"] < 30
            short = df["rsi"] > 70
        elif strategy == "BreakoutMA":
            long  = (df["close"] > df["ema50"]) & (df["close"].shift() <= df["ema50"].shift())
            short = (df["close"] < df["ema50"]) & (df["close"].shift() >= df["ema50"].shift())
        else:
            long  = df["close"] > df["ema50"]
            short = df["close"] < df["ema50"]
        df.loc[long,  "sig"] =  1
        df.loc[short, "sig"] = -1
        return df

    def _simulate(self, df: pd.DataFrame, pair: str):
        capital = self.capital
        equity  = [capital]
        trades: List[Trade] = []
        in_trade = False
        te = {}

        for i in range(1, len(df)):
            row   = df.iloc[i]
            prev  = df.iloc[i-1]

            if not in_trade and prev["sig"] != 0:
                atr    = max(float(row["atr"]), 1e-8)
                entry  = float(row["open"])
                direction = "LONG" if prev["sig"] == 1 else "SHORT"
                sl = entry - 1.5 * atr if direction == "LONG" else entry + 1.5 * atr
                tp = entry + 3.5 * atr if direction == "LONG" else entry - 3.5 * atr
                units  = (capital * 0.01) / abs(entry - sl)
                te     = {"entry": entry, "sl": sl, "tp": tp, "dir": direction, "units": units}
                in_trade = True

            elif in_trade:
                price  = float(row["close"])
                reason = None
                if te["dir"] == "LONG":
                    if price <= te["sl"]: reason = "SL_HIT"
                    elif price >= te["tp"]: reason = "TP_HIT"
                else:
                    if price >= te["sl"]: reason = "SL_HIT"
                    elif price <= te["tp"]: reason = "TP_HIT"

                if reason:
                    if te["dir"] == "LONG":
                        pnl = (price - te["entry"]) * te["units"]
                    else:
                        pnl = (te["entry"] - price) * te["units"]
                    pnl_pct = pnl / capital
                    capital += pnl
                    rr = abs(te["tp"] - te["entry"]) / (abs(te["sl"] - te["entry"]) + 1e-9)
                    trades.append(Trade(pair, te["dir"], te["entry"], price, te["sl"], te["tp"],
                                        round(pnl, 2), round(pnl_pct, 4), round(rr, 2), reason))
                    in_trade = False
                    equity.append(round(capital, 2))

        return trades, equity

    def _metrics(self, trades, equity, pair, strategy, timeframe, df) -> BacktestResult:
        null = BacktestResult(strategy, pair, timeframe, str(df.index[0])[:10],
                              str(df.index[-1])[:10], self.capital, self.capital,
                              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, [self.capital], [])
        if not trades:
            return null

        final = equity[-1] if equity else self.capital
        wins  = [t for t in trades if t.pnl > 0]
        loss  = [t for t in trades if t.pnl <= 0]

        gp = sum(t.pnl for t in wins)
        gl = abs(sum(t.pnl for t in loss))
        pf = gp / (gl + 1e-9)

        eq = np.array(equity)
        peak = np.maximum.accumulate(eq)
        dd = (peak - eq) / (peak + 1e-9)
        max_dd = float(dd.max())

        rets = np.diff(eq) / (eq[:-1] + 1e-9)
        if len(rets) > 1 and rets.std() > 0:
            sharpe = float(rets.mean() / rets.std() * np.sqrt(8760))
        else:
            sharpe = 0.0
        neg = rets[rets < 0]
        sortino = float(rets.mean() / neg.std() * np.sqrt(8760)) if len(neg) > 1 and neg.std() > 0 else 0.0
        total_ret = (final - self.capital) / self.capital
        calmar = total_ret / (max_dd + 1e-9)

        return BacktestResult(
            strategy=strategy, pair=pair, timeframe=timeframe,
            start=str(df.index[0])[:10], end=str(df.index[-1])[:10],
            initial_capital=self.capital, final_capital=round(final, 2),
            total_return_pct=round(total_ret * 100, 2),
            total_trades=len(trades), wins=len(wins), losses=len(loss),
            win_rate=len(wins) / len(trades),
            profit_factor=round(pf, 2), max_drawdown_pct=round(max_dd * 100, 2),
            sharpe=round(sharpe, 2), sortino=round(sortino, 2), calmar=round(calmar, 2),
            avg_win_pct=round(np.mean([t.pnl_pct for t in wins]) * 100, 2) if wins else 0,
            avg_loss_pct=round(np.mean([t.pnl_pct for t in loss]) * 100, 2) if loss else 0,
            best_trade_pct=round(max(t.pnl_pct for t in trades) * 100, 2),
            worst_trade_pct=round(min(t.pnl_pct for t in trades) * 100, 2),
            equity_curve=equity,
            trades=[t.__dict__ for t in trades[-50:]],
        )
