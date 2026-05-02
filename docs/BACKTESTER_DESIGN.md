# 🧪 Backtester v2 — Brain Replay Engine

**Status:** Phase A live (price-only baseline).
**Roadmap slot:** NEW Priority 1 (unblocks Pillar 1 L4, Pillar 3, Pillar 4).

## Why this exists
Without a backtester, every algo tweak takes 30+ live picks (~6 weeks)
to validate. With it, we can validate in <1 hour using 2 years of data.

## Phase A — Price-Only Baseline (THIS RELEASE)
- Strict point-in-time slicing (no look-ahead)
- Simple RSI + SMA + ATR scoring (mirrors live scorer style)
- Outcome simulator with conservative assumptions
- Sharpe / Sortino / Max DD / Profit Factor
- Per-exit-status breakdown
- NOT YET: LLM, news, regime gates (Phase B)
- NOT YET: Survivorship bias correction (Phase C)

## Conservative Assumptions (all in our favor for trust)
| Assumption | Why |
|---|---|
| SL hits first when both touched same day | Pessimistic = honest |
| Entry at sim-day close | Slight slippage realism |
| Min 60 days history before any pick | Avoids cold-start noise |
| N<30 cohorts flagged "not significant" | Prevents tweaking on noise |

## Output Layout
    data/backtest_results/<run_id>/
      picks.csv         - every simulated pick + outcome
      metrics.json      - aggregate Sharpe/Sortino/MaxDD
      report.md         - human-readable summary

## Quick start
    # Default: 30 tickers, 180 days, takes ~2-5 min
    python scripts/run_backtest.py

    # Custom: specific tickers, 90 days
    python scripts/run_backtest.py --tickers AAPL,NVDA,MSFT --days 90

    # Full universe (slower, ~10-15 min)
    python scripts/run_backtest.py --limit-tickers 100 --days 365

## Phase B (next sprint)
- Add cached news data (Polygon free tier or yfinance)
- Add market regime gates from main.py
- Compute per-day stock_stats (kill last look-ahead bias source)
- Walk-forward validation (train/test splits)

## Phase C (Month 3+)
- Optional LLM scoring on sampled picks ($500 cap/run)
- Pattern recognition stats feed Pillar 4
- Survivorship-corrected universe (paid data)
