import { useState, useEffect, useCallback, useRef } from "react";

const API = "http://localhost:8000/api/v1";

// ── Utility helpers ───────────────────────────────────────────────────────────
const fmt = (n, d = 2) => typeof n === "number" ? n.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d }) : "—";
const fmtPct = (n) => `${n >= 0 ? "+" : ""}${fmt(n)}%`;
const timeAgo = (iso) => {
  if (!iso) return "—";
  const s = Math.floor((Date.now() - new Date(iso)) / 1000);
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
};

// ── Design tokens ─────────────────────────────────────────────────────────────
const C = {
  bg: "#07080f",
  surface: "#0e1018",
  card: "#13151f",
  cardHover: "#181b27",
  border: "#1e2133",
  borderLight: "#252840",
  accent: "#00d4aa",
  accentDim: "#00d4aa22",
  accentHover: "#00efc0",
  long: "#00d4aa",
  longDim: "#00d4aa18",
  short: "#ff4c6a",
  shortDim: "#ff4c6a18",
  text: "#e8eaf0",
  textMuted: "#6b7280",
  textDim: "#3d4253",
  purple: "#8b5cf6",
  purpleDim: "#8b5cf618",
  gold: "#f59e0b",
  goldDim: "#f59e0b18",
  neutral: "#60a5fa",
};

// ── Global CSS injector ───────────────────────────────────────────────────────
const injectGlobalCSS = () => {
  const id = "cq-globals";
  if (document.getElementById(id)) return;
  const s = document.createElement("style");
  s.id = id;
  s.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');
    *{box-sizing:border-box;margin:0;padding:0;}
    body{background:${C.bg};color:${C.text};font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;}
    ::-webkit-scrollbar{width:4px;height:4px}
    ::-webkit-scrollbar-track{background:${C.surface}}
    ::-webkit-scrollbar-thumb{background:${C.border};border-radius:2px}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
    @keyframes slideIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
    @keyframes glow{0%,100%{box-shadow:0 0 8px ${C.accent}33}50%{box-shadow:0 0 20px ${C.accent}66}}
    @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
    @keyframes fadeIn{from{opacity:0}to{opacity:1}}
    .slide-in{animation:slideIn .25s ease forwards}
    .pulse{animation:pulse 2s infinite}
    .spin{animation:spin 1s linear infinite}
  `;
  document.head.appendChild(s);
};

// ── Reusable components ───────────────────────────────────────────────────────

function Badge({ children, color = C.accent, bg }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4,
      padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700,
      fontFamily: "'Space Mono', monospace", letterSpacing: ".04em",
      color, background: bg || color + "22", border: `1px solid ${color}33`,
    }}>{children}</span>
  );
}

function Card({ children, style = {}, glow = false, onClick }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: hover && onClick ? C.cardHover : C.card,
        border: `1px solid ${hover ? C.borderLight : C.border}`,
        borderRadius: 12,
        padding: 20,
        transition: "all .2s",
        cursor: onClick ? "pointer" : "default",
        boxShadow: glow ? `0 0 24px ${C.accent}22` : "none",
        ...style,
      }}
    >{children}</div>
  );
}

function StatBox({ label, value, sub, color = C.accent, icon }) {
  return (
    <Card style={{ textAlign: "center", padding: "16px 12px" }}>
      {icon && <div style={{ fontSize: 20, marginBottom: 6 }}>{icon}</div>}
      <div style={{ color, fontSize: 22, fontWeight: 700, fontFamily: "'Space Mono', monospace" }}>{value}</div>
      <div style={{ color: C.text, fontSize: 12, fontWeight: 600, marginTop: 4 }}>{label}</div>
      {sub && <div style={{ color: C.textMuted, fontSize: 10, marginTop: 2 }}>{sub}</div>}
    </Card>
  );
}

function Spinner({ size = 18 }) {
  return <div className="spin" style={{ width: size, height: size, border: `2px solid ${C.border}`, borderTopColor: C.accent, borderRadius: "50%" }} />;
}

function LiveDot() {
  return <span className="pulse" style={{ display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: C.long, marginRight: 6 }} />;
}

function ConfBar({ value }) {
  const color = value >= 80 ? C.long : value >= 65 ? C.gold : C.short;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 4, background: C.border, borderRadius: 2 }}>
        <div style={{ height: "100%", width: `${value}%`, background: color, borderRadius: 2, transition: "width .4s" }} />
      </div>
      <span style={{ fontSize: 11, fontWeight: 700, color, fontFamily: "'Space Mono', monospace", minWidth: 34 }}>{value}%</span>
    </div>
  );
}

// ── Signal Card ───────────────────────────────────────────────────────────────

function SignalCard({ sig, onSelect }) {
  const isLong = sig.signal_type === "LONG";
  const color  = isLong ? C.long : C.short;
  const dim    = isLong ? C.longDim : C.shortDim;

  return (
    <div
      className="slide-in"
      onClick={() => onSelect(sig)}
      style={{
        background: C.card,
        border: `1px solid ${color}44`,
        borderLeft: `3px solid ${color}`,
        borderRadius: 10,
        padding: "14px 16px",
        cursor: "pointer",
        transition: "all .18s",
        marginBottom: 8,
        position: "relative",
        overflow: "hidden",
      }}
      onMouseEnter={e => { e.currentTarget.style.background = C.cardHover; e.currentTarget.style.borderColor = color + "88"; }}
      onMouseLeave={e => { e.currentTarget.style.background = C.card; e.currentTarget.style.borderColor = color + "44"; }}
    >
      <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: "100%", background: `linear-gradient(90deg, transparent, ${dim})`, pointerEvents: "none" }} />
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 15, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: C.text }}>{sig.pair.replace("USDT", "")}<span style={{ color: C.textMuted, fontWeight: 400 }}>/USDT</span></span>
          <Badge color={color}>{sig.signal_type}</Badge>
          {sig.pattern && sig.pattern !== "—" && <Badge color={C.purple}>{sig.pattern.split(",")[0]}</Badge>}
        </div>
        <span style={{ fontSize: 10, color: C.textMuted }}>{timeAgo(sig.timestamp)}</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 10 }}>
        {[
          { l: "Entry",       v: fmt(sig.entry_price, 4), c: C.text },
          { l: "Take Profit", v: fmt(sig.take_profit, 4), c: C.long },
          { l: "Stop Loss",   v: fmt(sig.stop_loss, 4),   c: C.short },
        ].map(({ l, v, c }) => (
          <div key={l}>
            <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 2 }}>{l}</div>
            <div style={{ fontSize: 13, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: c }}>{v}</div>
          </div>
        ))}
      </div>
      <ConfBar value={sig.confidence_score} />
      <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
        {sig.algorithms_confirmed?.map(a => <Badge key={a} color={C.purple} bg={C.purpleDim}>{a}</Badge>)}
        <Badge color={C.neutral}>R/R 1:{sig.risk_reward}</Badge>
        <Badge color={C.textMuted}>{sig.market_structure}</Badge>
      </div>
    </div>
  );
}

// ── Signal Detail Modal ───────────────────────────────────────────────────────

function SignalModal({ sig, onClose }) {
  if (!sig) return null;
  const isLong = sig.signal_type === "LONG";
  const color = isLong ? C.long : C.short;

  useEffect(() => {
    const handler = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      style={{ position: "fixed", inset: 0, background: "#00000099", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}
      onClick={e => e.target === e.currentTarget && onClose()}
    >
      <div className="slide-in" style={{ background: C.card, border: `1px solid ${color}55`, borderRadius: 16, padding: 28, width: "100%", maxWidth: 520, maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <div>
            <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 20, color: C.text }}>{sig.pair}</h2>
            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <Badge color={color}>{sig.signal_type}</Badge>
              <Badge color={C.neutral}>{sig.timeframe}</Badge>
              <Badge color={sig.confidence_score >= 80 ? C.long : C.gold}>{sig.confidence_score}% confidence</Badge>
            </div>
          </div>
          <button onClick={onClose} style={{ background: C.border, border: "none", color: C.text, width: 32, height: 32, borderRadius: 8, cursor: "pointer", fontSize: 16 }}>✕</button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
          {[
            { l: "Entry Price",   v: fmt(sig.entry_price, 6),   c: C.text },
            { l: "Take Profit",   v: fmt(sig.take_profit, 6),   c: C.long },
            { l: "Stop Loss",     v: fmt(sig.stop_loss, 6),     c: C.short },
            { l: "Risk/Reward",   v: `1 : ${sig.risk_reward}`,  c: C.neutral },
            { l: "Risk",          v: `${sig.risk_percent}% of balance`, c: C.gold },
            { l: "Structure",     v: sig.market_structure,      c: C.purple },
          ].map(({ l, v, c }) => (
            <div key={l} style={{ background: C.surface, borderRadius: 8, padding: "12px 14px" }}>
              <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>{l}</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: c }}>{v}</div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8, fontWeight: 600, letterSpacing: ".06em" }}>ALGORITHM CONFIRMATIONS</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {sig.algorithms_confirmed?.map(a => <Badge key={a} color={C.purple} bg={C.purpleDim}>{a}</Badge>)}
          </div>
        </div>

        {sig.pattern && sig.pattern !== "—" && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8, fontWeight: 600, letterSpacing: ".06em" }}>PATTERNS DETECTED</div>
            <Badge color={C.gold}>{sig.pattern}</Badge>
          </div>
        )}

        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 8, fontWeight: 600, letterSpacing: ".06em" }}>CONFIDENCE SCORE</div>
          <ConfBar value={sig.confidence_score} />
        </div>

        <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 4 }}>Signal ID: <code style={{ color: C.accent }}>{sig.id}</code></div>
        <div style={{ fontSize: 11, color: C.textMuted }}>Generated: {new Date(sig.timestamp).toLocaleString()}</div>

        <div style={{ marginTop: 20, padding: "10px 14px", background: "#f59e0b11", border: "1px solid #f59e0b33", borderRadius: 8 }}>
          <div style={{ fontSize: 10, color: C.gold }}>⚠ NOT FINANCIAL ADVICE — Always conduct your own research and use proper risk management.</div>
        </div>
      </div>
    </div>
  );
}

// ── Market Ticker Row ─────────────────────────────────────────────────────────

function TickerRow({ pair, data }) {
  const up = data?.change_24h >= 0;
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 0", borderBottom: `1px solid ${C.border}` }}>
      <div>
        <span style={{ fontWeight: 600, fontSize: 13 }}>{pair.replace("USDT", "")}<span style={{ color: C.textMuted, fontWeight: 400, fontSize: 11 }}>/USDT</span></span>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 13, fontWeight: 700 }}>${fmt(data?.price, 4)}</div>
        <div style={{ fontSize: 11, color: up ? C.long : C.short, fontWeight: 600 }}>{fmtPct(data?.change_24h ?? 0)}</div>
      </div>
    </div>
  );
}

// ── Backtest Result Card ──────────────────────────────────────────────────────

function BacktestCard({ result }) {
  const positive = result.total_return_pct >= 0;
  return (
    <Card style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div>
          <span style={{ fontWeight: 700, fontFamily: "'Space Mono', monospace" }}>{result.pair}</span>
          <span style={{ color: C.textMuted, fontSize: 11, marginLeft: 8 }}>{result.strategy}</span>
        </div>
        <Badge color={positive ? C.long : C.short}>{fmtPct(result.total_return_pct)}</Badge>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
        {[
          { l: "Win Rate",      v: `${result.win_rate}%`,          c: result.win_rate >= 50 ? C.long : C.short },
          { l: "Profit Factor", v: fmt(result.profit_factor),       c: result.profit_factor >= 1.5 ? C.long : C.gold },
          { l: "Sharpe",        v: fmt(result.sharpe),              c: result.sharpe >= 1 ? C.long : C.gold },
          { l: "Max DD",        v: `${fmt(result.max_drawdown_pct)}%`, c: result.max_drawdown_pct > 20 ? C.short : C.gold },
          { l: "Trades",        v: result.total_trades,             c: C.text },
          { l: "Sortino",       v: fmt(result.sortino),             c: result.sortino >= 1.5 ? C.long : C.text },
        ].map(({ l, v, c }) => (
          <div key={l} style={{ background: C.surface, borderRadius: 6, padding: "8px 10px" }}>
            <div style={{ fontSize: 9, color: C.textMuted, marginBottom: 2 }}>{l}</div>
            <div style={{ fontSize: 13, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: c }}>{v}</div>
          </div>
        ))}
      </div>
      {result.equity_curve?.length > 2 && (
        <div style={{ marginTop: 12 }}>
          <MiniChart data={result.equity_curve} color={positive ? C.long : C.short} />
        </div>
      )}
    </Card>
  );
}

// ── Mini SVG Chart ────────────────────────────────────────────────────────────

function MiniChart({ data, color = C.long, height = 44 }) {
  if (!data || data.length < 2) return null;
  const w = 320, h = height;
  const mn = Math.min(...data), mx = Math.max(...data);
  const range = mx - mn || 1;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - mn) / range) * (h - 4) - 2;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width="100%" viewBox={`0 0 ${w} ${h}`} style={{ display: "block" }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
      <polyline points={`0,${h} ${pts} ${w},${h}`} fill={`${color}18`} stroke="none" />
    </svg>
  );
}

// ── Strategy Info Panel ───────────────────────────────────────────────────────

function StrategyPanel() {
  const strategies = [
    { n: 1, name: "Trend Following",    desc: "EMA 9>21>50 stack • Higher highs/lows structure",   color: C.long },
    { n: 2, name: "Mean Reversion",     desc: "RSI < 35 oversold • Bollinger Band lower touch",    color: C.neutral },
    { n: 3, name: "Momentum",           desc: "MACD crossover • RSI 50-70 • Volume 1.3x+",         color: C.purple },
    { n: 4, name: "Breakout Detection", desc: "Price within 0.8% of resistance • Vol confirm",     color: C.gold },
    { n: 5, name: "Market Structure",   desc: "HH/HL = uptrend • LH/LL = downtrend analysis",      color: C.accent },
    { n: 6, name: "Pattern Recog.",     desc: "Engulfing • Hammer • Triangle • Marubozu AI scan",  color: C.short },
    { n: 7, name: "ML Optimizer",       desc: "Genetic algorithm • Bayesian tuning • 24h retrain", color: C.textMuted },
  ];
  return (
    <div>
      <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 12 }}>7 ACTIVE ALGORITHMS</div>
      {strategies.map(s => (
        <div key={s.n} style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "10px 0", borderBottom: `1px solid ${C.border}` }}>
          <div style={{ width: 24, height: 24, borderRadius: 6, background: s.color + "22", border: `1px solid ${s.color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 700, color: s.color, flexShrink: 0, fontFamily: "'Space Mono', monospace" }}>{s.n}</div>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: C.text }}>{s.name}</div>
            <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2 }}>{s.desc}</div>
          </div>
        </div>
      ))}
      <div style={{ marginTop: 14, padding: "10px 12px", background: C.accentDim, borderRadius: 8, border: `1px solid ${C.accent}33` }}>
        <div style={{ fontSize: 10, color: C.accent, fontWeight: 600 }}>Signal requires 3 of 7 algorithms to confirm + 65%+ confidence + 1:2 min R/R</div>
      </div>
    </div>
  );
}

// ── Risk Panel ────────────────────────────────────────────────────────────────

function RiskPanel({ status }) {
  const rules = [
    { l: "Max Risk Per Trade", v: "1.0%",    desc: "Of account balance per signal" },
    { l: "Min Risk / Reward",  v: "1 : 2",   desc: "Minimum to generate signal" },
    { l: "Max Daily Drawdown", v: "5.0%",    desc: "Auto-pause trading if exceeded" },
    { l: "Min Confidence",     v: "65%",     desc: "Algo agreement score threshold" },
    { l: "Stop Loss",          v: "1.5x ATR", desc: "Average True Range based" },
    { l: "Take Profit",        v: "3.5x ATR", desc: "Guaranteed 1:2.3+ R/R ratio" },
  ];
  return (
    <div>
      <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 12 }}>RISK PARAMETERS</div>
      {rules.map(r => (
        <div key={r.l} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderBottom: `1px solid ${C.border}` }}>
          <div>
            <div style={{ fontSize: 12, fontWeight: 600 }}>{r.l}</div>
            <div style={{ fontSize: 10, color: C.textMuted }}>{r.desc}</div>
          </div>
          <Badge color={C.accent}>{r.v}</Badge>
        </div>
      ))}
      {status && (
        <div style={{ marginTop: 14 }}>
          <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: status.trading_allowed ? C.longDim : C.shortDim, borderRadius: 8, border: `1px solid ${status.trading_allowed ? C.long : C.short}44` }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Trading Status</span>
            <Badge color={status.trading_allowed ? C.long : C.short}>{status.trading_allowed ? "ACTIVE" : "PAUSED"}</Badge>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginTop: 8 }}>
            <div style={{ background: C.surface, borderRadius: 8, padding: "10px 12px" }}>
              <div style={{ fontSize: 10, color: C.textMuted }}>Daily PnL</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: status.daily_pnl >= 0 ? C.long : C.short }}>{status.daily_pnl >= 0 ? "+" : ""}{fmt(status.daily_pnl)}</div>
            </div>
            <div style={{ background: C.surface, borderRadius: 8, padding: "10px 12px" }}>
              <div style={{ fontSize: 10, color: C.textMuted }}>Trades Today</div>
              <div style={{ fontSize: 14, fontWeight: 700, fontFamily: "'Space Mono', monospace", color: C.text }}>{status.trades_today}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  injectGlobalCSS();

  const [tab, setTab] = useState("signals");
  const [signals, setSignals] = useState([]);
  const [market, setMarket] = useState({});
  const [sentiment, setSentiment] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [backtests, setBacktests] = useState([]);
  const [riskStatus, setRiskStatus] = useState(null);
  const [selectedSig, setSelectedSig] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [btPair, setBtPair] = useState("BTCUSDT");
  const [btStrategy, setBtStrategy] = useState("TrendMomentum");
  const [btRunning, setBtRunning] = useState(false);
  const pollRef = useRef(null);

  const fetchAll = useCallback(async () => {
    try {
      const [sigRes, mktRes, sentRes, anaRes, riskRes] = await Promise.allSettled([
        fetch(`${API}/signals/?limit=80`).then(r => r.json()),
        fetch(`${API}/market/prices`).then(r => r.json()),
        fetch(`${API}/market/sentiment`).then(r => r.json()),
        fetch(`${API}/analytics/overview`).then(r => r.json()),
        fetch(`${API}/risk/status`).then(r => r.json()),
      ]);
      if (sigRes.status  === "fulfilled") setSignals(sigRes.value.signals || []);
      if (mktRes.status  === "fulfilled") setMarket(mktRes.value.market || {});
      if (sentRes.status === "fulfilled") setSentiment(sentRes.value);
      if (anaRes.status  === "fulfilled") setAnalytics(anaRes.value);
      if (riskRes.status === "fulfilled") setRiskStatus(riskRes.value);
      setLastUpdate(new Date());
      setError(null);
    } catch (e) {
      setError("Cannot reach backend — is it running? (python -m uvicorn backend.main:app --reload)");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    pollRef.current = setInterval(fetchAll, 30000);
    return () => clearInterval(pollRef.current);
  }, [fetchAll]);

  const scan = async () => {
    setScanning(true);
    try {
      await fetch(`${API}/signals/scan`, { method: "POST" });
      await fetchAll();
    } catch (e) {
      setError("Scan failed — check backend connection");
    }
    setScanning(false);
  };

  const runBacktest = async () => {
    setBtRunning(true);
    try {
      const res = await fetch(`${API}/backtest/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pair: btPair, strategy: btStrategy, limit: 300 }),
      });
      const data = await res.json();
      setBacktests(prev => [data, ...prev.slice(0, 9)]);
    } catch (e) {
      setError("Backtest failed");
    }
    setBtRunning(false);
  };

  const pairs = ["BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","ADAUSDT","XRPUSDT","DOTUSDT","AVAXUSDT","MATICUSDT","LINKUSDT"];
  const strategies = ["TrendMomentum","MeanReversion","BreakoutMA","TrendFollow"];

  // ── Sidebar tabs ───────────────────────────────────────────────────────────
  const tabs = [
    { id: "signals",    label: "Signals",     icon: "⚡" },
    { id: "market",     label: "Market",      icon: "📊" },
    { id: "backtest",   label: "Backtest",    icon: "🔬" },
    { id: "strategies", label: "Strategies",  icon: "🤖" },
    { id: "risk",       label: "Risk",        icon: "🛡" },
  ];

  const longCount  = signals.filter(s => s.signal_type === "LONG").length;
  const shortCount = signals.filter(s => s.signal_type === "SHORT").length;
  const highConf   = signals.filter(s => s.confidence_score >= 80).length;

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden", background: C.bg }}>

      {/* ── Sidebar ──────────────────────────────────────────────────────── */}
      <div style={{ width: 220, flexShrink: 0, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", padding: "16px 12px" }}>
        {/* Logo */}
        <div style={{ marginBottom: 24, padding: "0 4px" }}>
          <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, fontWeight: 700, color: C.accent, letterSpacing: "-0.02em" }}>CryptoQuant</div>
          <div style={{ fontSize: 10, color: C.textMuted, marginTop: 2, letterSpacing: ".06em" }}>AI TRADING PLATFORM</div>
        </div>

        {/* Status */}
        <div style={{ marginBottom: 20, padding: "8px 12px", background: C.accentDim, borderRadius: 8, border: `1px solid ${C.accent}33` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: C.accent, fontWeight: 600 }}>
            <LiveDot />{loading ? "Connecting..." : error ? "Offline" : "Live"}
          </div>
          {lastUpdate && <div style={{ fontSize: 9, color: C.textMuted, marginTop: 3 }}>Updated {timeAgo(lastUpdate)}</div>}
        </div>

        {/* Nav */}
        <nav style={{ flex: 1 }}>
          {tabs.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                display: "flex", alignItems: "center", gap: 10, width: "100%",
                padding: "10px 12px", borderRadius: 8, border: "none",
                background: tab === t.id ? C.accentDim : "transparent",
                color: tab === t.id ? C.accent : C.textMuted,
                fontWeight: tab === t.id ? 600 : 400,
                fontSize: 13, cursor: "pointer", marginBottom: 2,
                borderLeft: tab === t.id ? `2px solid ${C.accent}` : "2px solid transparent",
                transition: "all .15s",
              }}
            >
              <span>{t.icon}</span>{t.label}
              {t.id === "signals" && signals.length > 0 && (
                <span style={{ marginLeft: "auto", background: C.accent, color: C.bg, borderRadius: 10, padding: "1px 6px", fontSize: 10, fontWeight: 700 }}>{signals.length}</span>
              )}
            </button>
          ))}
        </nav>

        {/* Scan button */}
        <button
          onClick={scan}
          disabled={scanning}
          style={{
            display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
            padding: "11px 16px", borderRadius: 8, border: "none",
            background: scanning ? C.border : `linear-gradient(135deg, ${C.accent}, #00b894)`,
            color: scanning ? C.textMuted : C.bg, fontWeight: 700, fontSize: 13,
            cursor: scanning ? "not-allowed" : "pointer", transition: "all .2s",
            marginBottom: 8,
          }}
        >
          {scanning ? <><Spinner size={14} /> Scanning...</> : "⚡ Scan Now"}
        </button>
        <div style={{ fontSize: 9, color: C.textMuted, textAlign: "center", padding: "0 4px", lineHeight: 1.4 }}>Auto-scans every 5 min</div>
      </div>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Top bar */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 24px", borderBottom: `1px solid ${C.border}`, background: C.surface, flexShrink: 0 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <StatBox label="Total Signals" value={signals.length} color={C.accent} />
            <StatBox label="Long" value={longCount}  color={C.long}  />
            <StatBox label="Short" value={shortCount} color={C.short} />
            <StatBox label="High Conf (80%+)" value={highConf} color={C.gold} />
            {sentiment && <StatBox label="Fear & Greed" value={sentiment.value} sub={sentiment.label} color={sentiment.value > 50 ? C.long : C.short} />}
          </div>
          {error && <div style={{ marginLeft: "auto", fontSize: 11, color: C.short, background: C.shortDim, padding: "6px 12px", borderRadius: 6, maxWidth: 340 }}>{error}</div>}
        </div>

        {/* Content area */}
        <div style={{ flex: 1, overflow: "auto", padding: 24 }}>

          {/* ── SIGNALS TAB ─────────────────────────────────────────────── */}
          {tab === "signals" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20, maxWidth: 1200 }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, color: C.text }}>
                    Live Signals <span style={{ color: C.textMuted, fontWeight: 400, fontSize: 12 }}>— {signals.length} total</span>
                  </h2>
                  <div style={{ display: "flex", gap: 8 }}>
                    <Badge color={C.long}>{longCount} LONG</Badge>
                    <Badge color={C.short}>{shortCount} SHORT</Badge>
                  </div>
                </div>
                {loading && <div style={{ display: "flex", alignItems: "center", gap: 10, color: C.textMuted, padding: 20 }}><Spinner /> Loading signals...</div>}
                {!loading && signals.length === 0 && (
                  <Card style={{ textAlign: "center", padding: 40 }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}>🔍</div>
                    <div style={{ color: C.text, fontWeight: 600, marginBottom: 8 }}>No signals yet</div>
                    <div style={{ color: C.textMuted, fontSize: 13, marginBottom: 16 }}>Click "Scan Now" to analyze all {pairs.length} pairs using 7 AI algorithms</div>
                    <button onClick={scan} disabled={scanning} style={{ padding: "10px 20px", background: C.accent, border: "none", borderRadius: 8, color: C.bg, fontWeight: 700, cursor: "pointer" }}>
                      {scanning ? "Scanning..." : "⚡ Scan Now"}
                    </button>
                  </Card>
                )}
                {signals.map((s, i) => <SignalCard key={s.id || i} sig={s} onSelect={setSelectedSig} />)}
              </div>

              {/* Right panel */}
              <div>
                <Card style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 12 }}>MARKET OVERVIEW</div>
                  {Object.keys(market).length === 0 && <div style={{ color: C.textMuted, fontSize: 12 }}>Loading prices...</div>}
                  {pairs.slice(0, 8).map(p => <TickerRow key={p} pair={p} data={market[p]} />)}
                </Card>
                {analytics && (
                  <Card>
                    <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 12 }}>ANALYTICS</div>
                    {[
                      { l: "Platform Start", v: analytics.platform?.platform_start ? timeAgo(analytics.platform.platform_start) : "—" },
                      { l: "Last Scan",      v: analytics.platform?.last_scan ? timeAgo(analytics.platform.last_scan) : "—" },
                      { l: "Pairs Scanned",  v: analytics.platform?.pairs_scanned || "—" },
                      { l: "Top Pair",       v: analytics.signals?.top_pair || "—" },
                      { l: "Avg Confidence", v: analytics.signals?.avg_confidence ? `${analytics.signals.avg_confidence}%` : "—" },
                    ].map(r => (
                      <div key={r.l} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid ${C.border}`, fontSize: 12 }}>
                        <span style={{ color: C.textMuted }}>{r.l}</span>
                        <span style={{ fontFamily: "'Space Mono', monospace", fontWeight: 700 }}>{r.v}</span>
                      </div>
                    ))}
                  </Card>
                )}
              </div>
            </div>
          )}

          {/* ── MARKET TAB ──────────────────────────────────────────────── */}
          {tab === "market" && (
            <div>
              <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, marginBottom: 20 }}>Market Data</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 12, marginBottom: 24 }}>
                {pairs.map(pair => {
                  const d = market[pair];
                  const up = d?.change_24h >= 0;
                  return (
                    <Card key={pair} style={{ padding: 16 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                        <span style={{ fontWeight: 700, fontSize: 14 }}>{pair.replace("USDT","")}<span style={{ color: C.textMuted, fontSize: 11 }}>/USDT</span></span>
                        <Badge color={up ? C.long : C.short}>{fmtPct(d?.change_24h ?? 0)}</Badge>
                      </div>
                      <div style={{ fontFamily: "'Space Mono', monospace", fontSize: 18, fontWeight: 700, marginBottom: 8 }}>${fmt(d?.price, 4)}</div>
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4, fontSize: 10, color: C.textMuted }}>
                        <div>H: <span style={{ color: C.long }}>${fmt(d?.high_24h, 4)}</span></div>
                        <div>L: <span style={{ color: C.short }}>${fmt(d?.low_24h, 4)}</span></div>
                        <div style={{ gridColumn: "span 2" }}>Vol: ${d?.volume_24h ? (d.volume_24h / 1e6).toFixed(1) + "M" : "—"}</div>
                      </div>
                    </Card>
                  );
                })}
              </div>
              {sentiment && (
                <Card style={{ maxWidth: 340 }}>
                  <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 12 }}>FEAR & GREED INDEX</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <div style={{ fontSize: 48, fontFamily: "'Space Mono', monospace", fontWeight: 700, color: sentiment.value > 50 ? C.long : C.short }}>{sentiment.value}</div>
                    <div>
                      <div style={{ fontWeight: 700, color: C.text, fontSize: 16 }}>{sentiment.label}</div>
                      <div style={{ fontSize: 11, color: C.textMuted, marginTop: 4 }}>Market sentiment indicator</div>
                    </div>
                  </div>
                  <div style={{ marginTop: 12, height: 6, background: `linear-gradient(90deg, ${C.short}, ${C.gold}, ${C.long})`, borderRadius: 3, position: "relative" }}>
                    <div style={{ position: "absolute", top: -3, left: `${sentiment.value}%`, transform: "translateX(-50%)", width: 12, height: 12, borderRadius: "50%", background: C.text, border: `2px solid ${C.bg}` }} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: C.textMuted, marginTop: 4 }}>
                    <span>Extreme Fear</span><span>Extreme Greed</span>
                  </div>
                </Card>
              )}
            </div>
          )}

          {/* ── BACKTEST TAB ─────────────────────────────────────────────── */}
          {tab === "backtest" && (
            <div style={{ maxWidth: 900 }}>
              <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, marginBottom: 20 }}>Strategy Backtesting</h2>
              <Card style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 11, color: C.textMuted, fontWeight: 600, letterSpacing: ".08em", marginBottom: 14 }}>RUN BACKTEST</div>
                <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
                  <div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 6 }}>Pair</div>
                    <select value={btPair} onChange={e => setBtPair(e.target.value)} style={{ background: C.surface, color: C.text, border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 12px", fontSize: 13, cursor: "pointer" }}>
                      {pairs.map(p => <option key={p}>{p}</option>)}
                    </select>
                  </div>
                  <div>
                    <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 6 }}>Strategy</div>
                    <select value={btStrategy} onChange={e => setBtStrategy(e.target.value)} style={{ background: C.surface, color: C.text, border: `1px solid ${C.border}`, borderRadius: 6, padding: "8px 12px", fontSize: 13, cursor: "pointer" }}>
                      {strategies.map(s => <option key={s}>{s}</option>)}
                    </select>
                  </div>
                  <button onClick={runBacktest} disabled={btRunning} style={{ padding: "9px 20px", background: btRunning ? C.border : C.accent, border: "none", borderRadius: 8, color: C.bg, fontWeight: 700, fontSize: 13, cursor: btRunning ? "not-allowed" : "pointer", display: "flex", alignItems: "center", gap: 8 }}>
                    {btRunning ? <><Spinner size={14} /> Running...</> : "▶ Run Backtest"}
                  </button>
                </div>
              </Card>
              {backtests.length === 0 && <div style={{ color: C.textMuted, textAlign: "center", padding: 40 }}>No backtest results yet. Configure and run a backtest above.</div>}
              {backtests.map((r, i) => <BacktestCard key={i} result={r} />)}
            </div>
          )}

          {/* ── STRATEGIES TAB ──────────────────────────────────────────── */}
          {tab === "strategies" && (
            <div style={{ maxWidth: 700 }}>
              <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, marginBottom: 20 }}>AI Algorithm Stack</h2>
              <Card><StrategyPanel /></Card>
            </div>
          )}

          {/* ── RISK TAB ────────────────────────────────────────────────── */}
          {tab === "risk" && (
            <div style={{ maxWidth: 600 }}>
              <h2 style={{ fontFamily: "'Space Mono', monospace", fontSize: 16, marginBottom: 20 }}>Risk Management</h2>
              <Card><RiskPanel status={riskStatus} /></Card>
            </div>
          )}

        </div>
      </div>

      {/* ── Signal Detail Modal ───────────────────────────────────────────── */}
      {selectedSig && <SignalModal sig={selectedSig} onClose={() => setSelectedSig(null)} />}
    </div>
  );
}
