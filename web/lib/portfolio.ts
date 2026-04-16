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
  // Already in your portfolio
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
  { ticker: "SNOW",  name: "Snowflake" },
  { ticker: "PLTR",  name: "Palantir" },
  { ticker: "UBER",  name: "Uber" },
  { ticker: "ABNB",  name: "Airbnb" },
  { ticker: "SPOT",  name: "Spotify" },
  { ticker: "COIN",  name: "Coinbase" },
  // Semiconductors
  { ticker: "AVGO",  name: "Broadcom" },
  { ticker: "QCOM",  name: "Qualcomm" },
  { ticker: "INTC",  name: "Intel" },
  { ticker: "MU",    name: "Micron" },
  { ticker: "ARM",   name: "Arm Holdings" },
  // Finance
  { ticker: "BRK-B", name: "Berkshire Hathaway" },
  { ticker: "JPM",   name: "JPMorgan Chase" },
  { ticker: "V",     name: "Visa" },
  { ticker: "MA",    name: "Mastercard" },
  { ticker: "BAC",   name: "Bank of America" },
  { ticker: "GS",    name: "Goldman Sachs" },
  { ticker: "MS",    name: "Morgan Stanley" },
  { ticker: "BLK",   name: "BlackRock" },
  { ticker: "SPGI",  name: "S&P Global" },
  { ticker: "PYPL",  name: "PayPal" },
  // Consumer
  { ticker: "WMT",   name: "Walmart" },
  { ticker: "COST",  name: "Costco" },
  { ticker: "KO",    name: "Coca-Cola" },
  { ticker: "PEP",   name: "PepsiCo" },
  { ticker: "MCD",   name: "McDonald's" },
  { ticker: "SBUX",  name: "Starbucks" },
  { ticker: "NKE",   name: "Nike" },
  { ticker: "HD",    name: "Home Depot" },
  { ticker: "DIS",   name: "Disney" },
  // Healthcare
  { ticker: "JNJ",   name: "Johnson & Johnson" },
  { ticker: "UNH",   name: "UnitedHealth" },
  // Healthcare (extended)
  { ticker: "LLY",   name: "Eli Lilly" },
  { ticker: "PFE",   name: "Pfizer" },
  { ticker: "ABBV",  name: "AbbVie" },
  { ticker: "MRK",   name: "Merck" },
  // Energy
  { ticker: "XOM",   name: "ExxonMobil" },
  { ticker: "CVX",   name: "Chevron" },
  // China / International
  { ticker: "BABA",  name: "Alibaba" },
  { ticker: "PDD",   name: "PDD Holdings" },
  { ticker: "ASML",  name: "ASML" },
  { ticker: "TSM",   name: "TSMC" },
  { ticker: "SAP",   name: "SAP" },
  // More tech
  { ticker: "NOW",   name: "ServiceNow" },
  { ticker: "WDAY",  name: "Workday" },
  { ticker: "TEAM",  name: "Atlassian" },
  { ticker: "DDOG",  name: "Datadog" },
  { ticker: "ZS",    name: "Zscaler" },
  { ticker: "CRWD",  name: "CrowdStrike" },
  { ticker: "NET",   name: "Cloudflare" },
  { ticker: "MDB",   name: "MongoDB" },
  { ticker: "HUBS",  name: "HubSpot" },
  { ticker: "TTD",   name: "The Trade Desk" },
  { ticker: "APP",   name: "AppLovin" },
  // More consumer & retail
  { ticker: "AMZN",  name: "Amazon" },
  { ticker: "TGT",   name: "Target" },
  { ticker: "LOW",   name: "Lowe's" },
  { ticker: "TJX",   name: "TJX Companies" },
  { ticker: "LULU",  name: "Lululemon" },
  // More finance
  { ticker: "AXP",   name: "American Express" },
  { ticker: "C",     name: "Citigroup" },
  { ticker: "WFC",   name: "Wells Fargo" },
  { ticker: "CME",   name: "CME Group" },
  { ticker: "ICE",   name: "Intercontinental Exchange" },
  // Industrials & other
  { ticker: "CAT",   name: "Caterpillar" },
  { ticker: "DE",    name: "Deere & Company" },
  { ticker: "BA",    name: "Boeing" },
  { ticker: "RTX",   name: "RTX (Raytheon)" },
  { ticker: "GE",    name: "GE Aerospace" },
  { ticker: "LIN",   name: "Linde" },
  { ticker: "APH",   name: "Amphenol" },
  // Telecom & media
  { ticker: "T",     name: "AT&T" },
  { ticker: "VZ",    name: "Verizon" },
  { ticker: "CHTR",  name: "Charter Communications" },
  // Other high-quality
  { ticker: "ISRG",  name: "Intuitive Surgical" },
  { ticker: "TMO",   name: "Thermo Fisher" },
  { ticker: "MSTR",  name: "MicroStrategy" },
  { ticker: "HOOD",  name: "Robinhood" },
  { ticker: "SOFI",  name: "SoFi Technologies" },
  { ticker: "RBLX",  name: "Roblox" },
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
