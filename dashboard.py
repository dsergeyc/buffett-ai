#!/usr/bin/env python3
"""
Buffett AI — Real-time portfolio dashboard.
Run:  python3 dashboard.py
Opens automatically in your browser at http://localhost:8765
Prices refresh every 60 seconds. Verdicts refresh every 4 hours.
"""

import anthropic
import json
import os
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    os.system(f"{sys.executable} -m pip install yfinance -q")
    import yfinance as yf

PORT = 8765
VERDICT_CACHE = Path(__file__).parent / ".verdict_cache.json"
VERDICT_TTL   = 4 * 3600  # regenerate verdicts every 4 hours

# ── YOUR PORTFOLIO ─────────────────────────────────────────────────────────
# shares: exact number of shares you hold
# value:  use instead of shares when you know the dollar amount but not shares
#         (dashboard will compute shares = value / live_price)
PORTFOLIO = [
    {"ticker": "ADBE",    "name": "Adobe",     "value": 100_000},   # ~$100K
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

# ── PRICE FETCHING ─────────────────────────────────────────────────────────
_price_cache: dict = {}
_price_lock = threading.Lock()


def fetch_prices():
    tickers = [p["ticker"] for p in PORTFOLIO]
    try:
        raw = yf.download(tickers, period="2d", interval="1d",
                          progress=False, auto_adjust=True)
        closes = raw["Close"]
        result = {}
        for t in tickers:
            try:
                series = closes[t].dropna()
                result[t] = {
                    "price": float(series.iloc[-1]),
                    "prev":  float(series.iloc[-2]) if len(series) > 1 else float(series.iloc[-1]),
                }
            except Exception:
                result[t] = {"price": 0.0, "prev": 0.0}
        result["_updated"] = datetime.now(timezone.utc).strftime("%H:%M UTC")
        with _price_lock:
            _price_cache.clear()
            _price_cache.update(result)
    except Exception as e:
        print(f"  ⚠ Price fetch error: {e}")


def price_loop():
    while True:
        time.sleep(60)
        fetch_prices()


# ── VERDICT FETCHING ───────────────────────────────────────────────────────

def load_cached_verdicts():
    if VERDICT_CACHE.exists():
        data = json.loads(VERDICT_CACHE.read_text())
        if time.time() - data.get("ts", 0) < VERDICT_TTL:
            return data.get("verdicts", {}), data.get("ts", 0)
    return None, 0


def fetch_verdicts(prices: dict | None = None):
    import re
    stock_tickers = [p["ticker"] for p in PORTFOLIO
                     if not p["ticker"].endswith("-USD")]
    client = anthropic.Anthropic()

    # Build price context from already-fetched yfinance data (no web search needed)
    price_lines = []
    for t in stock_tickers:
        pd = (prices or {}).get(t, {})
        pr = pd.get("price", 0)
        pv = pd.get("prev", pr)
        pct = (pr - pv) / pv * 100 if pv else 0
        sign = "+" if pct >= 0 else ""
        if pr:
            price_lines.append(f"  {t}: ${pr:.2f} ({sign}{pct:.1f}% today)")
    price_ctx = "\nCurrent prices:\n" + "\n".join(price_lines) if price_lines else ""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            system=(
                "You are a Warren Buffett investment analyst. "
                "You respond ONLY with a valid JSON object — no preamble, no explanation, "
                "no markdown fences, no trailing text. Pure JSON only."
            ),
            messages=[{
                "role": "user",
                "content": (
                    f"Give a Warren Buffett verdict (BUY MORE / HOLD / TRIM / SELL) "
                    f"for each of these stocks.{price_ctx}\n\n"
                    f"Stocks: {', '.join(stock_tickers)}\n\n"
                    "Rules:\n"
                    "- verdict is exactly one of: BUY MORE, HOLD, TRIM, SELL\n"
                    "- reason is under 12 words, must include a specific valuation metric\n"
                    "- BUY MORE = trading below intrinsic value, strong moat\n"
                    "- HOLD = good business, fairly valued, keep but don't add\n"
                    "- TRIM = richly valued or moat weakening, reduce position\n"
                    "- SELL = broken moat, dangerously overvalued, or better uses of capital\n\n"
                    'Return this exact format:\n'
                    '{"AAPL":{"verdict":"HOLD","reason":"P/E 28x, great moat, fairly valued"},'
                    '"MSFT":{"verdict":"HOLD","reason":"P/E 32x, cloud moat intact but rich"}}'
                ),
            }],
        )
        text = "".join(b.text for b in resp.content if hasattr(b, "text")).strip()

        # Extract the outermost JSON object robustly
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start == -1:
            raise ValueError("No JSON found in response")
        verdicts = json.loads(text[start:end])

    except Exception as e:
        print(f"  ⚠ Verdict fetch error: {e}")
        verdicts = {}

    # Only cache if we got real results
    if verdicts:
        VERDICT_CACHE.write_text(json.dumps({"ts": time.time(), "verdicts": verdicts}))
    return verdicts


def get_verdicts(prices: dict | None = None):
    verdicts, _ = load_cached_verdicts()
    if verdicts:
        return verdicts
    print("  Refreshing Buffett verdicts via Claude…")
    return fetch_verdicts(prices)


# ── DASHBOARD HTML ─────────────────────────────────────────────────────────

VERDICT_CLASS = {
    "BUY MORE": "v-buy",
    "HOLD":     "v-hold",
    "TRIM":     "v-trim",
    "SELL":     "v-sell",
}


def build_html(prices: dict, verdicts: dict) -> str:
    now    = datetime.now(timezone.utc)
    rows   = []
    total_value    = 0.0
    total_day_gain = 0.0

    for p in PORTFOLIO:
        t     = p["ticker"]
        pd    = prices.get(t, {"price": 0.0, "prev": 0.0})
        price = pd["price"]
        prev  = pd["prev"]

        # resolve shares
        if "value" in p and price > 0:
            shares = p["value"] / price
        else:
            shares = p.get("shares", 0)

        value    = price * shares
        day_gain = (price - prev) * shares
        day_pct  = (price - prev) / prev * 100 if prev else 0.0

        total_value    += value
        total_day_gain += day_gain

        # verdict
        label_ticker = t.replace("-USD", "")
        v      = verdicts.get(label_ticker, {})
        verdict = v.get("verdict", "—")
        reason  = v.get("reason", "")
        vc     = VERDICT_CLASS.get(verdict, "")

        sign      = "+" if day_gain >= 0 else ""
        gain_cls  = "pos" if day_gain >= 0 else "neg"
        share_str = f"{shares:,.4f}" if t.endswith("-USD") else f"{shares:g}"

        rows.append(f"""
      <tr>
        <td class="td-ticker">{label_ticker}</td>
        <td class="td-name">{p['name']}</td>
        <td class="td-num">{share_str}</td>
        <td class="td-num">${price:,.2f}</td>
        <td class="td-num bold">${value:,.0f}</td>
        <td class="td-num {gain_cls}">{sign}${day_gain:,.0f}<span class="pct"> ({sign}{day_pct:.2f}%)</span></td>
        <td>{"<span class='vbadge " + vc + "'>" + verdict + "</span>" if vc else "<span style='color:#d1d5db'>—</span>"}</td>
        <td class="td-reason">{reason}</td>
      </tr>""")

    rows_html  = "\n".join(rows)
    total_sign = "+" if total_day_gain >= 0 else ""
    total_cls  = "pos" if total_day_gain >= 0 else "neg"
    day_pct_tot = total_day_gain / (total_value - total_day_gain) * 100 if (total_value - total_day_gain) else 0

    _, vts = load_cached_verdicts()
    if vts:
        age_min = int((time.time() - vts) / 60)
        vage = f"{age_min}m ago" if age_min < 60 else f"{age_min // 60}h ago"
    else:
        vage = "loading…"

    price_updated = prices.get("_updated", "—")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buffett AI — Dashboard</title>
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

/* HEADER */
header {{
  background:var(--navy);
  border-bottom:3px solid var(--green);
  padding:0 32px;
  display:flex; align-items:center; justify-content:space-between; gap:20px;
}}
.logo-wrap {{ display:flex; align-items:center; gap:12px; padding:16px 0; }}
.logo-icon {{ width:34px; height:34px; background:var(--green); border-radius:8px;
  display:flex; align-items:center; justify-content:center; font-size:1rem; }}
.logo-text strong {{ display:block; font-family:'Playfair Display',serif; font-size:1.15rem; color:#fff; }}
.logo-text span {{ font-size:.62rem; color:rgba(255,255,255,.4); text-transform:uppercase; letter-spacing:.1em; }}
.hdr-right {{ color:rgba(255,255,255,.45); font-size:.72rem; text-align:right; padding:16px 0; }}
.hdr-right strong {{ display:block; color:#fff; font-size:.88rem; margin-bottom:2px; }}

/* SUMMARY BAR */
.summary {{
  background:#fff; border-bottom:1px solid var(--border);
  padding:14px 32px; display:flex; align-items:center; gap:36px; flex-wrap:wrap;
}}
.stat {{ display:flex; flex-direction:column; gap:2px; }}
.stat-label {{ font-size:.62rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); }}
.stat-val {{ font-size:1.2rem; font-weight:700; letter-spacing:-.02em; }}
.stat-val.pos {{ color:#059669; }}
.stat-val.neg {{ color:var(--red); }}
.sep {{ width:1px; height:32px; background:var(--border); flex-shrink:0; }}
.btn {{
  margin-left:auto; background:var(--green); color:#fff; border:none;
  border-radius:8px; padding:7px 16px; font:600 .78rem 'Inter',sans-serif;
  cursor:pointer; transition:background .15s; white-space:nowrap;
}}
.btn:hover {{ background:#059669; }}
.btn-outline {{
  background:transparent; color:var(--muted); border:1px solid var(--border);
  border-radius:8px; padding:7px 14px; font:600 .78rem 'Inter',sans-serif;
  cursor:pointer; transition:all .15s; white-space:nowrap;
}}
.btn-outline:hover {{ border-color:var(--navy); color:var(--navy); }}

/* TABLE CARD */
main {{ max-width:1280px; margin:28px auto; padding:0 24px; }}
.card {{ background:var(--card); border-radius:var(--r); border:1px solid var(--border);
  box-shadow:0 1px 3px rgba(0,0,0,.06),0 4px 16px rgba(0,0,0,.04); overflow:hidden; }}
.card-hdr {{
  padding:13px 20px; border-bottom:1px solid var(--border);
  display:flex; align-items:center; justify-content:space-between; gap:12px;
}}
.card-title {{ font-size:.65rem; font-weight:700; text-transform:uppercase; letter-spacing:.12em; color:var(--muted); }}
.card-meta {{ font-size:.68rem; color:var(--muted); }}

table {{ width:100%; border-collapse:collapse; }}
th {{
  text-align:left; font-size:.6rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.1em; color:var(--muted); padding:10px 16px;
  border-bottom:1px solid var(--border); white-space:nowrap;
}}
td {{ padding:12px 16px; border-bottom:1px solid #f3f4f6; vertical-align:middle; }}
tr:last-child td {{ border-bottom:none; }}
tr:hover td {{ background:#f9fafb; }}

.td-ticker {{ font-weight:700; font-size:.88rem; color:var(--navy); }}
.td-name   {{ color:var(--muted); font-size:.82rem; }}
.td-num    {{ font-variant-numeric:tabular-nums; white-space:nowrap; }}
.bold      {{ font-weight:600; }}
.pos       {{ color:#059669; }}
.neg       {{ color:var(--red); }}
.pct       {{ opacity:.65; font-size:.8em; }}
.td-reason {{ color:var(--muted); font-size:.76rem; max-width:200px; }}

.vbadge {{
  display:inline-block; padding:3px 9px; border-radius:100px;
  font-size:.62rem; font-weight:700; text-transform:uppercase;
  letter-spacing:.07em; white-space:nowrap;
}}
.v-buy  {{ background:var(--green2);  color:#065f46; }}
.v-hold {{ background:var(--violet2); color:#4c1d95; }}
.v-trim {{ background:var(--amber2);  color:#78350f; }}
.v-sell {{ background:var(--red2);    color:#7f1d1d; }}

footer {{
  text-align:center; padding:24px; color:#9ca3af; font-size:.72rem; margin-top:8px;
}}

@media(max-width:768px) {{
  .td-reason, th:nth-child(8), td:nth-child(8) {{ display:none; }}
  .summary {{ gap:20px; padding:12px 20px; }}
  main {{ padding:0 16px; }}
}}
</style>
</head>
<body>

<header>
  <div class="logo-wrap">
    <div class="logo-icon">📈</div>
    <div class="logo-text">
      <strong>Buffett AI</strong>
      <span>Portfolio Dashboard</span>
    </div>
  </div>
  <div class="hdr-right">
    <strong>{now.strftime('%A, %B %d, %Y')}</strong>
    Live prices · {now.strftime('%H:%M UTC')}
  </div>
</header>

<div class="summary">
  <div class="stat">
    <span class="stat-label">Total Value</span>
    <span class="stat-val">${total_value:,.0f}</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Today's P&amp;L</span>
    <span class="stat-val {total_cls}">{total_sign}${total_day_gain:,.0f}
      <span style="font-size:.8rem;font-weight:500">({total_sign}{day_pct_tot:.2f}%)</span>
    </span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Positions</span>
    <span class="stat-val">{len(PORTFOLIO)}</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Prices updated</span>
    <span class="stat-val" style="font-size:.9rem;color:var(--muted)">{price_updated}</span>
  </div>
  <div class="sep"></div>
  <div class="stat">
    <span class="stat-label">Verdicts updated</span>
    <span class="stat-val" style="font-size:.9rem;color:var(--muted)">{vage}</span>
  </div>
  <button class="btn-outline" onclick="location.href='/refresh-verdicts'">↻ Refresh Verdicts</button>
  <button class="btn" onclick="location.reload()">↻ Refresh Prices</button>
</div>

<main>
  <div class="card">
    <div class="card-hdr">
      <span class="card-title">Holdings</span>
      <span class="card-meta">Prices: Yahoo Finance · Verdicts: Claude using Warren Buffett's framework</span>
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
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
</main>

<footer>Buffett AI &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Always do your own research</footer>

<script>
  // Auto-refresh prices every 60 seconds
  setTimeout(() => location.reload(), 60000);
</script>
</body>
</html>"""


# ── HTTP SERVER ────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # suppress request logs

    def do_GET(self):
        if self.path == "/refresh-verdicts":
            if VERDICT_CACHE.exists():
                VERDICT_CACHE.unlink()
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return

        with _price_lock:
            prices = dict(_price_cache)
        verdicts = get_verdicts(prices)
        html = build_html(prices, verdicts).encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html)))
        self.end_headers()
        self.wfile.write(html)


# ── MAIN ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is not set.")
        sys.exit(1)

    print("📈 Buffett AI Dashboard starting up…")
    print("   Fetching live prices…")
    fetch_prices()

    threading.Thread(target=price_loop, daemon=True).start()

    url = f"http://localhost:{PORT}"
    print(f"   Opening {url}")
    print("   Press Ctrl+C to stop.\n")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    HTTPServer(("", PORT), Handler).serve_forever()
