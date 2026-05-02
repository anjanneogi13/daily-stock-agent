"""
Build stock_stats for top N stocks in the universe.
Run weekly to refresh the per-stock statistical foundation.

Usage:
    python scripts/build_stock_stats.py             # default top 20
    python scripts/build_stock_stats.py NVDA        # single ticker
    python scripts/build_stock_stats.py --all       # entire universe
"""
import sys
import time
from pathlib import Path

# Make src/ importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_stats import compute_stock_stats, save_stats

# Top 20 most-traded US stocks (covers most of our pick universe)
TOP_TICKERS = [
    "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN",
    "META", "TSLA", "AVGO", "TSM", "AMD",
    "MU", "QCOM", "INTC", "ORCL", "CRM",
    "PLTR", "RMBS", "MRVL", "NFLX", "JPM",
]

# Top 100 most-liquid US stocks (S&P + high-volume names)
# Used for weekly stats refresh — gives brain coverage on ~95% of picks
TOP_100_TICKERS = [
    # Mega-cap tech
    "NVDA", "MSFT", "AAPL", "GOOGL", "GOOG", "AMZN", "META", "TSLA",
    # Semis
    "AVGO", "TSM", "AMD", "MU", "QCOM", "INTC", "ORCL", "CRM",
    "ASML", "AMAT", "LRCX", "KLAC", "MRVL", "ADI", "TXN", "MCHP",
    "NXPI", "ON", "RMBS", "ARM", "SMCI",
    # Software/cloud
    "PLTR", "NFLX", "ADBE", "NOW", "CRWD", "PANW", "SNOW", "DDOG",
    "MDB", "NET", "TEAM", "WDAY", "INTU",
    # Financials
    "JPM", "BAC", "GS", "MS", "WFC", "C", "BLK", "SCHW", "AXP", "V",
    "MA", "PYPL", "COIN", "SOFI",
    # Consumer
    "WMT", "COST", "HD", "LOW", "TGT", "MCD", "SBUX", "NKE", "DIS",
    "CMCSA", "T", "VZ", "TMUS",
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB",
    # Healthcare/biotech
    "UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "DHR", "AMGN",
    "GILD", "BMY", "REGN", "VRTX",
    # Industrials/aerospace
    "BA", "GE", "CAT", "DE", "LMT", "RTX",
    # ETFs (benchmarks for relative analysis)
    "SPY", "QQQ", "IWM", "DIA",
    # EV/auto
    "F", "GM", "RIVN", "LCID",
    # Misc high-volume
    "BABA", "PDD", "NIO", "JD", "UBER",
]



def main():
    args = sys.argv[1:]
    if args and not args[0].startswith("--"):
        tickers = [t.upper() for t in args]
    elif "--top100" in args or "--all" in args:
        # PILLAR 1 expansion (May 2 2026): use top 100 for full coverage
        tickers = TOP_100_TICKERS
    else:
        tickers = TOP_TICKERS
    
    print(f"Building stock_stats for {len(tickers)} tickers...")
    print("=" * 60)
    
    success = 0
    failed = []
    for i, ticker in enumerate(tickers, 1):
        print(f"[{i:>2}/{len(tickers)}] {ticker:<6} ", end="", flush=True)
        profile = compute_stock_stats(ticker)
        if profile is None:
            print("❌ FETCH FAILED")
            failed.append(ticker)
            continue
        save_stats(profile)
        r1d = profile.get("returns", {}).get("1d", {})
        atr14 = profile.get("atr", {}).get("14d", {})
        print(
            f"✓  ${profile['current_price']:>8.2f}  "
            f"daily σ={r1d.get('std_pct', 0):.2f}%  "
            f"ATR14={atr14.get('atr_pct', 0):.2f}%"
        )
        success += 1
        # Be polite to yfinance
        time.sleep(0.5)
    
    print("=" * 60)
    print(f"✓ {success}/{len(tickers)} tickers processed")
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")


if __name__ == "__main__":
    main()