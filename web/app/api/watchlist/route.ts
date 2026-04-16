import { NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { getWatchlistVerdicts, saveWatchlistVerdicts } from '@/lib/db'
import { WATCHLIST } from '@/lib/portfolio'

export async function GET() {
  return NextResponse.json(getWatchlistVerdicts())
}

async function fetchBatch(
  client: Anthropic,
  tickers: string[]
): Promise<Record<string, { verdict: string; reason: string }>> {
  const resp = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4000,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tools: [{ type: 'web_search_20260209', name: 'web_search' } as any],
    messages: [{
      role: 'user',
      content:
        'Search current prices and valuations, then give a Warren Buffett verdict ' +
        'for each of these stocks.\n\n' +
        `Stocks: ${tickers.join(', ')}\n\n` +
        'Return ONLY a valid JSON object — absolutely no other text:\n' +
        '{"AAPL": {"verdict": "HOLD", "reason": "P/E 28x, great moat, fairly valued"}, ...}\n\n' +
        'verdict must be exactly one of: BUY MORE, HOLD, TRIM, SELL\n' +
        'reason: under 12 words, include P/E or a key valuation metric.',
    }],
  })

  const text = resp.content
    .filter(b => b.type === 'text')
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .map(b => (b as any).text as string)
    .join('')

  const s = text.indexOf('{')
  const e = text.lastIndexOf('}') + 1
  if (s === -1) return {}
  try {
    return JSON.parse(text.slice(s, e))
  } catch {
    return {}
  }
}

export async function POST() {
  const apiKey = process.env.ANTHROPIC_API_KEY
  if (!apiKey) {
    return NextResponse.json({ error: 'ANTHROPIC_API_KEY not set' }, { status: 500 })
  }

  const client = new Anthropic({ apiKey })
  const tickers = WATCHLIST.map(w => w.ticker)

  // Split into 3 batches of ~33 to handle 100 stocks reliably
  const third = Math.ceil(tickers.length / 3)
  const batches = [
    tickers.slice(0, third),
    tickers.slice(third, third * 2),
    tickers.slice(third * 2),
  ]

  const results = await Promise.all(batches.map(b => fetchBatch(client, b)))
  const combined = Object.assign({}, ...results)
  saveWatchlistVerdicts(combined)
  return NextResponse.json(combined)
}
