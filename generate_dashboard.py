#!/usr/bin/env python3
"""
Generates the GitHub Pages portfolio dashboard → index.html
Run manually or via GitHub Actions daily.
"""

import anthropic
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    os.system(f"{sys.executable} -m pip install yfinance -q")
    import yfinance as yf

# ── PORTFOLIO ──────────────────────────────────────────────────────────────
PORTFOLIO = [
    {"ticker": "ADBE",    "name": "Adobe",     "value": 100_000},
    {"ticker": "AAPL",    "name": "Apple",     "shares": 78},
    {"ticker": "QQQ",     "name": "QQQ ETF",   "shares": 29.12},
    {"ticker": "QQQM",    "name": "QQQM ETF",  "shares": 14},
    {"ticker": "MSFT",    "name": "Microsoft", "shares": 35},
    {"ticker": "SHOP",    "name": "Shopify",   "shares": 81},
    {"ticker": "NVDA",    "name": "NVIDIA",    "shares": 39},
    {"ticker": "GOOGL",   "name": "Alphabet",  "shares": 14},
    {"ticker": "TSLA",    "name": "Tesla",     "shares": 8},
    {"ticker": "META",    "name": "Meta",      "shares": 4},
    {"ticker": "NFLX",    "name": "Netflix",   "shares": 45},
    {"ticker": "AMD",     "name": "AMD",       "shares": 14},
    {"ticker": "TWLO",    "name": "Twilio",    "shares": 18},
    {"ticker": "TCEHY",   "name": "Tencent",   "shares": 27},
    {"ticker": "VOO",     "name": "VOO ETF",   "shares": 1},
    {"ticker": "ORCL",    "name": "Oracle",    "shares": 12},
    {"ticker": "BTC-USD", "name": "Bitcoin",   "shares": 0.05821928},
    {"ticker": "ETH-USD", "name": "Ethereum",  "shares": 0.84374},
]

# ── WATCHLIST (50 major stocks) ────────────────────────────────────────────
WATCHLIST = [
    {"ticker": "AAPL",  "name": "Apple"},
    {"ticker": "MSFT",  "name": "Microsoft"},
    {"ticker": "NVDA",  "name": "NVIDIA"},
    {"ticker": "GOOGL", "name": "Alphabet"},
    {"ticker": "META",  "name": "Meta"},
    {"ticker": "TSLA",  "name": "Tesla"},
    {"ticker": "NFLX",  "name": "Netflix"},
    {"ticker": "SHOP",  "name": "Shopify"},
    {"ticker": "AMD",   "name": "AMD"},
    {"ticker": "TWLO",  "name": "Twilio"},
    {"ticker": "ORCL",  "name": "Oracle"},
    {"ticker": "ADBE",  "name": "Adobe"},
    {"ticker": "TCEHY", "name": "Tencent"},
    {"ticker": "AMZN",  "name": "Amazon"},
    {"ticker": "CRM",   "name": "Salesforce"},
    {"ticker": "SNOW",  "name": "Snowflake"},
    {"ticker": "PLTR",  "name": "Palantir"},
    {"ticker": "UBER",  "name": "Uber"},
    {"ticker": "ABNB",  "name": "Airbnb"},
    {"ticker": "SPOT",  "name": "Spotify"},
    {"ticker": "COIN",  "name": "Coinbase"},
    {"ticker": "AVGO",  "name": "Broadcom"},
    {"ticker": "QCOM",  "name": "Qualcomm"},
    {"ticker": "INTC",  "name": "Intel"},
    {"ticker": "MU",    "name": "Micron"},
    {"ticker": "ARM",   "name": "Arm Holdings"},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway"},
    {"ticker": "JPM",   "name": "JPMorgan Chase"},
    {"ticker": "V",     "name": "Visa"},
    {"ticker": "MA",    "name": "Mastercard"},
    {"ticker": "BAC",   "name": "Bank of America"},
    {"ticker": "GS",    "name": "Goldman Sachs"},
    {"ticker": "MS",    "name": "Morgan Stanley"},
    {"ticker": "BLK",   "name": "BlackRock"},
    {"ticker": "SPGI",  "name": "S&P Global"},
    {"ticker": "PYPL",  "name": "PayPal"},
    {"ticker": "WMT",   "name": "Walmart"},
    {"ticker": "COST",  "name": "Costco"},
    {"ticker": "KO",    "name": "Coca-Cola"},
    {"ticker": "PEP",   "name": "PepsiCo"},
    {"ticker": "MCD",   "name": "McDonald's"},
    {"ticker": "SBUX",  "name": "Starbucks"},
    {"ticker": "NKE",   "name": "Nike"},
    {"ticker": "HD",    "name": "Home Depot"},
    {"ticker": "DIS",   "name": "Disney"},
    {"ticker": "JNJ",   "name": "Johnson & Johnson"},
    {"ticker": "UNH",   "name": "UnitedHealth"},
    {"ticker": "LLY",   "name": "Eli Lilly"},
    {"ticker": "PFE",   "name": "Pfizer"},
    {"ticker": "ABBV",  "name": "AbbVie"},
    {"ticker": "MRK",   "name": "Merck"},
    {"ticker": "XOM",   "name": "ExxonMobil"},
    {"ticker": "CVX",   "name": "Chevron"},
    {"ticker": "BABA",  "name": "Alibaba"},
    {"ticker": "PDD",   "name": "PDD Holdings"},
    {"ticker": "ASML",  "name": "ASML"},
    {"ticker": "TSM",   "name": "TSMC"},
    {"ticker": "SAP",   "name": "SAP"},
    {"ticker": "NOW",   "name": "ServiceNow"},
    {"ticker": "WDAY",  "name": "Workday"},
    {"ticker": "TEAM",  "name": "Atlassian"},
    {"ticker": "DDOG",  "name": "Datadog"},
    {"ticker": "ZS",    "name": "Zscaler"},
    {"ticker": "CRWD",  "name": "CrowdStrike"},
    {"ticker": "NET",   "name": "Cloudflare"},
    {"ticker": "MDB",   "name": "MongoDB"},
    {"ticker": "HUBS",  "name": "HubSpot"},
    {"ticker": "TTD",   "name": "The Trade Desk"},
    {"ticker": "APP",   "name": "AppLovin"},
    {"ticker": "TGT",   "name": "Target"},
    {"ticker": "LOW",   "name": "Lowe's"},
    {"ticker": "TJX",   "name": "TJX Companies"},
    {"ticker": "LULU",  "name": "Lululemon"},
    {"ticker": "AXP",   "name": "American Express"},
    {"ticker": "C",     "name": "Citigroup"},
    {"ticker": "WFC",   "name": "Wells Fargo"},
    {"ticker": "CME",   "name": "CME Group"},
    {"ticker": "ICE",   "name": "Intercontinental Exchange"},
    {"ticker": "CAT",   "name": "Caterpillar"},
    {"ticker": "DE",    "name": "Deere & Company"},
    {"ticker": "BA",    "name": "Boeing"},
    {"ticker": "RTX",   "name": "RTX (Raytheon)"},
    {"ticker": "GE",    "name": "GE Aerospace"},
    {"ticker": "LIN",   "name": "Linde"},
    {"ticker": "APH",   "name": "Amphenol"},
    {"ticker": "T",     "name": "AT&T"},
    {"ticker": "VZ",    "name": "Verizon"},
    {"ticker": "CHTR",  "name": "Charter Communications"},
    {"ticker": "ISRG",  "name": "Intuitive Surgical"},
    {"ticker": "TMO",   "name": "Thermo Fisher"},
    {"ticker": "MSTR",  "name": "MicroStrategy"},
    {"ticker": "HOOD",  "name": "Robinhood"},
    {"ticker": "SOFI",  "name": "SoFi Technologies"},
    {"ticker": "RBLX",  "name": "Roblox"},
]

PORTFOLIO_TICKERS = {p["ticker"] for p in PORTFOLIO}


# ── DATA FETCHING ──────────────────────────────────────────────────────────

def fetch_prices() -> dict:
    all_tickers = list({p["ticker"] for p in PORTFOLIO} | {w["ticker"] for w in WATCHLIST})
    print("  Fetching prices via yfinance…")
    raw = yf.download(all_tickers, period="5d", interval="1d",
                      progress=False, auto_adjust=True)
    closes = raw["Close"]
    result = {}
    for t in all_tickers:
        try:
            series = closes[t].dropna()
            result[t] = {
                "price": round(float(series.iloc[-1]), 4),
                "prev":  round(float(series.iloc[-2]), 4) if len(series) > 1 else round(float(series.iloc[-1]), 4),
            }
        except Exception:
            result[t] = {"price": 0.0, "prev": 0.0}
    return result


def fetch_verdicts_batch(client, tickers: list) -> dict:
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                "Search current prices and valuations, then give a Warren Buffett verdict "
                "for each of these stocks.\n\n"
                f"Stocks: {', '.join(tickers)}\n\n"
                "Return ONLY a valid JSON object — absolutely no other text:\n"
                '{"AAPL": {"verdict": "HOLD", "reason": "P/E 28x, great moat, fairly valued"}, ...}\n\n'
                "verdict must be exactly one of: BUY MORE, HOLD, TRIM, SELL\n"
                "reason: under 12 words, include P/E or a key valuation metric."
            ),
        }],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        return json.loads(text[s:e]) if s != -1 else {}
    except Exception:
        return {}


def fetch_portfolio_verdicts(client) -> dict:
    stock_tickers = [p["ticker"] for p in PORTFOLIO if not p["ticker"].endswith("-USD")]
    print("  Fetching portfolio verdicts…")
    return fetch_verdicts_batch(client, stock_tickers)


def fetch_watchlist_verdicts(client) -> dict:
    tickers = [w["ticker"] for w in WATCHLIST]
    mid = len(tickers) // 2
    print("  Fetching watchlist verdicts (batch 1/2)…")
    r1 = fetch_verdicts_batch(client, tickers[:mid])
    print("  Fetching watchlist verdicts (batch 2/2)…")
    r2 = fetch_verdicts_batch(client, tickers[mid:])
    return {**r1, **r2}


def fetch_market_pulse(client, date_str: str) -> str:
    print("  Fetching market pulse…")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                f"What's happening in financial markets today ({date_str}) "
                "that Warren Buffett would care about? "
                "2-3 sentences max. Plain text only, no markdown, no bullet points."
            ),
        }],
    )
    return "".join(b.text for b in resp.content if hasattr(b, "text")).strip()


# ── HTML TEMPLATE ──────────────────────────────────────────────────────────

def build_html(prices: dict, portfolio_verdicts: dict, watchlist_verdicts: dict,
               market_pulse: str, date_str: str, timestamp: str) -> str:

    # Portfolio JS data
    portfolio_js = []
    for p in PORTFOLIO:
        t   = p["ticker"]
        pd  = prices.get(t, {"price": 0.0, "prev": 0.0})
        lbl = t.replace("-USD", "")
        v   = portfolio_verdicts.get(lbl, {})
        portfolio_js.append({
            "ticker":  t,
            "label":   lbl,
            "name":    p["name"],
            "shares":  p.get("shares"),
            "value":   p.get("value"),
            "price":   pd["price"],
            "prev":    pd["prev"],
            "verdict": v.get("verdict", "—"),
            "reason":  v.get("reason", ""),
        })

    # Watchlist JS data
    watchlist_js = []
    for w in WATCHLIST:
        t  = w["ticker"]
        pd = prices.get(t, {"price": 0.0, "prev": 0.0})
        v  = watchlist_verdicts.get(t, {})
        watchlist_js.append({
            "ticker":    t,
            "name":      w["name"],
            "price":     pd["price"],
            "prev":      pd["prev"],
            "verdict":   v.get("verdict", "—"),
            "reason":    v.get("reason", ""),
            "inPortfolio": t in PORTFOLIO_TICKERS,
        })

    portfolio_json  = json.dumps(portfolio_js)
    watchlist_json  = json.dumps(watchlist_js)
    pulse_escaped   = market_pulse.replace('"', '&quot;').replace('<', '&lt;')

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buffett AI — Portfolio Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
  --navy:#0d1b2a; --green:#10b981; --green2:#d1fae5;
  --amber:#f59e0b; --amber2:#fef3c7; --violet:#8b5cf6; --violet2:#ede9fe;
  --red:#ef4444; --red2:#fee2e2; --ink:#111827; --muted:#6b7280;
  --border:#e5e7eb; --bg:#f4f6f9; --card:#fff; --r:12px;
}}
body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--ink); font-size:14px; line-height:1.5; }}

header {{
  background:var(--navy); border-bottom:3px solid var(--green);
  padding:0 32px; display:flex; align-items:center; justify-content:space-between; gap:20px;
}}
.logo-wrap {{ display:flex; align-items:center; gap:12px; padding:16px 0; }}
.logo-icon {{ width:34px; height:34px; background:var(--green); border-radius:8px;
  display:flex; align-items:center; justify-content:center; font-size:1rem; }}
.logo-text strong {{ display:block; font-family:'Playfair Display',serif; font-size:1.15rem; color:#fff; }}
.logo-text small {{ font-size:.62rem; color:rgba(255,255,255,.4); text-transform:uppercase; letter-spacing:.1em; }}
.hdr-right {{ color:rgba(255,255,255,.45); font-size:.72rem; text-align:right; padding:16px 0; }}
.hdr-right strong {{ display:block; color:#fff; font-size:.88rem; margin-bottom:2px; }}

.pulse-bar {{
  background:#fff; border-bottom:1px solid var(--border);
  padding:12px 32px; font-size:.82rem; color:#374151; line-height:1.6;
}}
.pulse-bar strong {{ color:var(--navy); font-weight:600; margin-right:6px; }}

.summary {{
  background:#fff; border-bottom:1px solid var(--border);
  padding:14px 32px; display:flex; align-items:center; gap:32px; flex-wrap:wrap;
}}
.stat {{ display:flex; flex-direction:column; gap:2px; }}
.stat-label {{ font-size:.6rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }}
.stat-val {{ font-size:1.15rem; font-weight:700; letter-spacing:-.02em; }}
.pos {{ color:#059669; }} .neg {{ color:var(--red); }}
.sep {{ width:1px; height:30px; background:var(--border); flex-shrink:0; }}
.btn {{
  background:var(--green); color:#fff; border:none; border-radius:8px;
  padding:7px 15px; font:600 .76rem 'Inter',sans-serif; cursor:pointer;
}}
.btn-ghost {{
  background:transparent; color:var(--muted); border:1px solid var(--border);
  border-radius:8px; padding:7px 13px; font:600 .76rem 'Inter',sans-serif; cursor:pointer;
}}
.live-dot {{
  width:7px; height:7px; border-radius:50%; background:var(--green);
  display:inline-block; margin-right:5px; animation:pulse 2s infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}

/* ── Tabs ── */
.tabs {{
  background:#fff; border-bottom:1px solid var(--border); padding:0 32px; display:flex;
}}
.tab {{
  background:none; border:none; cursor:pointer; padding:12px 20px;
  font:600 .82rem 'Inter',sans-serif; color:var(--muted);
  border-bottom:2px solid transparent; margin-bottom:-1px;
}}
.tab.active {{ color:var(--navy); border-bottom-color:var(--green); }}

main {{ max-width:1280px; margin:28px auto; padding:0 24px 40px; }}
.pane {{ display:none; }}
.pane.active {{ display:block; }}

.card {{ background:var(--card); border-radius:var(--r); border:1px solid var(--border);
  box-shadow:0 1px 3px rgba(0,0,0,.06),0 4px 16px rgba(0,0,0,.04); overflow:hidden; }}
.card-hdr {{
  padding:12px 20px; border-bottom:1px solid var(--border);
  display:flex; align-items:center; justify-content:space-between; gap:12px;
}}
.card-title {{ font-size:.63rem; font-weight:700; text-transform:uppercase; letter-spacing:.12em; color:var(--muted); }}
.card-meta {{ font-size:.68rem; color:var(--muted); }}

table {{ width:100%; border-collapse:collapse; }}
th {{
  text-align:left; font-size:.59rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.1em; color:var(--muted); padding:10px 16px;
  border-bottom:1px solid var(--border); white-space:nowrap;
}}
td {{ padding:11px 16px; border-bottom:1px solid #f3f4f6; vertical-align:middle; }}
tr:last-child td {{ border-bottom:none; }}
tr:hover td {{ background:#f9fafb; }}

.td-ticker {{ font-weight:700; font-size:.88rem; color:var(--navy); }}
.td-name   {{ color:var(--muted); font-size:.82rem; }}
.td-num    {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
.fw6       {{ font-weight:600; }}
.td-reason {{ color:var(--muted); font-size:.75rem; max-width:240px; }}
.pct       {{ opacity:.6; font-size:.8em; }}
.owned-tag {{
  margin-left:6px; font-size:.55rem; font-weight:700; color:var(--green);
  text-transform:uppercase; letter-spacing:.06em;
}}

.vbadge {{
  display:inline-block; padding:3px 9px; border-radius:100px;
  font-size:.61rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; white-space:nowrap;
}}
.v-buy  {{ background:var(--green2);  color:#065f46; }}
.v-hold {{ background:var(--violet2); color:#4c1d95; }}
.v-trim {{ background:var(--amber2);  color:#78350f; }}
.v-sell {{ background:var(--red2);    color:#7f1d1d; }}

.summary-pills {{ display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; align-items:center; }}
.pill {{ padding:4px 12px; border-radius:100px; font-size:.72rem; font-weight:700; }}

footer {{ text-align:center; padding:24px; color:#9ca3af; font-size:.72rem; }}

@media(max-width:768px) {{
  th:nth-child(3), td:nth-child(3),
  th:nth-child(8), td:nth-child(8) {{ display:none; }}
  .summary {{ gap:16px; padding:12px 16px; }}
  header, .pulse-bar, .summary, .tabs {{ padding-left:16px; padding-right:16px; }}
  main {{ padding:16px 12px 32px; }}
}}
</style>
</head>
<body>

<header>
  <div class="logo-wrap">
    <div class="logo-icon">📈</div>
    <div class="logo-text">
      <strong>Buffett AI</strong>
      <small>Portfolio Dashboard</small>
    </div>
  </div>
  <div class="hdr-right">
    <strong>{date_str}</strong>
    Verdicts updated {timestamp}
  </div>
</header>

<div class="pulse-bar">
  <strong>Market Pulse</strong>{pulse_escaped}
</div>

<div class="summary">
  <div class="stat">
    <span class="stat-label">Portfolio Value</span>
    <span class="stat-val" id="total-value">—</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Today's P&amp;L</span>
    <span class="stat-val" id="total-pnl">—</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Positions</span>
    <span class="stat-val">{len(PORTFOLIO)}</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Prices</span>
    <span class="stat-val" style="font-size:.82rem;color:var(--muted)">
      <span class="live-dot" id="live-dot" style="background:#9ca3af"></span>
      <span id="price-status">Loading…</span>
    </span>
  </div>
  <div style="margin-left:auto">
    <button class="btn-ghost" onclick="refreshPrices()">↻ Prices</button>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="switchTab('portfolio', this)">My Portfolio</button>
  <button class="tab" onclick="switchTab('watchlist', this)">Market Watchlist — Top {len(WATCHLIST)}</button>
</div>

<main>

  <!-- Portfolio pane -->
  <div id="pane-portfolio" class="pane active">
    <div class="card">
      <div class="card-hdr">
        <span class="card-title">Holdings</span>
        <span class="card-meta">Verdicts by Claude (Warren Buffett framework) · {timestamp}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Ticker</th><th>Name</th><th>Shares</th><th>Price</th>
            <th>Value</th><th>Today</th><th>Verdict</th><th>Why</th>
          </tr>
        </thead>
        <tbody id="tbody-portfolio"></tbody>
      </table>
    </div>
  </div>

  <!-- Watchlist pane -->
  <div id="pane-watchlist" class="pane">
    <div class="summary-pills" id="watchlist-pills"></div>
    <div class="card">
      <div class="card-hdr">
        <span class="card-title">Top 50 Stocks — Buffett Verdict</span>
        <span class="card-meta">Claude analysis · {timestamp}</span>
      </div>
      <table>
        <thead>
          <tr>
            <th>Ticker</th><th>Company</th><th>Price</th><th>Day %</th><th>Verdict</th><th>Why</th>
          </tr>
        </thead>
        <tbody id="tbody-watchlist"></tbody>
      </table>
    </div>
  </div>

</main>

<footer>Buffett AI &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Always do your own research</footer>

<script>
const PORTFOLIO  = {portfolio_json};
const WATCHLIST  = {watchlist_json};

const VERDICT_CLASS = {{
  "BUY MORE": "v-buy",
  "HOLD":     "v-hold",
  "TRIM":     "v-trim",
  "SELL":     "v-sell",
}};
const VERDICT_PILL = {{
  "BUY MORE": {{ bg:"#d1fae5", color:"#065f46" }},
  "HOLD":     {{ bg:"#ede9fe", color:"#4c1d95" }},
  "TRIM":     {{ bg:"#fef3c7", color:"#78350f" }},
  "SELL":     {{ bg:"#fee2e2", color:"#7f1d1d" }},
}};
const ORDER = {{ "BUY MORE":0, "HOLD":1, "TRIM":2, "SELL":3 }};

function fmt(n, digits=2) {{
  return n.toLocaleString('en-US', {{minimumFractionDigits:digits, maximumFractionDigits:digits}});
}}

function badge(verdict) {{
  const vc = VERDICT_CLASS[verdict] || 'v-hold';
  return `<span class="vbadge ${{vc}}">${{verdict}}</span>`;
}}

// ── Portfolio table ──────────────────────────────────────────────────────
function renderPortfolio(data) {{
  let totalValue = 0, totalGain = 0;
  const tbody = document.getElementById('tbody-portfolio');
  tbody.innerHTML = '';
  data.forEach(p => {{
    const price  = p.price || 0;
    const prev   = p.prev  || price;
    const shares = p.value && price > 0 ? p.value / price : (p.shares || 0);
    const value  = price * shares;
    const gain   = (price - prev) * shares;
    const pct    = prev ? (price - prev) / prev * 100 : 0;
    totalValue  += value;
    totalGain   += gain;
    const gs = gain >= 0 ? '+' : '';
    const gc = gain >= 0 ? 'pos' : 'neg';
    const ss = p.ticker.endsWith('-USD') ? shares.toFixed(5) : fmt(shares, 0);
    tbody.innerHTML += `<tr>
      <td class="td-ticker">${{p.label}}</td>
      <td class="td-name">${{p.name}}</td>
      <td class="td-num">${{ss}}</td>
      <td class="td-num fw6">${{price > 0 ? '$'+fmt(price) : '—'}}</td>
      <td class="td-num fw6">${{value > 0 ? '$'+fmt(value,0) : '—'}}</td>
      <td class="td-num ${{gc}}">${{price > 0 ? gs+'$'+fmt(Math.abs(gain),0)+'<span class="pct"> ('+gs+Math.abs(pct).toFixed(2)+'%)</span>' : '—'}}</td>
      <td>${{badge(p.verdict)}}</td>
      <td class="td-reason">${{p.reason}}</td>
    </tr>`;
  }});
  document.getElementById('total-value').textContent = '$' + fmt(totalValue, 0);
  const pnlEl = document.getElementById('total-pnl');
  const sign  = totalGain >= 0 ? '+' : '';
  pnlEl.textContent = sign + '$' + fmt(Math.abs(totalGain), 0);
  pnlEl.className   = 'stat-val ' + (totalGain >= 0 ? 'pos' : 'neg');
}}

// ── Watchlist table ──────────────────────────────────────────────────────
function renderWatchlist(data) {{
  const sorted = [...data].sort((a,b) => {{
    const oa = a.verdict in ORDER ? ORDER[a.verdict] : 5;
    const ob = b.verdict in ORDER ? ORDER[b.verdict] : 5;
    return oa - ob;
  }});

  const counts = {{}};
  sorted.forEach(r => {{ if (r.verdict !== '—') counts[r.verdict] = (counts[r.verdict]||0)+1; }});
  const pillsEl = document.getElementById('watchlist-pills');
  pillsEl.innerHTML = ['BUY MORE','HOLD','TRIM','SELL']
    .filter(k => counts[k])
    .map(k => {{
      const s = VERDICT_PILL[k];
      return `<span class="pill" style="background:${{s.bg}};color:${{s.color}}">${{k}} · ${{counts[k]}}</span>`;
    }}).join('');

  const tbody = document.getElementById('tbody-watchlist');
  tbody.innerHTML = '';
  sorted.forEach(w => {{
    const price = w.price || 0;
    const prev  = w.prev  || price;
    const pct   = prev ? (price - prev) / prev * 100 : 0;
    const ps    = pct >= 0 ? '+' : '';
    const pc    = pct >= 0 ? 'pos' : 'neg';
    const owned = w.inPortfolio ? '<span class="owned-tag">owned</span>' : '';
    tbody.innerHTML += `<tr>
      <td class="td-ticker">${{w.ticker}}${{owned}}</td>
      <td class="td-name">${{w.name}}</td>
      <td class="td-num fw6">${{price > 0 ? '$'+fmt(price) : '—'}}</td>
      <td class="td-num ${{pc}}">${{price > 0 ? ps+Math.abs(pct).toFixed(2)+'%' : '—'}}</td>
      <td>${{badge(w.verdict)}}</td>
      <td class="td-reason">${{w.reason}}</td>
    </tr>`;
  }});
}}

// ── Tab switching ────────────────────────────────────────────────────────
function switchTab(name, btn) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.pane').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('pane-'+name).classList.add('active');
}}

// ── Initial render ───────────────────────────────────────────────────────
renderPortfolio(PORTFOLIO);
renderWatchlist(WATCHLIST);

// ── Live price refresh ───────────────────────────────────────────────────
async function refreshPrices() {{
  document.getElementById('price-status').textContent = 'Updating…';
  document.getElementById('live-dot').style.background = '#f59e0b';

  const allTickers = [...new Set([
    ...PORTFOLIO.map(p => p.ticker),
    ...WATCHLIST.map(w => w.ticker),
  ])].join(',');
  const yhUrl    = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${{allTickers}}&lang=en-US&region=US`;
  const proxyUrl = `https://api.allorigins.win/raw?url=${{encodeURIComponent(yhUrl)}}`;

  try {{
    const res    = await fetch(proxyUrl, {{signal: AbortSignal.timeout(10000)}});
    const data   = await res.json();
    const quotes = data?.quoteResponse?.result || [];
    if (!quotes.length) throw new Error('empty');

    const priceMap = {{}};
    quotes.forEach(q => {{
      priceMap[q.symbol] = {{ price: q.regularMarketPrice, prev: q.regularMarketPreviousClose }};
    }});

    const updatedPortfolio = PORTFOLIO.map(p => ({{
      ...p, price: priceMap[p.ticker]?.price ?? p.price, prev: priceMap[p.ticker]?.prev ?? p.prev,
    }}));
    const updatedWatchlist = WATCHLIST.map(w => ({{
      ...w, price: priceMap[w.ticker]?.price ?? w.price, prev: priceMap[w.ticker]?.prev ?? w.prev,
    }}));

    renderPortfolio(updatedPortfolio);
    renderWatchlist(updatedWatchlist);

    const now = new Date().toLocaleTimeString('en-US', {{hour:'2-digit', minute:'2-digit'}});
    document.getElementById('price-status').textContent = `Live · ${{now}}`;
    document.getElementById('live-dot').style.background = '#10b981';
  }} catch(e) {{
    document.getElementById('price-status').textContent = 'Snapshot (as of report)';
    document.getElementById('live-dot').style.background = '#9ca3af';
  }}
}}

refreshPrices();
setInterval(refreshPrices, 60000);
</script>
</body>
</html>"""


# ── MAIN ───────────────────────────────────────────────────────────────────

def generate():
    client = anthropic.Anthropic()
    now        = datetime.now(timezone.utc)
    date_str   = now.strftime("%A, %B %d, %Y")
    timestamp  = now.strftime("%Y-%m-%d %H:%M UTC")

    print(f"📈 Buffett AI Dashboard — {date_str}")

    prices             = fetch_prices()
    portfolio_verdicts = fetch_portfolio_verdicts(client)
    watchlist_verdicts = fetch_watchlist_verdicts(client)
    pulse              = fetch_market_pulse(client, date_str)

    html = build_html(prices, portfolio_verdicts, watchlist_verdicts, pulse, date_str, timestamp)

    out = Path(__file__).parent / "index.html"
    out.write_text(html, encoding="utf-8")

    print(f"✅ Dashboard saved → index.html")
    print(f"   Open: open index.html")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is not set.")
        sys.exit(1)
    generate()
