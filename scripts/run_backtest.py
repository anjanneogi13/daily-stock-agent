"""Run the Phase A backtester.

Usage:
    python scripts/run_backtest.py
    python scripts/run_backtest.py --tickers AAPL,NVDA,MSFT --days 90
"""
import argparse
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd
from src.backtester.engine import run_backtest


def get_default_tickers():
    """Read tickers from data/stock_stats/ folder (already curated)."""
    from pathlib import Path
    stats_dir = Path("data/stock_stats")
    if stats_dir.exists():
        tickers = sorted(p.stem for p in stats_dir.glob("*.json"))
        # Exclude indices/ETFs
        tickers = [t for t in tickers if t not in {"SPY", "QQQ", "IWM", "DIA"}]
        return tickers
    # fallback small set
    return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
            "AMD", "AVGO", "TSM"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", default=None,
                   help="Comma-sep tickers (default: from data/stock_stats/)")
    p.add_argument("--days", type=int, default=180,
                   help="How many days back to start (default: 180)")
    p.add_argument("--top-n", type=int, default=5,
                   help="Max picks per simulated day (default: 5)")
    p.add_argument("--max-hold", type=int, default=10,
                   help="Outcome window in trading days (default: 10)")
    p.add_argument("--limit-tickers", type=int, default=30,
                   help="Cap ticker count for speed in v1 (default: 30)")
    args = p.parse_args()

    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
    else:
        tickers = get_default_tickers()[:args.limit_tickers]

    print(f"[run_backtest] Tickers ({len(tickers)}): {tickers}")

    # Date range
    end = date.today() - timedelta(days=20)  # leave buffer for outcome sim
    start = end - timedelta(days=args.days)
    # Also need history for PIT slicing (60 day min)
    fetch_start = start - timedelta(days=120)

    print(f"[run_backtest] Fetching OHLCV {fetch_start} → {date.today()}...")

    # Fetch SPY too (used as reference for trading-day calendar)
    fetch_tickers = list(set(tickers + ["SPY"]))
    raw = yf.download(fetch_tickers, start=str(fetch_start),
                      end=str(date.today()), progress=False,
                      group_by="ticker", auto_adjust=True, threads=True)

    ohlcv = {}
    for tk in fetch_tickers:
        try:
            df = raw[tk].dropna() if len(fetch_tickers) > 1 else raw.dropna()
            if not df.empty:
                ohlcv[tk] = df
        except (KeyError, AttributeError):
            print(f"  [warn] no data for {tk}")

    print(f"[run_backtest] Loaded data for {len(ohlcv)} tickers")

    summary = run_backtest(
        tickers=tickers,
        ohlcv=ohlcv,
        start_date=str(start),
        end_date=str(end),
        top_n_per_day=args.top_n,
        max_hold_days=args.max_hold,
    )

    print("\n" + "=" * 60)
    print("BACKTEST COMPLETE")
    print("=" * 60)
    import json
    print(json.dumps(summary["overall"], indent=2))


if __name__ == "__main__":
    main()
