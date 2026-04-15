# Buffett AI

An investment agent that thinks like Warren Buffett.

## Usage

```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Interactive menu (analyze / buy-wait-sell / picks)
python3 buffett_agent.py

# Command line
python3 buffett_agent.py analyze Apple
python3 buffett_agent.py action NVDA
python3 buffett_agent.py picks

# Generate daily HTML report → index.html
python3 generate_report.py
```

## Daily Report

The report at `index.html` is regenerated automatically every weekday at 9 AM ET via GitHub Actions.

To trigger it manually: **Actions** → **Daily Buffett Report** → **Run workflow**

## Setup

1. Add your `ANTHROPIC_API_KEY` as a GitHub secret (Settings → Secrets → Actions)
2. Enable GitHub Pages (Settings → Pages → Source: main branch, / root)
3. Your report lives at `https://YOUR_USERNAME.github.io/buffett-ai/`
