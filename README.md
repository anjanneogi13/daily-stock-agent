# 📈 Daily Stock Agent

Autonomous AI-powered US-equity stock-picking agent. Runs daily on GitHub Actions, generates picks 45 min before market open, monitors them intraday, evaluates at close, and produces a Claude-coached weekly reflection.

## 🏗️ Architecture

- **8:45 AM ET** → daily-picks.yml → picks + premarket check + Telegram
- **Every 30 min** → intraday_monitor.yml → TP/SL alerts via Telegram
- **5:00 PM ET** → evaluate.yml → mark TP/SL/expired + daily report
- **Sat 8 AM ET** → weekend_reflection.yml → Claude weekly review
- **1st of month** → monthly_xray.yml → Claude monthly deep-dive

## 🧠 Tech Stack

| Layer | Tool |
|---|---|
| Data | Finnhub (fundamentals, news, earnings), yfinance (OHLCV) |
| Indicators | ta library + custom (RSI, MACD, ATR, ADX, Bollinger, Fib, S/R) |
| Scoring | Composite: trend + momentum + volatility + volume + sector + news + fundamentals |
| LLM | Claude Sonnet 4.5 → Gemini 2.5 Flash → rule-based |
| Notifications | Telegram (personal + group) + GitHub Issues |
| CI/CD | GitHub Actions, DST-aware multi-cron + dedup guards |
| Tests | pytest |

## 🔑 Required Secrets

Set in **Settings → Secrets and variables → Actions**:

| Secret | Purpose |
|---|---|
| ANTHROPIC_API_KEY | Claude (primary LLM) |
| GEMINI_API_KEY | Gemini fallback |
| FINNHUB_API_KEY | Fundamentals, news, earnings |
| TELEGRAM_BOT_TOKEN | Bot identity |
| TELEGRAM_CHAT_ID | Personal DM chat ID |
| TELEGRAM_GROUP_CHAT_ID | Group chat ID (optional) |

## 🏃 Local Development

    pip install -r requirements.txt
    cp .env.example .env   # fill in your keys
    python main.py         # generate picks
    pytest tests/          # run tests
    streamlit run app.py   # dashboard

## 📁 Project Layout

    main.py                 # daily pick generator
    evaluate_picks.py       # end-of-day evaluator
    backtest.py             # backtest harness
    config.yaml             # universe + weights + LLM config
    src/                    # core engine
    scripts/                # workflows & helpers
    data/                   # picks_log.csv, trades.csv, learning/, caches
    .github/workflows/      # 5 cron-driven workflows
    tests/                  # pytest suite

## 💵 Monthly Cost ≈ $2-3

Mostly Claude Sonnet 4.5 (~30 ticker rationales/day + 1 sentiment briefing/day). Everything else is free tier.

## ⚠️ Disclaimer

Research software, **not financial advice**. Always confirm with your own analysis before risking real capital.

## 📜 License

MIT

---
*Built with Claude + GitHub Copilot.*

---

## 🔔 Phase 2A: News Engine (Live)

The agent continuously monitors news from Alpaca, Yahoo Finance, and curated sources.
Each headline is classified by Claude Sonnet 4.5 for trading impact (sentiment, urgency,
category, tradeable score).

**High-impact news (score ≥ 0.7) triggers:**
- Telegram alert with rationale
- Addition to 3-day watchlist
- Score boost in next morning's pick generation

**Schedule:** Every 30 min, pre-market + market hours + after-hours (4 AM – 8 PM ET).

**State files:**
- `data/watchlist.json` — current 3-day watchlist
- `data/news_log.jsonl` — every classified headline (forever log)
- `data/news_seen.json` — dedup cache (48h TTL)

**Telegram threshold:** `tradeable_score >= 0.7` (configurable in `scripts/run_news_engine.py`)
