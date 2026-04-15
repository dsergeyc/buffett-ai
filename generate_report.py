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

Output ONLY HTML body content (no <!DOCTYPE>, no <html>, <head>, or <body> tags).
Use EXACTLY these CSS class names — no others:
  market-pulse, picks, pick-card, pick-header, pick-rank, pick-name, pick-verdict,
  verdict-buy, verdict-wait, verdict-hold, verdict-avoid,
  pick-scores, top-pick, buffett-quote

Structure your output like this:

<div class="market-pulse">
  <h2>Market Pulse</h2>
  <p>What's happening in markets today from a Buffett perspective. What he'd be paying attention to.</p>
</div>

<div class="picks">
  <h2>Today's Top 5 Picks</h2>

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
  <p>Which of the 5 is the single best opportunity and why.</p>
</div>

<div class="buffett-quote">
  <p>A closing paragraph in Buffett's voice summarizing his view of today's market and opportunities.</p>
</div>
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buffett AI — {date}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #f0f2f5;
    color: #1a1a2e;
    line-height: 1.6;
  }}

  header {{
    background: #1a1a2e;
    color: white;
    padding: 20px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }}
  .logo {{ font-size: 1.4rem; font-weight: 700; letter-spacing: -0.02em; }}
  .logo span {{ color: #4ade80; }}
  .header-right {{ text-align: right; }}
  .report-date {{ font-size: 1rem; font-weight: 500; }}
  .tagline {{ font-size: 0.78rem; opacity: 0.55; margin-top: 2px; }}

  main {{
    max-width: 860px;
    margin: 36px auto;
    padding: 0 20px;
  }}

  /* ── Market Pulse ── */
  .market-pulse {{
    background: white;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 28px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
  }}
  .market-pulse h2 {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #888;
    margin-bottom: 10px;
  }}
  .market-pulse p {{
    font-size: 0.95rem;
    color: #374151;
  }}

  /* ── Picks Section ── */
  .picks h2 {{
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #888;
    margin-bottom: 14px;
  }}

  /* ── Pick Card ── */
  .pick-card {{
    background: white;
    border-radius: 12px;
    padding: 22px 26px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-left: 4px solid #e5e7eb;
    transition: box-shadow 0.2s;
  }}
  .pick-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.10); }}

  /* Color the left border based on verdict inside */
  .pick-card:has(.verdict-buy)   {{ border-left-color: #22c55e; }}
  .pick-card:has(.verdict-wait)  {{ border-left-color: #f59e0b; }}
  .pick-card:has(.verdict-hold)  {{ border-left-color: #818cf8; }}
  .pick-card:has(.verdict-avoid) {{ border-left-color: #f87171; }}

  .pick-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }}
  .pick-rank {{
    width: 28px;
    height: 28px;
    background: #1a1a2e;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.82rem;
    font-weight: 700;
    flex-shrink: 0;
  }}
  .pick-name {{
    font-size: 1.15rem;
    font-weight: 700;
    flex: 1;
    min-width: 0;
  }}
  .pick-verdict {{
    padding: 3px 11px;
    border-radius: 20px;
    font-size: 0.74rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    white-space: nowrap;
  }}
  .verdict-buy   {{ background: #dcfce7; color: #15803d; }}
  .verdict-wait  {{ background: #fef3c7; color: #92400e; }}
  .verdict-hold  {{ background: #ede9fe; color: #5b21b6; }}
  .verdict-avoid {{ background: #fee2e2; color: #991b1b; }}

  .pick-scores {{
    font-size: 0.82rem;
    color: #6b7280;
    margin-bottom: 12px;
  }}
  .pick-card p {{
    font-size: 0.9rem;
    color: #374151;
    margin-bottom: 6px;
  }}
  .pick-card p strong {{ color: #1a1a2e; }}

  /* ── Top Pick ── */
  .top-pick {{
    background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 100%);
    color: white;
    border-radius: 12px;
    padding: 24px 28px;
    margin: 28px 0 14px;
  }}
  .top-pick h2 {{
    font-size: 1rem;
    font-weight: 700;
    margin-bottom: 10px;
  }}
  .top-pick p {{
    font-size: 0.92rem;
    opacity: 0.88;
    line-height: 1.7;
  }}

  /* ── Buffett Quote ── */
  .buffett-quote {{
    background: white;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 36px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border-top: 3px solid #1a1a2e;
  }}
  .buffett-quote p {{
    font-style: italic;
    font-size: 0.95rem;
    color: #374151;
    line-height: 1.75;
  }}

  /* ── Footer ── */
  footer {{
    text-align: center;
    padding: 20px;
    color: #9ca3af;
    font-size: 0.78rem;
    border-top: 1px solid #e5e7eb;
  }}
  footer a {{ color: #6b7280; }}

  @media (max-width: 600px) {{
    header {{ padding: 18px 20px; }}
    .header-right {{ text-align: left; }}
    main {{ margin: 20px auto; }}
    .pick-card {{ padding: 18px; }}
  }}
</style>
</head>
<body>

<header>
  <div class="logo">📈 Buffett <span>AI</span></div>
  <div class="header-right">
    <div class="report-date">{date}</div>
    <div class="tagline">Daily Investment Report · Warren Buffett's Framework</div>
  </div>
</header>

<main>
{content}
</main>

<footer>
  <p>Generated by Buffett AI · Not financial advice · Always do your own research</p>
  <p style="margin-top:4px">Last updated: {timestamp}</p>
</footer>

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
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=REPORT_SYSTEM,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": (
                f"Generate the daily Buffett AI investment report for {date_str}.\n\n"
                "Search for:\n"
                "1. What's happening in markets today that Buffett would care about\n"
                "2. 5 high-quality stocks that are currently undervalued or have pulled back\n"
                "   — look for wide-moat businesses with FCF yields above 4%, P/E below 5-year average,\n"
                "     or recent price dislocations in otherwise great businesses\n\n"
                "Output as HTML using the exact CSS classes specified."
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
