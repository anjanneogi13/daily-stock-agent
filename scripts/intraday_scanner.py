"""Live quotes + simple opportunity scanner.

Scans a watchlist of liquid US tickers for sudden momentum + news catalysts
that weren't in the morning picks.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone, timedelta

try:
    import yfinance as yf
except ImportError:
    yf = None

from intraday_news import fetch_recent_news, classify_material

# Default watchlist — top liquid US names. Override by creating data/watchlist.txt
DEFAULT_WATCHLIST = [
    # Mega-cap tech
    "AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA","AVGO","AMD","NFLX",
    # Semis / AI
    "TSM","ASML","MU","SMCI","ARM","PLTR","CRWD","SNOW","DDOG","NET",
    # Finance
    "JPM","BAC","GS","MS","V","MA","COIN","HOOD",
    # Consumer / health
    "WMT","COST","HD","NKE","SBUX","LLY","UNH","NVO","PFE",
    # Energy / industrial
    "XOM","CVX","CAT","BA","GE","DE",
    # ETFs (sentiment)
    "SPY","QQQ","IWM","XLK","XLF","XLE",
]

def load_watchlist() -> list:
    wl_file = Path("data/watchlist.txt")
    if wl_file.exists():
        return [t.strip().upper() for t in wl_file.read_text().splitlines() if t.strip()]
    return DEFAULT_WATCHLIST

def get_live_quote(ticker: str) -> dict:
    """Returns {price, change_pct, vol_ratio} or {} on failure."""
    if yf is None:
        return {}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="5m", prepost=False)
        if hist.empty:
            return {}
        last_close = float(hist["Close"].iloc[-1])
        # previous day close
        daily = t.history(period="5d", interval="1d")
        prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else last_close
        change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
        # volume vs 20-day avg
        avg_vol = float(daily["Volume"].tail(20).mean()) if len(daily) else 0
        today_vol = float(daily["Volume"].iloc[-1]) if len(daily) else 0
        vol_ratio = (today_vol / avg_vol) if avg_vol > 0 else 0
        return {
            "price": last_close,
            "change_pct": change_pct,
            "vol_ratio": vol_ratio,
            "prev_close": prev_close,
        }
    except Exception as e:
        print(f"[quote] {ticker}: {e}")
        return {}

def score_opportunity(quote: dict, has_catalyst: bool) -> float:
    """Simple intraday score 0-100."""
    if not quote:
        return 0
    score = 50
    # Momentum
    score += min(quote.get("change_pct", 0) * 4, 25)   # +1% = +4pts, capped
    # Volume confirmation
    vr = quote.get("vol_ratio", 0)
    if vr >= 2: score += 10
    if vr >= 3: score += 10
    # Catalyst
    if has_catalyst: score += 15
    return max(0, min(100, score))

def scan_for_new_opportunities(exclude: set, sent_alerts: set, max_results: int = 3) -> list:
    """Scan watchlist for high-momentum tickers not in morning picks."""
    watchlist = [t for t in load_watchlist() if t not in exclude]
    candidates = []

    for ticker in watchlist:
        quote = get_live_quote(ticker)
        if not quote or quote.get("change_pct", 0) < 1.5:
            continue  # need >+1.5% intraday move
        if quote.get("vol_ratio", 0) < 1.5:
            continue  # need volume confirmation

        # Catalyst?
        news = fetch_recent_news(ticker, lookback_min=120)
        catalyst_headline = None
        for n in news:
            cat = classify_material(n.get("headline", ""))
            if cat in ("upgrade", "earnings", "guidance", "ma"):
                catalyst_headline = n.get("headline", "")[:120]
                break

        score = score_opportunity(quote, has_catalyst=bool(catalyst_headline))
        if score < 70:
            continue

        # Dedupe across runs
        fp = f"NEW|{ticker}|{int(score/10)}"
        if fp in sent_alerts:
            continue
        sent_alerts.add(fp)

        price = quote["price"]
        # Simple entry/SL/TP at 1.5% / 3% (R:R = 2.0)
        candidates.append({
            "ticker": ticker,
            "price": price,
            "score": score,
            "morning_score": 0,  # unknown — placeholder
            "entry": round(price, 2),
            "sl": round(price * 0.985, 2),
            "tp": round(price * 1.03, 2),
            "reason": catalyst_headline or f"+{quote['change_pct']:.1f}% on {quote['vol_ratio']:.1f}× volume",
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:max_results]