# ⚡ CryptoQuant AI Trading Platform

Institutional-grade AI crypto trading signals platform.  
**Signals display IN the app — no Telegram required.**

---

## ✅ Version Requirements

| Tool | Minimum | Recommended | Notes |
|------|---------|-------------|-------|
| Python | 3.11 | **3.11 or 3.12** | 3.14 is pre-release, avoid for production |
| Node.js | 18 | 20+ | For React frontend |
| npm | 9 | 10+ | Comes with Node.js |
| Git | Any | Any | For cloning |

---

## 🔍 Step 1: Check Your Versions (Run in CMD / Terminal)

### Windows CMD:
```cmd
python --version
py -3.11 --version
py -3.12 --version
py -3.14 --version
node --version
npm --version
pip --version
git --version
```

### Mac / Linux Terminal:
```bash
python3 --version
python3.11 --version
python3.12 --version
python3.14 --version
node --version
npm --version
pip3 --version
git --version
```

### Or run the included script:
```cmd
# Windows:
scripts\check_versions.bat

# Mac/Linux:
bash scripts/check_versions.sh
```

---

## 📦 Step 2: Install Dependencies

### Backend (Python):
```cmd
# Windows — use Python 3.11 (recommended):
py -3.11 -m pip install -r requirements.txt

# Windows — use Python 3.12:
py -3.12 -m pip install -r requirements.txt

# Mac/Linux:
python3.11 -m pip install -r requirements.txt
# OR
pip3 install -r requirements.txt
```

### Frontend (Node.js):
```cmd
cd frontend
npm install
cd ..
```

---

## 🚀 Step 3: Start the Platform

### Terminal 1 — Backend:
```cmd
# Windows with Python 3.11:
py -3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Windows with Python 3.12:
py -3.12 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Mac/Linux:
python3.11 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Generic (if python in PATH):
uvicorn backend.main:app --reload --port 8000
```

### Terminal 2 — Frontend:
```cmd
cd frontend
npm run dev
```

---

## 🌐 Access the App

| URL | What |
|-----|------|
| http://localhost:3000 | **Trading Dashboard (React app)** |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/api/v1/signals/ | Signals JSON |
| http://localhost:8000/health | Health check |

---

## 🔑 API Keys (Optional)

The platform works **without any API keys** using synthetic market data.  
For live market prices, add Binance API keys (free, read-only) to `.env`:

```env
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_secret_here
```

Get free keys at: https://binance.com → API Management → Create (enable Read-only only)

---

## 📁 Project Structure

```
cryptoquant_app/
├── backend/
│   ├── main.py                    ← FastAPI app entry point
│   ├── core/
│   │   ├── config.py              ← Settings & trading params
│   │   ├── store.py               ← In-memory signal storage
│   │   └── scheduler.py           ← 24/7 background task runner
│   ├── api/
│   │   ├── signals.py             ← Signal endpoints
│   │   ├── market.py              ← Market data endpoints
│   │   ├── backtest.py            ← Backtesting endpoints
│   │   ├── risk.py                ← Risk management endpoints
│   │   ├── strategies.py          ← Strategy info endpoints
│   │   └── analytics.py           ← Analytics endpoints
│   ├── services/
│   │   ├── market_data/
│   │   │   └── collector.py       ← Binance + CoinGecko data
│   │   ├── technical_analysis/
│   │   │   └── indicators.py      ← 30+ TA indicators
│   │   └── signal_engine/
│   │       └── generator.py       ← 7-algorithm signal engine
│   ├── risk/
│   │   └── manager.py             ← Position sizing & risk rules
│   ├── backtest/
│   │   └── engine.py              ← Historical backtesting
│   └── ml/
│       └── optimization/
│           └── optimizer.py       ← Genetic + Bayesian ML
├── frontend/
│   ├── src/App.jsx                ← Complete React dashboard
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── check_versions.bat         ← Windows version checker
│   ├── check_versions.sh          ← Mac/Linux version checker
│   ├── start_backend.bat          ← Windows backend starter
│   └── start_frontend.bat         ← Windows frontend starter
├── requirements.txt               ← Python dependencies
├── .env                           ← API keys (optional)
└── README.md                      ← This file
```

---

## 🤖 What the App Does

| Feature | Description |
|---------|-------------|
| **Signal Dashboard** | Displays all AI-generated signals in real-time |
| **7-Algorithm Engine** | TrendFollow, MeanReversion, Momentum, Breakout, MarketStructure, PatternRecog, ML Score |
| **Multi-Confirmation** | Minimum 3 of 7 algorithms must agree before signal is shown |
| **Risk Calculator** | Auto-computes position size, shows R/R ratio and risk % |
| **Market Prices** | Live ticker for 10 pairs, Fear & Greed index |
| **Backtesting** | Test 4 strategies on historical data, view equity curve |
| **ML Optimization** | Genetic algorithm tunes parameters every 24 hours |
| **Auto-Scan** | Scans all pairs every 5 minutes automatically |
| **Signal Detail** | Click any signal for full breakdown with algo confirmations |

---

## ⚠️ Python 3.14 Note

Python 3.14 is currently **pre-release (alpha/beta)**. Many packages like `pandas` and `numpy`
may not have stable wheels for 3.14 yet.

**Recommendation:**
- Use **Python 3.11** (most stable, all packages support it)
- Or **Python 3.12** (stable, excellent compatibility)
- Avoid 3.14 for production until final release (~October 2025)

---

## 🛠 Troubleshooting

**"Module not found" error:**
```cmd
py -3.11 -m pip install -r requirements.txt
py -3.11 -m uvicorn backend.main:app --reload
```

**CORS error in browser:**
Backend must be running on port 8000. Check Terminal 1 shows "Application startup complete."

**No signals showing:**
Click "⚡ Scan Now" button in the sidebar. The platform uses synthetic data if Binance is unreachable.

**npm install fails:**
```cmd
node --version    # Must be 18+
npm cache clean --force
npm install
```
