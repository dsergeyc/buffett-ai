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
# shares: exact shares held
# value:  dollar amount held (shares computed from live price)
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


# ── DATA FETCHING ──────────────────────────────────────────────────────────

def fetch_prices() -> dict:
    tickers = [p["ticker"] for p in PORTFOLIO]
    print("  Fetching prices via yfinance…")
    raw = yf.download(tickers, period="5d", interval="1d",
                      progress=False, auto_adjust=True)
    closes = raw["Close"]
    result = {}
    for t in tickers:
        try:
            series = closes[t].dropna()
            result[t] = {
                "price": round(float(series.iloc[-1]), 4),
                "prev":  round(float(series.iloc[-2]), 4) if len(series) > 1 else round(float(series.iloc[-1]), 4),
            }
        except Exception:
            result[t] = {"price": 0.0, "prev": 0.0}
    return result


def fetch_verdicts(client: anthropic.Anthropic) -> dict:
    stock_tickers = [p["ticker"] for p in PORTFOLIO if not p["ticker"].endswith("-USD")]
    print("  Fetching Buffett verdicts via Claude…")
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                "Search current prices and valuations, then give a Warren Buffett verdict "
                "for each of these stocks.\n\n"
                f"Stocks: {', '.join(stock_tickers)}\n\n"
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


def fetch_market_pulse(client: anthropic.Anthropic, date_str: str) -> str:
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

def build_html(prices: dict, verdicts: dict, market_pulse: str,
               date_str: str, timestamp: str) -> str:

    # Build serialisable portfolio list for the JS runtime
    portfolio_js = []
    for p in PORTFOLIO:
        t  = p["ticker"]
        pd = prices.get(t, {"price": 0.0, "prev": 0.0})
        lbl = t.replace("-USD", "")
        v   = verdicts.get(lbl, {})
        portfolio_js.append({
            "ticker":  t,
            "label":   lbl,
            "name":    p["name"],
            "shares":  p.get("shares"),     # None when using value override
            "value":   p.get("value"),      # dollar override (e.g. ADBE $100K)
            "price":   pd["price"],
            "prev":    pd["prev"],
            "verdict": v.get("verdict", "—"),
            "reason":  v.get("reason", ""),
        })

    data_json = json.dumps(portfolio_js)
    pulse_escaped = market_pulse.replace('"', '&quot;').replace('<', '&lt;')

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
  padding:7px 15px; font:600 .76rem 'Inter',sans-serif; cursor:pointer; transition:background .15s;
}}
.btn:hover {{ background:#059669; }}
.btn-ghost {{
  background:transparent; color:var(--muted); border:1px solid var(--border);
  border-radius:8px; padding:7px 13px; font:600 .76rem 'Inter',sans-serif; cursor:pointer; transition:all .15s;
}}
.btn-ghost:hover {{ border-color:var(--navy); color:var(--navy); }}
.live-dot {{
  width:7px; height:7px; border-radius:50%; background:var(--green);
  display:inline-block; margin-right:5px; animation:pulse 2s infinite;
}}
@keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}

main {{ max-width:1280px; margin:28px auto; padding:0 24px 40px; }}
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
.td-reason {{ color:var(--muted); font-size:.75rem; max-width:200px; }}
.pct       {{ opacity:.6; font-size:.8em; }}

.vbadge {{
  display:inline-block; padding:3px 9px; border-radius:100px;
  font-size:.61rem; font-weight:700; text-transform:uppercase; letter-spacing:.07em; white-space:nowrap;
}}
.v-buy  {{ background:var(--green2);  color:#065f46; }}
.v-hold {{ background:var(--violet2); color:#4c1d95; }}
.v-trim {{ background:var(--amber2);  color:#78350f; }}
.v-sell {{ background:var(--red2);    color:#7f1d1d; }}

footer {{ text-align:center; padding:24px; color:#9ca3af; font-size:.72rem; }}

@media(max-width:768px) {{
  th:nth-child(3), td:nth-child(3),
  th:nth-child(8), td:nth-child(8) {{ display:none; }}
  .summary {{ gap:16px; padding:12px 16px; }}
  header, .pulse-bar, .summary {{ padding-left:16px; padding-right:16px; }}
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
  <div style="margin-left:auto;display:flex;gap:8px">
    <button class="btn-ghost" onclick="refreshPrices()">↻ Prices</button>
  </div>
</div>

<main>
  <div class="card">
    <div class="card-hdr">
      <span class="card-title">Holdings</span>
      <span class="card-meta" id="verdict-meta">Verdicts by Claude (Warren Buffett framework) · {timestamp}</span>
    </div>
    <table>
      <thead>
        <tr>
          <th>Ticker</th>
          <th>Name</th>
          <th>Shares</th>
          <th>Price</th>
          <th>Value</th>
          <th>Today</th>
          <th>Verdict</th>
          <th>Why</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</main>

<footer>Buffett AI &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Always do your own research</footer>

<script>
const PORTFOLIO = {data_json};

const VERDICT_CLASS = {{
  "BUY MORE": "v-buy",
  "HOLD":     "v-hold",
  "TRIM":     "v-trim",
  "SELL":     "v-sell",
}};

function fmt(n, digits=2) {{
  return n.toLocaleString('en-US', {{minimumFractionDigits: digits, maximumFractionDigits: digits}});
}}

function renderTable(data) {{
  let totalValue = 0, totalGain = 0;
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';

  data.forEach(p => {{
    const price  = p.price || 0;
    const prev   = p.prev  || price;
    const shares = p.value && price > 0 ? p.value / price : (p.shares || 0);
    const value  = price * shares;
    const gain   = (price - prev) * shares;
    const pct    = prev ? (price - prev) / prev * 100 : 0;
    totalValue += value;
    totalGain  += gain;

    const gainSign = gain >= 0 ? '+' : '';
    const gainCls  = gain >= 0 ? 'pos' : 'neg';
    const shareStr = p.ticker.endsWith('-USD') ? shares.toFixed(5) : fmt(shares, 0);
    const vc = VERDICT_CLASS[p.verdict] || 'v-hold';

    tbody.innerHTML += `
      <tr>
        <td class="td-ticker">${{p.label}}</td>
        <td class="td-name">${{p.name}}</td>
        <td class="td-num">${{shareStr}}</td>
        <td class="td-num fw6">$${{fmt(price)}}</td>
        <td class="td-num fw6">$${{fmt(value, 0)}}</td>
        <td class="td-num ${{gainCls}}">${{gainSign}}$${{fmt(Math.abs(gain), 0)}}<span class="pct"> (${{gainSign}}${{Math.abs(pct).toFixed(2)}}%)</span></td>
        <td><span class="vbadge ${{vc}}">${{p.verdict}}</span></td>
        <td class="td-reason">${{p.reason}}</td>
      </tr>`;
  }});

  document.getElementById('total-value').textContent = '$' + fmt(totalValue, 0);
  const pnlEl = document.getElementById('total-pnl');
  const sign  = totalGain >= 0 ? '+' : '';
  pnlEl.textContent = sign + '$' + fmt(Math.abs(totalGain), 0);
  pnlEl.className   = 'stat-val ' + (totalGain >= 0 ? 'pos' : 'neg');
}}

// Render immediately with baked-in prices
renderTable(PORTFOLIO);

// ── Live price refresh via Yahoo Finance ────────────────────────────────
async function refreshPrices() {{
  document.getElementById('price-status').textContent = 'Updating…';
  document.getElementById('live-dot').style.background = '#f59e0b';

  const tickers = PORTFOLIO.map(p => p.ticker).join(',');
  const yhUrl   = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${{tickers}}&lang=en-US&region=US`;
  const proxyUrl = `https://api.allorigins.win/raw?url=${{encodeURIComponent(yhUrl)}}`;

  try {{
    const res  = await fetch(proxyUrl, {{signal: AbortSignal.timeout(10000)}});
    const data = await res.json();
    const quotes = data?.quoteResponse?.result || [];

    if (quotes.length === 0) throw new Error('empty');

    const priceMap = {{}};
    quotes.forEach(q => {{
      priceMap[q.symbol] = {{
        price: q.regularMarketPrice,
        prev:  q.regularMarketPreviousClose,
      }};
    }});

    const updated = PORTFOLIO.map(p => ({{
      ...p,
      price: priceMap[p.ticker]?.price ?? p.price,
      prev:  priceMap[p.ticker]?.prev  ?? p.prev,
    }}));

    renderTable(updated);
    const now = new Date().toLocaleTimeString('en-US', {{hour:'2-digit', minute:'2-digit'}});
    document.getElementById('price-status').textContent = `Live · ${{now}}`;
    document.getElementById('live-dot').style.background = '#10b981';
  }} catch (e) {{
    document.getElementById('price-status').textContent = 'Snapshot (as of report)';
    document.getElementById('live-dot').style.background = '#9ca3af';
  }}
}}

// Initial live fetch + auto-refresh every 60s
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

    prices      = fetch_prices()
    verdicts    = fetch_verdicts(client)
    pulse       = fetch_market_pulse(client, date_str)

    html = build_html(prices, verdicts, pulse, date_str, timestamp)

    out = Path(__file__).parent / "index.html"
    out.write_text(html, encoding="utf-8")

    print(f"✅ Dashboard saved → index.html")
    print(f"   Open: open index.html")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is not set.")
        sys.exit(1)
    generate()
