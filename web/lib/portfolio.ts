export interface Holding {
  ticker: string
  name: string
  shares?: number
  value?: number  // dollar override (shares computed from live price)
}

export interface WatchItem {
  ticker: string
  name: string
}

export const WATCHLIST: WatchItem[] = [
  // Your portfolio stocks
  { ticker: "AAPL",  name: "Apple" },
  { ticker: "MSFT",  name: "Microsoft" },
  { ticker: "NVDA",  name: "NVIDIA" },
  { ticker: "GOOGL", name: "Alphabet" },
  { ticker: "META",  name: "Meta" },
  { ticker: "TSLA",  name: "Tesla" },
  { ticker: "NFLX",  name: "Netflix" },
  { ticker: "SHOP",  name: "Shopify" },
  { ticker: "AMD",   name: "AMD" },
  { ticker: "TWLO",  name: "Twilio" },
  { ticker: "ORCL",  name: "Oracle" },
  { ticker: "ADBE",  name: "Adobe" },
  { ticker: "TCEHY", name: "Tencent" },
  // Big tech & platforms
  { ticker: "AMZN",  name: "Amazon" },
  { ticker: "CRM",   name: "Salesforce" },
  { ticker: "PLTR",  name: "Palantir" },
  { ticker: "UBER",  name: "Uber" },
  { ticker: "COIN",  name: "Coinbase" },
  { ticker: "APP",   name: "AppLovin" },
  { ticker: "NOW",   name: "ServiceNow" },
  // Semiconductors
  { ticker: "AVGO",  name: "Broadcom" },
  { ticker: "QCOM",  name: "Qualcomm" },
  { ticker: "ARM",   name: "Arm Holdings" },
  { ticker: "TSM",   name: "TSMC" },
  { ticker: "MU",    name: "Micron" },
  // Finance
  { ticker: "BRK-B", name: "Berkshire Hathaway" },
  { ticker: "JPM",   name: "JPMorgan Chase" },
  { ticker: "V",     name: "Visa" },
  { ticker: "MA",    name: "Mastercard" },
  { ticker: "GS",    name: "Goldman Sachs" },
  { ticker: "BAC",   name: "Bank of America" },
  { ticker: "BLK",   name: "BlackRock" },
  { ticker: "AXP",   name: "American Express" },
  { ticker: "SPGI",  name: "S&P Global" },
  // Consumer
  { ticker: "WMT",   name: "Walmart" },
  { ticker: "COST",  name: "Costco" },
  { ticker: "KO",    name: "Coca-Cola" },
  { ticker: "MCD",   name: "McDonald's" },
  { ticker: "NKE",   name: "Nike" },
  { ticker: "HD",    name: "Home Depot" },
  { ticker: "DIS",   name: "Disney" },
  // Healthcare
  { ticker: "JNJ",   name: "Johnson & Johnson" },
  { ticker: "UNH",   name: "UnitedHealth" },
  { ticker: "LLY",   name: "Eli Lilly" },
  // Energy
  { ticker: "XOM",   name: "ExxonMobil" },
  { ticker: "CVX",   name: "Chevron" },
  // International
  { ticker: "BABA",  name: "Alibaba" },
  { ticker: "CRWD",  name: "CrowdStrike" },
  { ticker: "INTC",  name: "Intel" },
  { ticker: "PEP",   name: "PepsiCo" },
]

export const PORTFOLIO: Holding[] = [
  { ticker: "ADBE",    name: "Adobe",     value: 100_000 },
  { ticker: "AAPL",    name: "Apple",     shares: 78 },
  { ticker: "QQQ",     name: "QQQ ETF",   shares: 29.12 },
  { ticker: "QQQM",    name: "QQQM ETF",  shares: 14 },
  { ticker: "MSFT",    name: "Microsoft", shares: 35 },
  { ticker: "SHOP",    name: "Shopify",   shares: 81 },
  { ticker: "NVDA",    name: "NVIDIA",    shares: 39 },
  { ticker: "GOOGL",   name: "Alphabet",  shares: 14 },
  { ticker: "TSLA",    name: "Tesla",     shares: 8 },
  { ticker: "META",    name: "Meta",      shares: 4 },
  { ticker: "NFLX",    name: "Netflix",   shares: 45 },
  { ticker: "AMD",     name: "AMD",       shares: 14 },
  { ticker: "TWLO",    name: "Twilio",    shares: 18 },
  { ticker: "TCEHY",   name: "Tencent",   shares: 27 },
  { ticker: "VOO",     name: "VOO ETF",   shares: 1 },
  { ticker: "ORCL",    name: "Oracle",    shares: 12 },
  { ticker: "BTC-USD", name: "Bitcoin",   shares: 0.05821928 },
  { ticker: "ETH-USD", name: "Ethereum",  shares: 0.84374 },
]
