#!/usr/bin/env python3
"""
Generates a daily Buffett AI investment report as index.html.
Run manually or via GitHub Actions on a schedule.
"""

import anthropic
import os
import sys
from datetime import datetime, timezone
from io import StringIO

REPORT_SYSTEM = """You are a Warren Buffett-style investment analyst generating a daily HTML report.

Warren Buffett's framework:
- MOAT: brand, network effects, switching costs, cost advantages, regulatory barriers
- MANAGEMENT: honest, capital-allocating, shareholder-oriented, skin in the game
- FINANCIALS: ROE > 15%, gross margins > 40%, low debt, strong FCF, consistent EPS growth
- PREDICTABILITY: can you project earnings 10 years out? avoid airlines/commodities/fast-changing tech
- VALUATION: intrinsic value = owner earnings / (discount rate - growth). Want 20-30% margin of safety

Verdict definitions:
- BUY NOW: trading at a meaningful discount to intrinsic value, high-quality business, act now
- WAIT FOR DIP: great business but fairly/richly valued — wait for a 10-20%+ pullback
- HOLD: own it, don't add, not a bargain today
- AVOID: poor moat, bad financials, or so overvalued the risk/reward is poor

Output ONLY HTML body content (no <!DOCTYPE>, no <html>, <head>, or <body> tags).
Use EXACTLY these CSS class names — no others:
  market-pulse,
  watchlist, watchlist-item, watchlist-ticker, watchlist-company, watchlist-price,
  watchlist-verdict, verdict-buy, verdict-wait, verdict-hold, verdict-avoid,
  watchlist-note,
  picks, pick-card, pick-header, pick-rank, pick-name, pick-verdict,
  pick-scores, top-pick, buffett-quote

Structure your output in this EXACT order:

<div class="market-pulse">
  <h2>Market Pulse</h2>
  <p>2-3 sentences: what's happening in markets today that Buffett would care about.</p>
</div>

<div class="watchlist">
  <h2>Buffett Verdict — Stocks Investors Are Watching</h2>
  <p class="watchlist-intro">What would Buffett do with the most-discussed stocks right now?</p>

  <!-- Include 12–16 major stocks investors commonly ask about today.
       Always cover: AAPL, MSFT, NVDA, GOOGL, META, AMZN, ORCL, TSLA, BRK.B, JPM, V, WMT
       Add any others that are in the news or heavily discussed today.
       Use real current prices and valuations from your search. -->

  <div class="watchlist-item">
    <span class="watchlist-ticker">MSFT</span>
    <span class="watchlist-company">Microsoft</span>
    <span class="watchlist-price">$XXX</span>
    <span class="watchlist-verdict verdict-wait">WAIT FOR DIP</span>
    <span class="watchlist-note">P/E 32x — excellent moat but priced for perfection. Wait for sub-$380.</span>
  </div>

  [more watchlist-item rows for each stock]
</div>

<div class="picks">
  <h2>Today's 5 Best Opportunities</h2>

  <div class="pick-card">
    <div class="pick-header">
      <span class="pick-rank">1</span>
      <span class="pick-name">Company Name (TICKER)</span>
      <span class="pick-verdict verdict-buy">BUY NOW</span>
    </div>
    <p class="pick-scores">Moat: X/10 · Management: X/10 · Financials: X/10 · Predictability: X/10 · Total: XX/40</p>
    <p><strong>Why Buffett loves it:</strong> ...</p>
    <p><strong>Key numbers:</strong> ROE X%, gross margin X%, FCF $Xbn, debt/equity X</p>
    <p><strong>Why buy now:</strong> what created the opportunity</p>
    <p><strong>Intrinsic value:</strong> $X–$Y (stock at $Z = X% discount/premium)</p>
    <p><strong>Risk:</strong> ...</p>
  </div>

  [4 more pick-card divs]
</div>

<div class="top-pick">
  <h2>🏆 Top Pick of the Day</h2>
  <p>Which of the 5 is the single best opportunity right now and exactly why.</p>
</div>

<div class="buffett-quote">
  <p>A closing paragraph in Buffett's voice summarizing his view of today's market.</p>
</div>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buffett AI — {date}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  :root {{
    --navy:   #0d1b2a;
    --navy2:  #1b2d42;
    --green:  #10b981;
    --green2: #d1fae5;
    --amber:  #f59e0b;
    --amber2: #fef3c7;
    --violet: #8b5cf6;
    --violet2:#ede9fe;
    --red:    #ef4444;
    --red2:   #fee2e2;
    --ink:    #111827;
    --muted:  #6b7280;
    --border: #e5e7eb;
    --bg:     #f4f6f9;
    --card:   #ffffff;
    --radius: 14px;
  }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--ink);
    line-height: 1.65;
    font-size: 15px;
  }}

  /* ── HEADER ── */
  header {{
    background: var(--navy);
    padding: 0 40px;
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    gap: 20px;
    border-bottom: 3px solid var(--green);
  }}
  .logo-block {{
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 22px 0;
  }}
  .logo-icon {{
    width: 40px;
    height: 40px;
    background: var(--green);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
  }}
  .logo-text {{ color: white; }}
  .logo-text strong {{
    display: block;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.35rem;
    line-height: 1;
    letter-spacing: -0.01em;
  }}
  .logo-text span {{
    font-size: 0.7rem;
    opacity: 0.5;
    text-transform: uppercase;
    letter-spacing: 0.12em;
  }}
  .header-meta {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    justify-content: center;
    gap: 3px;
    padding: 22px 0;
  }}
  .header-date {{
    color: white;
    font-size: 0.92rem;
    font-weight: 600;
  }}
  .header-tag {{
    font-size: 0.68rem;
    color: rgba(255,255,255,0.4);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }}

  /* ── MAIN ── */
  main {{
    max-width: 880px;
    margin: 40px auto;
    padding: 0 24px;
  }}

  /* ── SECTION LABELS ── */
  .section-label {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--muted);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .section-label::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* ── MARKET PULSE ── */
  .market-pulse {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 26px 30px;
    margin-bottom: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
  }}
  .market-pulse::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--navy) 0%, var(--green) 100%);
  }}
  .market-pulse h2 {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--muted);
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .market-pulse h2::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}
  .market-pulse p {{
    font-size: 0.95rem;
    color: #374151;
    line-height: 1.75;
  }}
  .market-pulse p + p {{ margin-top: 10px; }}

  /* ── WATCHLIST ── */
  .watchlist {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 26px 30px;
    margin-bottom: 32px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid var(--border);
  }}
  .watchlist h2 {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--muted);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .watchlist h2::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}
  .watchlist-intro {{
    font-size: 0.82rem;
    color: var(--muted);
    margin-bottom: 16px;
  }}
  .watchlist-item {{
    display: grid;
    grid-template-columns: 68px 1fr 70px 120px;
    align-items: center;
    gap: 10px 14px;
    padding: 11px 14px;
    border-radius: 9px;
    margin-bottom: 5px;
    background: #f9fafb;
    transition: background 0.15s;
  }}
  .watchlist-item:hover {{ background: #f0f2f5; }}
  .watchlist-ticker {{
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--navy);
    letter-spacing: 0.02em;
  }}
  .watchlist-company {{
    font-size: 0.85rem;
    color: #374151;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .watchlist-price {{
    font-size: 0.82rem;
    color: var(--muted);
    font-weight: 500;
    text-align: right;
  }}
  .watchlist-verdict {{
    padding: 3px 10px;
    border-radius: 100px;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    white-space: nowrap;
    text-align: center;
  }}
  .watchlist-note {{
    grid-column: 1 / -1;
    font-size: 0.78rem;
    color: var(--muted);
    padding: 0 2px;
    line-height: 1.4;
    margin-top: -4px;
    margin-bottom: 2px;
  }}
  @media (max-width: 640px) {{
    .watchlist-item {{
      grid-template-columns: 60px 1fr 60px;
    }}
    .watchlist-price {{ display: none; }}
    .watchlist-note {{ grid-column: 1 / -1; }}
  }}

  /* ── PICKS ── */
  .picks {{ margin-bottom: 8px; }}
  .picks h2 {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  .picks h2::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }}

  /* ── PICK CARD ── */
  .pick-card {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 24px 28px;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
    border: 1px solid var(--border);
    border-left: 5px solid var(--border);
    transition: box-shadow 0.18s, transform 0.18s;
  }}
  .pick-card:hover {{
    box-shadow: 0 8px 32px rgba(0,0,0,0.11);
    transform: translateY(-1px);
  }}
  .pick-card:has(.verdict-buy)   {{ border-left-color: var(--green); }}
  .pick-card:has(.verdict-wait)  {{ border-left-color: var(--amber); }}
  .pick-card:has(.verdict-hold)  {{ border-left-color: var(--violet); }}
  .pick-card:has(.verdict-avoid) {{ border-left-color: var(--red); }}

  .pick-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 14px;
    flex-wrap: wrap;
  }}
  .pick-rank {{
    width: 32px;
    height: 32px;
    background: var(--navy);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
    letter-spacing: -0.02em;
  }}
  .pick-name {{
    font-size: 1.18rem;
    font-weight: 700;
    flex: 1;
    min-width: 0;
    letter-spacing: -0.02em;
  }}
  .pick-verdict {{
    padding: 5px 14px;
    border-radius: 100px;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
  }}
  .verdict-buy   {{ background: var(--green2); color: #065f46; }}
  .verdict-wait  {{ background: var(--amber2); color: #78350f; }}
  .verdict-hold  {{ background: var(--violet2); color: #4c1d95; }}
  .verdict-avoid {{ background: var(--red2); color: #7f1d1d; }}

  /* ── SCORE BARS (rendered by JS) ── */
  .pick-scores {{ display: none; }}  /* hide raw text; JS renders bars */

  .score-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px 16px;
    margin-bottom: 16px;
    padding: 14px 16px;
    background: #f9fafb;
    border-radius: 10px;
  }}
  .score-item {{ min-width: 0; }}
  .score-label {{
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--muted);
    margin-bottom: 5px;
  }}
  .score-bar-track {{
    height: 5px;
    background: #e5e7eb;
    border-radius: 99px;
    overflow: hidden;
    margin-bottom: 3px;
  }}
  .score-bar-fill {{
    height: 100%;
    border-radius: 99px;
    background: var(--navy);
    transition: width 0.6s cubic-bezier(.25,.8,.25,1);
  }}
  .score-value {{
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--ink);
  }}
  .score-total-pill {{
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--navy);
    color: white;
    border-radius: 8px;
    padding: 7px 14px;
    margin-top: 2px;
  }}
  .score-total-label {{
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    opacity: 0.65;
  }}
  .score-total-value {{
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.02em;
  }}
  .score-total-bar {{
    flex: 1;
    height: 4px;
    background: rgba(255,255,255,0.2);
    border-radius: 99px;
    margin: 0 14px;
    overflow: hidden;
  }}
  .score-total-fill {{
    height: 100%;
    border-radius: 99px;
    background: var(--green);
  }}

  .pick-card p {{
    font-size: 0.88rem;
    color: #374151;
    margin-bottom: 5px;
    line-height: 1.65;
  }}
  .pick-card p strong {{
    color: var(--ink);
    font-weight: 600;
  }}
  .pick-card p:last-child {{ margin-bottom: 0; }}

  /* ── TOP PICK ── */
  .top-pick {{
    background: var(--navy);
    color: white;
    border-radius: var(--radius);
    padding: 28px 32px;
    margin: 32px 0 16px;
    position: relative;
    overflow: hidden;
  }}
  .top-pick::after {{
    content: '🏆';
    position: absolute;
    right: 28px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 3.5rem;
    opacity: 0.08;
    pointer-events: none;
  }}
  .top-pick h2 {{
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .top-pick h2 .tp-badge {{
    background: var(--green);
    color: #fff;
    font-family: 'Inter', sans-serif;
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    padding: 3px 9px;
    border-radius: 100px;
  }}
  .top-pick p {{
    font-size: 0.92rem;
    opacity: 0.85;
    line-height: 1.75;
    max-width: 680px;
  }}

  /* ── BUFFETT QUOTE ── */
  .buffett-quote {{
    background: var(--card);
    border-radius: var(--radius);
    padding: 28px 32px 28px 36px;
    margin-bottom: 40px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    border: 1px solid var(--border);
    position: relative;
  }}
  .buffett-quote::before {{
    content: '\\201C';
    position: absolute;
    left: 14px;
    top: 12px;
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 4rem;
    color: var(--green);
    line-height: 1;
    opacity: 0.35;
  }}
  .buffett-quote p {{
    font-size: 0.95rem;
    font-style: italic;
    color: #374151;
    line-height: 1.8;
  }}
  .buffett-quote p + p {{ margin-top: 10px; }}

  /* ── FOOTER ── */
  footer {{
    text-align: center;
    padding: 24px 20px;
    color: #9ca3af;
    font-size: 0.75rem;
    border-top: 1px solid var(--border);
    background: white;
  }}
  footer strong {{ color: var(--muted); font-weight: 600; }}

  /* ── MOBILE ── */
  @media (max-width: 640px) {{
    header {{ padding: 0 20px; }}
    main {{ margin: 24px auto; padding: 0 16px; }}
    .pick-card {{ padding: 18px 20px; }}
    .top-pick {{ padding: 22px 22px; }}
    .score-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .top-pick::after {{ display: none; }}
  }}
</style>
</head>
<body>

<header>
  <div class="logo-block">
    <div class="logo-icon">📈</div>
    <div class="logo-text">
      <strong>Buffett AI</strong>
      <span>Investment Intelligence</span>
    </div>
  </div>
  <div class="header-meta">
    <div class="header-date">{date}</div>
    <div class="header-tag">Daily Report · Buffett Framework</div>
  </div>
</header>

<main>
{content}
</main>

<footer>
  <strong>Buffett AI</strong> &nbsp;·&nbsp; Not financial advice &nbsp;·&nbsp; Always do your own research<br>
  <span style="margin-top:4px;display:inline-block;opacity:0.6">Last updated: {timestamp}</span>
</footer>

<script>
// Parse score text → visual bars
document.querySelectorAll('.pick-scores').forEach(el => {{
  const text = el.textContent;
  const cats = [];
  const catRe = /(Moat|Management|Financials|Predictability):\s*(\d+)\/10/gi;
  const totalRe = /Total:\s*(\d+)\/40/i;
  let m;
  while ((m = catRe.exec(text)) !== null) {{
    cats.push({{ label: m[1], val: parseInt(m[2]) }});
  }}
  const totalMatch = totalRe.exec(text);
  const total = totalMatch ? parseInt(totalMatch[1]) : null;

  if (cats.length === 0) return;

  const grid = document.createElement('div');
  grid.className = 'score-grid';

  cats.forEach(c => {{
    const pct = c.val / 10 * 100;
    const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#3b82f6' : pct >= 40 ? '#f59e0b' : '#ef4444';
    grid.innerHTML += `
      <div class="score-item">
        <div class="score-label">${{c.label}}</div>
        <div class="score-bar-track"><div class="score-bar-fill" style="width:${{pct}}%;background:${{color}}"></div></div>
        <div class="score-value">${{c.val}}<span style="color:#9ca3af;font-weight:400">/10</span></div>
      </div>`;
  }});

  if (total !== null) {{
    const pct = total / 40 * 100;
    grid.innerHTML += `
      <div class="score-total-pill">
        <span class="score-total-label">Total Score</span>
        <div class="score-total-bar"><div class="score-total-fill" style="width:${{pct}}%"></div></div>
        <span class="score-total-value">${{total}}<span style="opacity:0.5;font-size:0.75rem">/40</span></span>
      </div>`;
  }}

  el.replaceWith(grid);
}});
</script>

</body>
</html>"""


def generate_report():
    client = anthropic.Anthropic()

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%A, %B %d, %Y")
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    print(f"🔍 Generating Buffett AI report for {date_str} ...")

    content_buf = StringIO()

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=REPORT_SYSTEM,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                f"Generate the daily Buffett AI investment report for {date_str}.\n\n"
                "Search for the following and use REAL current prices and valuations:\n\n"
                "1. Today's market overview — what's moving, what Buffett would notice\n\n"
                "2. BUFFETT VERDICT on these specific stocks — search current price and P/E for each:\n"
                "   AAPL, MSFT, NVDA, GOOGL, META, AMZN, ORCL, TSLA, BRK.B, JPM, V, WMT\n"
                "   Plus any other stocks that are heavily discussed in the news today.\n"
                "   Give each a verdict: BUY NOW / WAIT FOR DIP / HOLD / AVOID\n"
                "   Include the current price and one-line reason for each verdict.\n\n"
                "3. The 5 best opportunities right now — wide-moat businesses with FCF yields\n"
                "   above 4%, P/E below 5-year average, or recent price dislocations.\n"
                "   These can overlap with the watchlist above.\n\n"
                "Output ONLY clean HTML using the exact CSS classes specified. "
                "Do NOT output any markdown, explanatory text, or code fences — pure HTML only."
            )
        }],
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                print(event.delta.text, end="", flush=True)
                content_buf.write(event.delta.text)

    print("\n")

    content = content_buf.getvalue().strip()

    # Strip any accidental markdown code fences
    if content.startswith("```html"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    html = HTML_TEMPLATE.format(
        date=date_str,
        timestamp=timestamp,
        content=content.strip(),
    )

    output_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Report saved → index.html")
    print(f"   Open in browser: open index.html")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is not set.")
        sys.exit(1)
    generate_report()
