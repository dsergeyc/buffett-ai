#!/usr/bin/env python3
"""
Buffett AI — An investment agent that thinks like Warren Buffett.

Modes:
    python3 buffett_agent.py                  # interactive menu
    python3 buffett_agent.py analyze Apple    # deep analysis
    python3 buffett_agent.py action AAPL      # buy now / wait / sell
    python3 buffett_agent.py picks            # top Buffett picks right now
"""

import anthropic
import sys
import os

# ─────────────────────────────────────────────
#  SHARED BUFFETT FRAMEWORK (injected into all prompts)
# ─────────────────────────────────────────────

BUFFETT_FRAMEWORK = """
You think exactly like Warren Buffett. You apply his framework rigorously:

**Moat**: Brand, network effects, switching costs, cost advantages, regulatory barriers.
**Management**: Honest, capital-allocating, shareholder-oriented, skin in the game.
**Financials**: ROE > 15% sustained, margins stable/high, low debt, strong free cash flow, consistent EPS growth.
**Predictability**: Can you project earnings 10 years out? Prefer staples, financials, dominant platforms. Avoid airlines, commodities, fast-changing tech.
**Valuation**: Intrinsic value = Owner Earnings / (discount rate - growth). Use 10% discount rate. Want 20-30% margin of safety.
**Buffett never buys**: businesses he doesn't understand, cyclicals, heavy debt + volatile earnings, companies needing constant reinvention.
"""

# ─────────────────────────────────────────────
#  SYSTEM PROMPTS
# ─────────────────────────────────────────────

ANALYZE_PROMPT = BUFFETT_FRAMEWORK + """
When analyzing a company, always search for current data first, then output exactly this structure:

**🏢 BUSINESS OVERVIEW**
What does this company do? Is it understandable?

**🏰 ECONOMIC MOAT** — Score: X/10
Describe the moat type and durability. Would it survive a well-funded attack?

**👔 MANAGEMENT QUALITY** — Score: X/10
CEO track record, capital allocation history, insider ownership, red flags.

**📊 FINANCIAL HEALTH** — Score: X/10
ROE, gross/operating margins, debt/equity, FCF conversion, EPS growth trend. Be specific with numbers.

**🔮 BUSINESS PREDICTABILITY** — Score: X/10
Confidence in projecting earnings 10 years out.

**💰 VALUATION**
Current P/E, P/FCF, EV/EBITDA. Estimated intrinsic value range. Margin of safety (or premium).

**⚠️ KEY RISKS**
What could permanently impair this business?

**📋 OVERALL SCORE: XX/40**

**🔴🟡🟢 BUFFETT VERDICT: [STRONG BUY / BUY / WATCH / AVOID]**
Clear reasoning. Would Buffett hold this for 20 years?

**💬 BUFFETT ONE-LINER**
How Buffett would describe this at the annual meeting.
"""

ACTION_PROMPT = BUFFETT_FRAMEWORK + """
Your job is to give a specific, actionable recommendation: BUY NOW, WAIT, or SELL.

Buffett's rules on timing:
- BUY NOW: The business is excellent AND the current price offers a meaningful margin of safety (at least 20% below intrinsic value). Don't wait.
- WAIT: The business is excellent but the price is fair-to-expensive. Define what price would make it a buy.
- SELL: The moat has deteriorated, management has changed badly, fundamentals are broken, OR the stock is wildly overvalued (50%+ above intrinsic value) — Buffett rarely sells, but when the story changes, he acts.
- HOLD: Great business, fair price, no reason to sell or add aggressively.

Search for current price, recent earnings, and valuation metrics. Then output:

**📍 CURRENT SITUATION**
Stock price, recent performance, key recent news.

**🏰 MOAT STATUS**
Is the moat intact, widening, or eroding? Any recent threats?

**📊 VALUATION RIGHT NOW**
P/E, P/FCF, estimated intrinsic value, current premium or discount.

**🎯 ACTION: [BUY NOW / WAIT / HOLD / SELL]**
Be direct and specific.

**📌 IF WAIT — Buy Price Target**
"I would buy at $XXX because that gives a X% margin of safety."
Only include this section if the action is WAIT.

**📌 IF SELL — Exit Reasoning**
Why the original thesis is broken or the valuation is extreme.
Only include this section if the action is SELL.

**💬 BUFFETT ONE-LINER**
What Buffett would say about this stock today.
"""

PICKS_PROMPT = BUFFETT_FRAMEWORK + """
Your job is to find 5 stocks that Warren Buffett would seriously consider buying RIGHT NOW.

Search for:
- Quality businesses (wide moat, strong financials) that have pulled back in price recently
- Companies with P/E or P/FCF below their 5-year average
- Stocks with FCF yields above 4-5%
- Recent market dislocations that created buying opportunities in otherwise great businesses
- Sectors Buffett likes: consumer staples, financial services, insurance, dominant platforms, healthcare

For each pick, output:

**[#] COMPANY NAME (TICKER)**
- **Why Buffett would love it**: moat + management summary
- **Key numbers**: ROE, margins, debt level, FCF yield
- **Why NOW**: what created the opportunity (pullback, undervaluation, overlooked)
- **Estimated intrinsic value**: range and current margin of safety
- **Risk**: the one thing that could go wrong
- **Verdict**: BUY NOW or WAIT FOR DIP (with target price)

After all 5, add:

**🏆 TOP PICK**
Which one is the single best opportunity today and why.

**💬 BUFFETT'S TAKE**
One paragraph as if Buffett were explaining his shopping list at the annual meeting.
"""

# ─────────────────────────────────────────────
#  CORE RUNNER
# ─────────────────────────────────────────────

def run(system: str, user_message: str, client: anthropic.Anthropic):
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                print(event.delta.text, end="", flush=True)
    print("\n")


# ─────────────────────────────────────────────
#  MODES
# ─────────────────────────────────────────────

def mode_analyze(company: str, client: anthropic.Anthropic):
    print(f"\n{'═'*62}")
    print(f"  📈 DEEP ANALYSIS — {company.upper()}")
    print(f"{'═'*62}\n")
    run(
        ANALYZE_PROMPT,
        f"Analyze {company} as a Buffett-style investment. Search for current financials, "
        f"competitive position, recent news, and valuation metrics, then give the full analysis.",
        client,
    )


def mode_action(company: str, client: anthropic.Anthropic):
    print(f"\n{'═'*62}")
    print(f"  🎯 BUY / WAIT / SELL — {company.upper()}")
    print(f"{'═'*62}\n")
    run(
        ACTION_PROMPT,
        f"Should I buy {company} right now, wait for a better price, hold, or sell? "
        f"Search for the current stock price, recent earnings, and valuation, "
        f"then give me a specific action recommendation.",
        client,
    )


def mode_picks(client: anthropic.Anthropic):
    print(f"\n{'═'*62}")
    print(f"  🛒 BUFFETT'S SHOPPING LIST — Top Picks Right Now")
    print(f"{'═'*62}\n")
    run(
        PICKS_PROMPT,
        "Search for high-quality stocks that are currently undervalued or fairly valued — "
        "the kind of businesses Buffett would want to buy today. Look for recent price "
        "pullbacks in great businesses, high FCF yields, and strong moats. Give me 5 picks "
        "with specific reasoning for why NOW is a good time.",
        client,
    )


# ─────────────────────────────────────────────
#  INTERACTIVE MENU
# ─────────────────────────────────────────────

def interactive(client: anthropic.Anthropic):
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║          BUFFETT AI — Investment Analysis Agent          ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    while True:
        print("What would you like to do?\n")
        print("  1. Analyze a company (deep Buffett-style analysis)")
        print("  2. Buy now / wait / sell? (specific action for a stock)")
        print("  3. What stocks should I buy right now? (Buffett's picks)")
        print("  4. Quit\n")

        try:
            choice = input("Choice (1/2/3/4): ").strip()
        except KeyboardInterrupt:
            print("\n\nGoodbye.\n")
            break

        if choice == "1":
            company = input("Company name or ticker: ").strip()
            if company:
                mode_analyze(company, client)

        elif choice == "2":
            company = input("Company name or ticker: ").strip()
            if company:
                mode_action(company, client)

        elif choice == "3":
            mode_picks(client)

        elif choice in ("4", "q", "quit", "exit"):
            print("\nGoodbye. Remember: the stock market is a device for transferring money from the impatient to the patient.\n")
            break

        else:
            print("Please enter 1, 2, 3, or 4.\n")


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY is not set.")
        print("   Run: export ANTHROPIC_API_KEY=sk-ant-...\n")
        sys.exit(1)

    client = anthropic.Anthropic()

    args = sys.argv[1:]

    if not args:
        interactive(client)
        return

    command = args[0].lower()

    if command == "analyze" and len(args) > 1:
        mode_analyze(" ".join(args[1:]), client)
    elif command == "action" and len(args) > 1:
        mode_action(" ".join(args[1:]), client)
    elif command == "picks":
        mode_picks(client)
    else:
        # Treat any bare argument as an analyze request
        mode_analyze(" ".join(args), client)


if __name__ == "__main__":
    main()
