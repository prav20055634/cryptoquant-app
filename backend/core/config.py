"""Platform configuration — all settings in one place"""
import os
from typing import List


class Settings:
    APP_NAME: str = "CryptoQuant AI Platform"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Exchange APIs (free read-only tiers)
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY: str = os.getenv("BINANCE_SECRET_KEY", "")

    # Trading pairs to scan
    TRADING_PAIRS: List[str] = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
        "XRPUSDT", "DOTUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT",
    ]

    # Risk parameters
    MAX_RISK_PER_TRADE: float = 0.01        # 1%
    MIN_RISK_REWARD_RATIO: float = 2.0
    MAX_DAILY_DRAWDOWN: float = 0.05        # 5%
    MIN_CONFIDENCE_SCORE: float = 0.65      # 65% minimum
    DEFAULT_ACCOUNT_BALANCE: float = 10000.0

    # Timeframes
    TIMEFRAMES: List[str] = ["1m", "5m", "15m", "1h", "4h", "1d"]

    # Scheduler intervals (seconds)
    MARKET_DATA_INTERVAL: int = 60          # Collect data every 60s
    SIGNAL_SCAN_INTERVAL: int = 300         # Scan signals every 5 min
    BACKTEST_INTERVAL: int = 3600           # Backtest every hour
    ML_OPTIMIZE_INTERVAL: int = 86400       # Optimize every 24h

    # Signal storage (in-memory ring buffer)
    MAX_SIGNALS_STORED: int = 200

    # Binance base URL (no auth needed for public endpoints)
    BINANCE_BASE_URL: str = "https://api.binance.com/api/v3"
    COINGECKO_BASE_URL: str = "https://api.coingecko.com/api/v3"
    FEAR_GREED_URL: str = "https://api.alternative.me/fng/?limit=1"


settings = Settings()
