"""Risk Management System — enforces all trading rules"""
import logging
from dataclasses import dataclass
from typing import Tuple
from backend.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PositionResult:
    pair: str
    entry: float
    stop_loss: float
    take_profit: float
    account_balance: float
    risk_amount: float
    units: float
    position_value: float
    risk_percent: float
    risk_reward: float
    approved: bool
    reason: str = "OK"


class RiskManager:

    def __init__(self):
        self._daily_pnl: float = 0.0
        self._trades_today: int = 0

    def validate_and_size(
        self,
        pair: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        balance: float = settings.DEFAULT_ACCOUNT_BALANCE,
    ) -> PositionResult:
        sl_dist = abs(entry - stop_loss)
        tp_dist = abs(take_profit - entry)

        if sl_dist <= 0:
            return PositionResult(pair, entry, stop_loss, take_profit, balance,
                                  0, 0, 0, 0, 0, False, "Stop loss distance is zero")

        rr = tp_dist / sl_dist
        if rr < settings.MIN_RISK_REWARD_RATIO:
            return PositionResult(pair, entry, stop_loss, take_profit, balance,
                                  0, 0, 0, 0, round(rr, 2), False,
                                  f"R/R {rr:.2f} below minimum {settings.MIN_RISK_REWARD_RATIO}")

        dd_limit = -settings.MAX_DAILY_DRAWDOWN * balance
        if self._daily_pnl < dd_limit:
            return PositionResult(pair, entry, stop_loss, take_profit, balance,
                                  0, 0, 0, 0, round(rr, 2), False,
                                  "Daily drawdown limit reached — trading paused")

        risk_amount = balance * settings.MAX_RISK_PER_TRADE
        units = risk_amount / sl_dist
        position_value = units * entry

        return PositionResult(
            pair=pair,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            account_balance=balance,
            risk_amount=round(risk_amount, 2),
            units=round(units, 6),
            position_value=round(position_value, 2),
            risk_percent=round(settings.MAX_RISK_PER_TRADE * 100, 1),
            risk_reward=round(rr, 2),
            approved=True,
        )

    def record_trade(self, pnl: float):
        self._daily_pnl += pnl
        self._trades_today += 1

    def reset_daily(self):
        self._daily_pnl = 0.0
        self._trades_today = 0

    def get_status(self) -> dict:
        return {
            "daily_pnl": round(self._daily_pnl, 2),
            "trades_today": self._trades_today,
            "max_risk_per_trade": f"{settings.MAX_RISK_PER_TRADE * 100:.1f}%",
            "min_risk_reward": settings.MIN_RISK_REWARD_RATIO,
            "max_daily_drawdown": f"{settings.MAX_DAILY_DRAWDOWN * 100:.1f}%",
            "min_confidence": f"{settings.MIN_CONFIDENCE_SCORE * 100:.0f}%",
            "trading_allowed": self._daily_pnl > -settings.MAX_DAILY_DRAWDOWN * settings.DEFAULT_ACCOUNT_BALANCE,
        }
